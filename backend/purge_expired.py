"""
Firestore Cleanup Script: Purge Expired Opportunities
Run this to remove expired entries from the scholarships collection.
Also removes entries with generic/broken URLs like 'https://devpost.com/hackathons/'
"""
import os
import sys
sys.path.insert(0, '.')
os.environ.setdefault('ENVIRONMENT', 'development')

from app.config import settings
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

def main():
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.firebase_credentials)
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    now = datetime.now()
    
    # Phase 1: Identify all expired or junk entries
    print("=== Scanning Firestore for expired/junk opportunities ===")
    docs = db.collection('scholarships').stream()
    
    to_delete = []
    total = 0
    
    for doc in docs:
        total += 1
        data = doc.to_dict()
        name = data.get('name', data.get('title', ''))
        source_url = data.get('source_url', '')
        deadline = data.get('deadline', '')
        
        delete_reason = None
        
        # Check 1: Expired by deadline string
        if deadline:
            try:
                dl_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                if dl_dt.date() < now.date():
                    delete_reason = f"expired ({deadline})"
            except:
                pass
        
        # Check 2: Generic/broken DevPost URLs (no specific hackathon)
        if not delete_reason and source_url:
            generic_patterns = [
                'https://devpost.com/hackathons/',
                'https://devpost.com/hackathons',
                'https://unstop.com/hackathons/',
                'https://unstop.com/hackathons',
                'https://unstop.com/competitions/',
                'https://unstop.com/competitions',
            ]
            if source_url.rstrip('/') + '/' in [p.rstrip('/') + '/' for p in generic_patterns]:
                delete_reason = f"generic URL ({source_url})"
        
        if delete_reason:
            to_delete.append({
                'id': doc.id,
                'name': name[:60],
                'reason': delete_reason,
                'ref': doc.reference
            })
    
    print(f"\nTotal scholarships: {total}")
    print(f"To delete: {len(to_delete)}")
    print(f"Will retain: {total - len(to_delete)}")
    
    if not to_delete:
        print("\nNo entries to delete. Database is clean!")
        return
    
    # Show sample of what we're deleting
    print(f"\n=== Sample of entries to delete (first 10) ===")
    for item in to_delete[:10]:
        print(f"  [{item['reason']}] {item['name']} (id: {item['id']})")
    
    # Phase 2: Confirm and delete
    confirm = input(f"\nDelete {len(to_delete)} entries? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Aborted.")
        return
    
    # Batch delete (Firestore supports up to 500 per batch)
    print(f"\n=== Deleting {len(to_delete)} entries in batches ===")
    batch_size = 450
    deleted = 0
    
    for i in range(0, len(to_delete), batch_size):
        batch = db.batch()
        chunk = to_delete[i:i + batch_size]
        
        for item in chunk:
            batch.delete(item['ref'])
        
        batch.commit()
        deleted += len(chunk)
        print(f"  Deleted batch: {deleted}/{len(to_delete)}")
    
    print(f"\n=== COMPLETE ===")
    print(f"Deleted: {deleted}")
    print(f"Remaining: {total - deleted}")


if __name__ == "__main__":
    main()
