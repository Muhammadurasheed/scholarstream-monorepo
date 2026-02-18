"""
Firestore Data Cleanup Script
Purges broken URLs and expired opportunities from the scholarships collection.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import httpx

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Initialize Firebase before imports
import firebase_admin
from firebase_admin import credentials, firestore

def init_firebase():
    """Initialize Firebase if not already done"""
    try:
        firebase_admin.get_app()
    except ValueError:
        from app.config import settings
        cred = credentials.Certificate(settings.firebase_credentials)
        firebase_admin.initialize_app(cred)
    return firestore.client()


async def validate_url(url: str, timeout: float = 10.0) -> bool:
    """Check if URL is accessible (not 404)"""
    if not url:
        return False
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            response = await client.head(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
            })
            return response.status_code < 400
    except Exception:
        return False


def fix_devpost_url(url: str) -> str:
    """Convert DevPost subdomain URLs to canonical path format"""
    if not url:
        return url
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.rstrip('/')
        
        if 'devpost.com' in domain:
            # Handle subdomains (e.g., project.devpost.com → devpost.com/hackathons/project)
            if domain != 'devpost.com' and domain.endswith('.devpost.com'):
                project_name = domain.replace('.devpost.com', '')
                if project_name and project_name not in ['www', 'api', 'help', 'blog', 'info']:
                    return f"https://devpost.com/hackathons/{project_name}/"
            
            # Handle path-based URLs
            if path.startswith('/hackathons/'):
                project = path.replace('/hackathons/', '').split('/')[0]
                if project and project not in ['hackathons', 'challenges', 'discover', '']:
                    return f"https://devpost.com/hackathons/{project}/"
            
            return f"https://devpost.com{path}/" if path else "https://devpost.com/"
        
        return url
    except Exception:
        return url


async def purge_and_fix_scholarships(dry_run: bool = True, validate_urls: bool = False):
    """
    Main cleanup function.
    
    Args:
        dry_run: If True, only report what would be done without making changes
        validate_urls: If True, make HTTP HEAD requests to check URLs (slow but thorough)
    """
    print(f"\n{'='*60}")
    print(f"ScholarStream Database Cleanup")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"URL Validation: {'Enabled' if validate_urls else 'Disabled'}")
    print(f"{'='*60}\n")
    
    db = init_firebase()
    
    # Stats
    stats = {
        'total': 0,
        'expired': 0,
        'urls_fixed': 0,
        'deleted': 0,
        'broken_urls': 0,
        'kept': 0
    }
    
    # Actions to take
    actions = []
    
    # Fetch all scholarships
    print("Fetching all scholarships...")
    docs = db.collection('scholarships').stream()
    
    now = datetime.now()
    
    for doc in docs:
        stats['total'] += 1
        data = doc.to_dict()
        doc_id = doc.id
        
        title = data.get('name') or data.get('title') or 'Unknown'
        source_url = data.get('source_url') or data.get('url') or ''
        deadline = data.get('deadline')
        
        # Check 1: Expired deadline
        is_expired = False
        if deadline:
            try:
                deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                if deadline_dt.date() < now.date():
                    is_expired = True
                    stats['expired'] += 1
                    actions.append({
                        'action': 'DELETE',
                        'reason': f'Expired ({deadline})',
                        'doc_id': doc_id,
                        'title': title[:50]
                    })
                    continue
            except Exception:
                pass
        
        # Check 2: DevPost URL needs fixing
        if 'devpost.com' in source_url:
            fixed_url = fix_devpost_url(source_url)
            if fixed_url != source_url:
                stats['urls_fixed'] += 1
                actions.append({
                    'action': 'FIX_URL',
                    'reason': 'Subdomain → Canonical',
                    'doc_id': doc_id,
                    'title': title[:50],
                    'old_url': source_url,
                    'new_url': fixed_url
                })
                # Don't continue - we might also validate
        
        # Check 3: Optional URL validation
        if validate_urls and source_url:
            is_valid = await validate_url(source_url)
            if not is_valid:
                stats['broken_urls'] += 1
                actions.append({
                    'action': 'DELETE',
                    'reason': 'URL returns 404',
                    'doc_id': doc_id,
                    'title': title[:50],
                    'url': source_url
                })
                continue
        
        stats['kept'] += 1
    
    # Print summary
    print(f"\n{'='*60}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"Total scholarships scanned: {stats['total']}")
    print(f"Expired (to delete): {stats['expired']}")
    print(f"URLs to fix: {stats['urls_fixed']}")
    if validate_urls:
        print(f"Broken URLs (to delete): {stats['broken_urls']}")
    print(f"Will keep: {stats['kept']}")
    
    # Print actions
    print(f"\n{'='*60}")
    print("PLANNED ACTIONS")
    print(f"{'='*60}")
    
    for action in actions[:50]:  # Show first 50
        # Safe print for Windows console (strip non-ASCII chars)
        safe_title = action['title'].encode('ascii', 'ignore').decode('ascii')
        if action['action'] == 'DELETE':
            print(f"  [X] DELETE: {safe_title} - {action['reason']}")
        elif action['action'] == 'FIX_URL':
            print(f"  [FIX] URL: {safe_title}")
            safe_old = action['old_url'][:60].encode('ascii', 'ignore').decode('ascii')
            safe_new = action['new_url'].encode('ascii', 'ignore').decode('ascii')
            print(f"      Old: {safe_old}...")
            print(f"      New: {safe_new}")
    
    if len(actions) > 50:
        print(f"  ... and {len(actions) - 50} more actions")
    
    # Execute if not dry run
    if not dry_run and actions:
        print(f"\n{'='*60}")
        print("EXECUTING CHANGES...")
        print(f"{'='*60}")
        
        batch = db.batch()
        batch_count = 0
        
        for action in actions:
            doc_ref = db.collection('scholarships').document(action['doc_id'])
            
            if action['action'] == 'DELETE':
                batch.delete(doc_ref)
                stats['deleted'] += 1
            elif action['action'] == 'FIX_URL':
                batch.update(doc_ref, {'source_url': action['new_url']})
            
            batch_count += 1
            
            # Commit every 400 (Firestore limit is 500)
            if batch_count >= 400:
                batch.commit()
                print(f"  Committed batch of {batch_count} changes")
                batch = db.batch()
                batch_count = 0
        
        # Commit remaining
        if batch_count > 0:
            batch.commit()
            print(f"  Committed final batch of {batch_count} changes")
        
        print(f"\n[OK] Done! Deleted {stats['deleted']} docs, fixed {stats['urls_fixed']} URLs")
    
    elif dry_run:
        print(f"\n⚠️  DRY RUN - No changes made. Run with --execute to apply changes.")
    
    return stats


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Cleanup ScholarStream database')
    parser.add_argument('--execute', action='store_true', help='Actually make changes (default is dry run)')
    parser.add_argument('--validate-urls', action='store_true', help='Validate URLs with HTTP requests (slow)')
    args = parser.parse_args()
    
    asyncio.run(purge_and_fix_scholarships(
        dry_run=not args.execute,
        validate_urls=args.validate_urls
    ))
