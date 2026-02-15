"""
Chat API endpoints
Real-time AI assistant for ScholarStream
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import structlog

from app.services.chat_service import chat_service
from app.database import db

logger = structlog.get_logger()
router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    user_id: str
    message: str
    context: Dict[str, Any] = {}


class ChatResponse(BaseModel):
    message: str
    opportunities: List[Dict[str, Any]] = []
    actions: List[Dict[str, Any]] = []


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """
    Chat with ScholarStream AI Assistant
    
    Handles natural language queries like:
    - "Find urgent hackathons for me"
    - "I need money for school fees by tomorrow"
    - "Show me scholarships for computer science majors"
    """
    try:
        logger.info("Chat request received", user_id=request.user_id, message_preview=request.message[:50])
        
        # Get user profile for context
        user_profile = await db.get_user_profile(request.user_id)
        if user_profile:
            request.context['user_profile'] = user_profile
        
        # Get matched opportunities count
        matched = await db.get_user_matched_scholarships(request.user_id)
        request.context['matched_count'] = len(matched) if matched else 0
        
        # Process chat
        response = await chat_service.chat(
            user_id=request.user_id,
            message=request.message,
            context=request.context
        )
        
        logger.info("Chat response generated", opportunities_found=len(response.get('opportunities', [])))
        
        return ChatResponse(
            message=response['message'],
            opportunities=response.get('opportunities', []),
            actions=response.get('actions', [])
        )
        
    except Exception as e:
        logger.error("Chat request failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/chat/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 50):
    """
    Get conversation history for a user
    """
    try:
        history = await db.get_chat_history(user_id, limit)
        return {"history": history}
    except Exception as e:
        logger.error("Failed to get chat history", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/history/{user_id}")
async def clear_chat_history(user_id: str):
    """
    Clear conversation history
    """
    try:
        await db.clear_chat_history(user_id)
        return {"success": True, "message": "Chat history cleared"}
    except Exception as e:
        logger.error("Failed to clear chat history", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
