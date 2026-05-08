"""
Scholarship API Routes
All endpoints for scholarship discovery, matching, and management
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
import time
import structlog

from app.models import (
    DiscoverRequest,
    DiscoveryJobResponse,
    MatchedScholarshipsResponse,
    Scholarship,
    SaveScholarshipRequest,
    StartApplicationRequest,
    ErrorResponse
)
from app.services.matching_service import matching_service
from app.services.discovery_pulse import discovery_pulse
from app.database import db

logger = structlog.get_logger()
router = APIRouter(prefix="/api/scholarships", tags=["scholarships"])


@router.get("/discovery-pulse")
async def get_discovery_pulse():
    """
    Get real-time feedback on background discovery missions.
    Ultra-Transparency for the Flagship experience.
    """
    try:
        missions = discovery_pulse.get_active_missions()
        return {
            "status": "active" if any(m.get("status") == "active" for m in missions) else "idle",
            "missions": missions,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error("Failed to fetch discovery pulse", error=str(e))
        return {"status": "idle", "missions": [], "error": str(e)}


@router.post("/discover", response_model=DiscoveryJobResponse)
async def discover_scholarships(
    request: DiscoverRequest,
    background_tasks: BackgroundTasks
):
    """
    Initial scholarship discovery after onboarding
    Returns immediate cached results and starts background discovery
    """
    try:
        logger.info("Discovery request received", user_id=request.user_id)
        
        # Start discovery job (returns immediately)
        response = await matching_service.start_discovery_job(
            request.user_id,
            request.profile
        )
        
        # If processing, schedule background task
        if response.status == "processing" and response.job_id:
            background_tasks.add_task(
                matching_service.run_background_discovery,
                response.job_id,
                request.user_id,
                request.profile
            )
        
        return response
    except Exception as e:
        logger.error("Discovery failed", error=str(e), user_id=request.user_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-mass-hunt")
async def trigger_mass_hunt(
    background_tasks: BackgroundTasks,
    platforms: List[str] = None
):
    """
    Manually trigger a high-intensity hunt for specific platforms.
    Populates the dashboard with 'tons' of opportunities.
    """
    try:
        from app.services.cortex.navigator import sentinel
        logger.info("Manual Heavy Hunt triggered", platforms=platforms)
        background_tasks.add_task(sentinel.heavy_hunt, platforms)
        return {"status": "dispatched", "message": "Heavy Hunt mission deployed to drones."}
    except Exception as e:
        logger.error("Failed to trigger heavy hunt", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discover/{job_id}", response_model=DiscoveryJobResponse)
async def get_discovery_progress(job_id: str):
    """
    Poll for discovery job progress
    Returns current status and any new scholarships found
    """
    try:
        result = await matching_service.get_job_status(job_id)
        
        if not result:
            # Graceful Fallback: If job is missing (e.g. server restart), tell frontend it's done
            # This prevents infinite 404 loops in the UI
            logger.warning("Discovery job not found, sending graceful completion", job_id=job_id)
            return DiscoveryJobResponse(
                status="completed",
                progress=100,
                job_id=job_id,
                total_found=0
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get discovery status", error=str(e), job_id=job_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get discovery status: {str(e)}"
        )


@router.get("/matched", response_model=MatchedScholarshipsResponse)
async def get_matched_scholarships(user_id: str):
    """
    Get all scholarships matched to a user
    Returns full list with match scores
    """
    try:
        logger.info("Fetching matched scholarships", user_id=user_id)
        
        # 1. Fetch current matches
        scholarships = await db.get_user_matched_scholarships(user_id)
        
        # 2. Get last match check timestamp
        user_profile_data = await db.get_user_profile(user_id)
        last_match_time = 0
        if user_profile_data:
            last_match_time = user_profile_data.get('last_match_at', 0)
        
        now = time.time()
        # Proactive Refresh: If matches are old (>30m) or empty, trigger fresh check
        STALENESS_THRESHOLD = 1800 # 30 minutes
        
        should_refresh = False
        if not scholarships:
            should_refresh = True
        elif (now - last_match_time) > STALENESS_THRESHOLD:
            should_refresh = True
        
        if should_refresh:
            logger.info("Proactive match refresh (Staleness/Empty Trigger)", user_id=user_id)
            all_opps = await db.get_all_scholarships()
            if not all_opps:
                logger.warning("Empty database - no opportunities to match", user_id=user_id)
            if all_opps:
                if user_profile_data and 'profile' in user_profile_data:
                    from app.models import UserProfile
                    profile = UserProfile(**user_profile_data['profile'])
                    
                    # Compute fresh matches
                    matched = matching_service._filter_and_rank(all_opps, profile)
                    logger.info("Match diagnostics", total_pool=len(all_opps), matched_count=len(matched), user_id=user_id)
                    
                    if matched:
                        # Save matches for next time
                        await db.save_user_matches(user_id, [s.id for s in matched])
                        scholarships = matched
                        # Update last_match_at in profile record
                        await db.update_user_last_match_time(user_id, now)
                        logger.info("Auto-refresh match complete", confirmed_matches=len(scholarships))

        # ALWAYS Re-Score matches to ensure personalization is fresh
        if scholarships:
            try:
                user_profile_data = await db.get_user_profile(user_id)
                if user_profile_data and 'profile' in user_profile_data:
                    from app.models import UserProfile
                    profile = UserProfile(**user_profile_data['profile'])
                    
                    # Re-calculate scores for up-to-the-minute accuracy
                    for scholarship in scholarships:
                        score = matching_service.calculate_match_score(scholarship, profile)
                        scholarship.match_score = score
                        scholarship.match_tier = matching_service.get_match_tier(score)
                    
                    # Re-sort by score descending
                    scholarships.sort(key=lambda x: x.match_score, reverse=True)
            except Exception as e:
                logger.warning("Failed to re-calculate scores on read", error=str(e))

        total_value = sum(s.amount for s in scholarships)
        
        return MatchedScholarshipsResponse(
            scholarships=scholarships,
            total_value=total_value,
            last_updated=(scholarships[0].last_verified or "") if scholarships else ""
        )
        
    except Exception as e:
        logger.error("Failed to fetch matched scholarships", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch scholarships: {str(e)}"
        )


@router.get("/{scholarship_id}", response_model=Scholarship)
async def get_scholarship_by_id(scholarship_id: str):
    """
    Get detailed information about a specific scholarship
    Used for the opportunity detail page
    """
    try:
        scholarship = await db.get_scholarship(scholarship_id)
        
        if not scholarship:
            raise HTTPException(
                status_code=404,
                detail="Scholarship not found"
            )
        
        return scholarship
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch scholarship", error=str(e), scholarship_id=scholarship_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch scholarship: {str(e)}"
        )


@router.post("/save")
async def save_scholarship(request: SaveScholarshipRequest):
    """
    Add scholarship to user's saved/favorites list
    """
    try:
        await db.save_user_scholarship(request.user_id, request.scholarship_id)
        return {"success": True, "message": "Scholarship saved to favorites"}
        
    except Exception as e:
        logger.error("Failed to save scholarship", error=str(e), user_id=request.user_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save scholarship: {str(e)}"
        )


@router.post("/unsave")
async def unsave_scholarship(request: SaveScholarshipRequest):
    """
    Remove scholarship from user's saved/favorites list
    """
    try:
        await db.unsave_user_scholarship(request.user_id, request.scholarship_id)
        return {"success": True, "message": "Scholarship removed from favorites"}
        
    except Exception as e:
        logger.error("Failed to unsave scholarship", error=str(e), user_id=request.user_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to unsave scholarship: {str(e)}"
        )


        return {"success": True, "message": "Scholarship removed from favorites"}
        
    except Exception as e:
        logger.error("Failed to unsave scholarship", error=str(e), user_id=request.user_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to unsave scholarship: {str(e)}"
        )
