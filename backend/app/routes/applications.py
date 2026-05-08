"""
Application Management API Routes
Comprehensive endpoints for scholarship application lifecycle
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Optional
import structlog
import cloudinary
import cloudinary.uploader
from datetime import datetime

from app.models import (
    StartApplicationRequest, 
    SaveDraftRequest, 
    SubmitApplicationRequest,
    SaveEssayRequest,
    ApplicationDraft,
    ApplicationSubmission
)
from app.database import db
from app.config import settings

logger = structlog.get_logger()
router = APIRouter(prefix="/api/applications", tags=["applications"])

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret
)


@router.post("/start")
async def start_application(request: StartApplicationRequest):
    """
    Initialize a new application draft
    Returns application_id for subsequent operations
    """
    try:
        logger.info("Starting application", user_id=request.user_id, scholarship_id=request.scholarship_id)
        
        application_id = await db.start_application(request.user_id, request.scholarship_id)
        
        return {
            "success": True,
            "application_id": application_id,
            "message": "Application draft created"
        }
        
    except Exception as e:
        logger.error("Failed to start application", error=str(e), user_id=request.user_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start application: {str(e)}"
        )


@router.post("/draft/save")
async def save_draft(request: SaveDraftRequest):
    """
    Auto-save application draft
    Called periodically as user fills out application
    """
    try:
        logger.info("Saving draft", user_id=request.user_id, scholarship_id=request.scholarship_id, step=request.current_step)
        
        # Get or create application
        draft = await db.get_application_draft(request.user_id, request.scholarship_id)
        
        if not draft:
            # Create new draft if doesn't exist
            application_id = await db.start_application(request.user_id, request.scholarship_id)
        else:
            application_id = draft['application_id']
        
        # Prepare draft data
        draft_data = {
            'current_step': request.current_step,
            'progress_percentage': request.progress_percentage
        }
        
        if request.personal_info:
            draft_data['personal_info'] = request.personal_info.model_dump()
        if request.documents:
            draft_data['documents'] = [doc.model_dump() for doc in request.documents]
        if request.essays:
            draft_data['essays'] = [essay.model_dump() for essay in request.essays]
        if request.recommenders:
            draft_data['recommenders'] = [rec.model_dump() for rec in request.recommenders]
        if request.additional_answers:
            draft_data['additional_answers'] = request.additional_answers
        
        # Save to database
        await db.save_application_draft(application_id, draft_data)
        
        return {
            "success": True,
            "application_id": application_id,
            "message": "Draft saved successfully",
            "last_saved": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to save draft", error=str(e), user_id=request.user_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save draft: {str(e)}"
        )


@router.get("/draft/{user_id}/{scholarship_id}")
async def get_draft(user_id: str, scholarship_id: str):
    """
    Retrieve saved application draft
    Used to resume application from where user left off
    """
    try:
        logger.info("Fetching draft", user_id=user_id, scholarship_id=scholarship_id)
        
        draft = await db.get_application_draft(user_id, scholarship_id)
        
        if not draft:
            return {
                "exists": False,
                "draft": None
            }
        
        return {
            "exists": True,
            "draft": draft
        }
        
    except Exception as e:
        logger.error("Failed to fetch draft", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch draft: {str(e)}"
        )


@router.post("/submit")
async def submit_application(request: SubmitApplicationRequest):
    """
    Submit final application
    Validates completeness, generates confirmation number
    """
    try:
        logger.info("Submitting application", user_id=request.user_id, scholarship_id=request.scholarship_id)
        
        # Get draft to update
        draft = await db.get_application_draft(request.user_id, request.scholarship_id)
        
        if not draft:
            raise HTTPException(status_code=404, detail="No draft found for this application")
        
        # Prepare submission data
        submission_data = {
            'application_id': draft['application_id'],
            'user_id': request.user_id,
            'scholarship_id': request.scholarship_id,
            'scholarship_name': request.scholarship_name,
            'scholarship_amount': request.scholarship_amount,
            'personal_info': request.personal_info.model_dump(),
            'documents': [doc.model_dump() for doc in request.documents],
            'essays': [essay.model_dump() for essay in request.essays],
            'recommenders': [rec.model_dump() for rec in request.recommenders],
            'additional_answers': request.additional_answers
        }
        
        # Submit to database
        confirmation_number = await db.submit_application(submission_data)
        
        logger.info("Application submitted successfully", 
                   user_id=request.user_id, 
                   confirmation=confirmation_number)
        
        return {
            "success": True,
            "confirmation_number": confirmation_number,
            "application_id": draft['application_id'],
            "submitted_at": datetime.now().isoformat(),
            "message": "Application submitted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to submit application", error=str(e), user_id=request.user_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit application: {str(e)}"
        )


@router.post("/document/upload")
async def upload_document(file: UploadFile = File(...), user_id: str = None, scholarship_id: str = None, document_type: str = None):
    """
    Upload document to Cloudinary
    Returns document URL and metadata
    """
    try:
        if not user_id or not scholarship_id or not document_type:
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        logger.info("Uploading document", 
                   user_id=user_id, 
                   scholarship_id=scholarship_id, 
                   document_type=document_type,
                   filename=file.filename)
        
        # Read file content
        content = await file.read()
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            content,
            folder=f"scholarstream/applications/{user_id}/{scholarship_id}",
            resource_type="auto",
            public_id=f"{document_type}_{datetime.now().timestamp()}",
            tags=[user_id, scholarship_id, document_type]
        )
        
        document_data = {
            "document_type": document_type,
            "file_name": file.filename,
            "file_url": upload_result['secure_url'],
            "cloudinary_public_id": upload_result['public_id'],
            "uploaded_at": datetime.now().isoformat(),
            "file_size": len(content)
        }
        
        logger.info("Document uploaded successfully", 
                   public_id=upload_result['public_id'],
                   url=upload_result['secure_url'])
        
        return {
            "success": True,
            "document": document_data,
            "message": "Document uploaded successfully"
        }
        
    except Exception as e:
        logger.error("Failed to upload document", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.post("/essay/save")
async def save_essay(request: SaveEssayRequest):
    """
    Save essay draft
    Auto-saves essay content as user writes
    """
    try:
        logger.info("Saving essay", user_id=request.user_id, scholarship_id=request.scholarship_id, word_count=request.word_count)
        
        # Get draft
        draft = await db.get_application_draft(request.user_id, request.scholarship_id)
        
        if not draft:
            application_id = await db.start_application(request.user_id, request.scholarship_id)
        else:
            application_id = draft['application_id']
        
        # Prepare essay data
        essay_data = {
            'prompt': request.prompt,
            'content': request.content,
            'word_count': request.word_count,
            'last_edited': datetime.now().isoformat()
        }
        
        # Update or add essay to existing essays
        essays = draft.get('essays', []) if draft else []
        
        # Find if essay for this prompt exists
        essay_exists = False
        for i, existing_essay in enumerate(essays):
            if existing_essay.get('prompt') == request.prompt:
                essays[i] = essay_data
                essay_exists = True
                break
        
        if not essay_exists:
            essays.append(essay_data)
        
        # Save draft
        await db.save_application_draft(application_id, {'essays': essays})
        
        return {
            "success": True,
            "application_id": application_id,
            "word_count": request.word_count,
            "message": "Essay saved successfully"
        }
        
    except Exception as e:
        logger.error("Failed to save essay", error=str(e), user_id=request.user_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save essay: {str(e)}"
        )


@router.get("/user/{user_id}")
async def get_user_applications(user_id: str, status: Optional[str] = None):
    """
    Get all applications for a user
    Optionally filter by status (draft, submitted, awarded, etc.)
    """
    try:
        logger.info("Fetching user applications", user_id=user_id, status_filter=status)
        
        applications = await db.get_user_applications(user_id)
        
        # Filter by status if provided
        if status:
            applications = [app for app in applications if app.get('status') == status]
        
        # Calculate statistics
        stats = {
            'total': len(applications),
            'draft': sum(1 for app in applications if app.get('status') == 'draft'),
            'submitted': sum(1 for app in applications if app.get('status') == 'submitted'),
            'awarded': sum(1 for app in applications if app.get('status') == 'awarded'),
            'total_value': sum(app.get('scholarship_amount', 0) for app in applications if app.get('status') in ['submitted', 'awarded']),
            'total_won': sum(app.get('award_amount', 0) for app in applications if app.get('status') == 'awarded')
        }
        
        return {
            "applications": applications,
            "stats": stats
        }
        
    except Exception as e:
        logger.error("Failed to fetch applications", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch applications: {str(e)}"
        )


@router.get("/{application_id}")
async def get_application_by_id(application_id: str):
    """
    Get detailed information about a specific application
    Includes all submitted data and status
    """
    try:
        logger.info("Fetching application", application_id=application_id)
        
        application = await db.get_application_by_id(application_id)
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        return {
            "application": application
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch application", error=str(e), application_id=application_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch application: {str(e)}"
        )


@router.delete("/{application_id}")
async def delete_application(application_id: str):
    """
    Delete an application draft
    Only drafts can be deleted, not submitted applications
    """
    try:
        logger.info("Deleting application", application_id=application_id)
        
        application = await db.get_application_by_id(application_id)
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        if application.get('status') != 'draft':
            raise HTTPException(status_code=400, detail="Can only delete draft applications")
        
        # Delete from Firebase
        db.db.collection('applications').document(application_id).delete()
        
        logger.info("Application deleted", application_id=application_id)
        
        return {
            "success": True,
            "message": "Application draft deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete application", error=str(e), application_id=application_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete application: {str(e)}"
        )
