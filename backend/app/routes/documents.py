"""
Document Processing API Endpoints
Handles document upload, parsing, and text extraction for PDF/DOCX/TXT files
"""
from fastapi import APIRouter, HTTPException, Header, UploadFile, File
from typing import Optional
import structlog
import io
import re

from firebase_admin import auth

router = APIRouter(prefix="/api/documents", tags=["documents"])
logger = structlog.get_logger()


async def verify_token(authorization: str) -> str:
    """Verify Firebase token from Authorization header"""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split('Bearer ')[1]
    
    if token == 'TEST_TOKEN' or 'TEST_TOKEN' in token:
        logger.warning("Blocked attempt to use TEST_TOKEN")
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token['uid']
    except Exception as e:
        logger.error("Token verification failed", error=str(e))
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def extract_text_from_pdf(content: bytes) -> str:
    """Extract text from PDF using PyPDF2"""
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text() or '')
        return '\n\n'.join(text_parts)
    except ImportError:
        logger.warning("PyPDF2 not installed, falling back to basic extraction")
        # Return placeholder if PyPDF2 not available
        return "[PDF content - please install PyPDF2 for full extraction]"
    except Exception as e:
        logger.error("PDF extraction failed", error=str(e))
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")


def extract_text_from_docx(content: bytes) -> str:
    """Extract text from DOCX using python-docx"""
    try:
        from docx import Document
        doc = Document(io.BytesIO(content))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return '\n\n'.join(paragraphs)
    except ImportError:
        logger.warning("python-docx not installed, falling back to basic extraction")
        return "[DOCX content - please install python-docx for full extraction]"
    except Exception as e:
        logger.error("DOCX extraction failed", error=str(e))
        raise HTTPException(status_code=400, detail=f"Failed to parse DOCX: {str(e)}")


def clean_extracted_text(text: str) -> str:
    """Clean and normalize extracted text"""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = text.strip()
    return text


@router.post("/parse")
async def parse_document(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """
    Parse uploaded document and extract text content
    
    Supports:
    - PDF files
    - DOCX files  
    - TXT/MD/JSON files (plain text)
    
    Returns extracted text content for use as project context
    """
    user_id = await verify_token(authorization)
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    filename = file.filename.lower()
    content = await file.read()
    
    # Size limit: 5MB
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB.")
    
    logger.info("Parsing document", user_id=user_id, filename=file.filename, size=len(content))
    
    extracted_text = ""
    file_type = "unknown"
    
    try:
        if filename.endswith('.pdf'):
            file_type = "pdf"
            extracted_text = extract_text_from_pdf(content)
        elif filename.endswith('.docx'):
            file_type = "docx"
            extracted_text = extract_text_from_docx(content)
        elif filename.endswith(('.txt', '.md', '.json', '.csv', '.readme')):
            file_type = "text"
            extracted_text = content.decode('utf-8', errors='ignore')
        else:
            # Try to decode as text
            try:
                file_type = "text"
                extracted_text = content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file type. Supported: PDF, DOCX, TXT, MD, JSON"
                )
        
        # Clean the extracted text
        extracted_text = clean_extracted_text(extracted_text)
        
        # Truncate if too long (50k chars max for context)
        max_chars = 50000
        was_truncated = len(extracted_text) > max_chars
        if was_truncated:
            extracted_text = extracted_text[:max_chars] + "\n\n[Content truncated due to length...]"
        
        logger.info(
            "Document parsed successfully",
            user_id=user_id,
            filename=file.filename,
            file_type=file_type,
            char_count=len(extracted_text),
            was_truncated=was_truncated
        )
        
        return {
            "success": True,
            "filename": file.filename,
            "file_type": file_type,
            "content": extracted_text,
            "char_count": len(extracted_text),
            "was_truncated": was_truncated,
            "message": f"Successfully extracted {len(extracted_text):,} characters from {file.filename}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Document parsing failed", user_id=user_id, filename=file.filename, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {str(e)}")


@router.get("/supported-types")
async def get_supported_types():
    """Return list of supported document types"""
    return {
        "supported_types": [
            {"extension": ".pdf", "name": "PDF Document", "mime": "application/pdf"},
            {"extension": ".docx", "name": "Word Document", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
            {"extension": ".txt", "name": "Text File", "mime": "text/plain"},
            {"extension": ".md", "name": "Markdown File", "mime": "text/markdown"},
            {"extension": ".json", "name": "JSON File", "mime": "application/json"},
        ],
        "max_size_mb": 5
    }
