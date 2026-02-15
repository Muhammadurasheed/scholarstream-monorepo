"""
Pydantic models for ScholarStream API
Data validation and serialization schemas
"""
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


# Enums and Type Literals
DeadlineType = Literal["rolling", "fixed"]
MatchTier = Literal["Excellent", "Good", "Fair", "Poor"]
PriorityLevel = Literal["URGENT", "HIGH", "MEDIUM", "LOW"]
CompetitionLevel = Literal["Low", "Medium", "High"]
SourceType = Literal["scraped", "ai_discovered", "curated"]
DiscoveryStatus = Literal["idle", "processing", "completed", "failed"]


# User Profile Models
class UserProfile(BaseModel):
    """User profile data from onboarding"""
    """User profile data from onboarding"""
    name: str = "Student" # Relaxed validation
    academic_status: str = "Unknown" # Relaxed validation
    school: Optional[str] = None
    year: Optional[str] = None
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    major: Optional[str] = None
    graduation_year: Optional[str] = None
    background: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    country: Optional[str] = "United States"
    state: Optional[str] = None
    city: Optional[str] = None
    
    @validator('gpa')
    def validate_gpa(cls, v):
        if v is not None and (v < 0 or v > 4.0):
            raise ValueError('GPA must be between 0.0 and 4.0')
        return v

# Deep Profile Models (The "Digital DNA")
class Project(BaseModel):
    """A portfolio project or hackathon submission"""
    title: str
    description: str = Field(..., description="Detailed description for RAG")
    tech_stack: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    role: Optional[str] = None

class WorkExperience(BaseModel):
    """Professional experience"""
    role: str
    company: str
    start_date: str
    end_date: Optional[str] = None
    description: str

class DeepUserProfile(BaseModel):
    """
    The Detailed 'Application Builder' Profile.
    Vectorized and stored in 'user.identity.v1'
    """
    # Core Identity
    name: str
    bio: str = Field(..., description="Professional summary")
    location: str
    
    # Skills (The Resume Layer)
    hard_skills: List[str] = Field(default_factory=list, description="Top tech skills")
    soft_skills: List[str] = Field(default_factory=list, description="Leadership, Communication")
    
    # Portfolio
    projects: List[Project] = Field(default_factory=list)
    experience: List[WorkExperience] = Field(default_factory=list)
    
    # Demographics (for eligibility tags)
    demographics: List[str] = Field(default_factory=list, description="['Nigeria', 'Student', 'Underrepresented']")
    
    # Education
    school: str
    major: str
    graduation_year: str
    gpa: float

    # System Fields
    vector_id: Optional[str] = None # Link to Pinecone/Firestore Vector



# Scholarship Models
class ScholarshipEligibility(BaseModel):
    """Eligibility criteria for a scholarship"""
    gpa_min: Optional[float] = None
    grades_eligible: List[str] = Field(default_factory=list)
    majors: Optional[List[str]] = None
    gender: Optional[str] = None
    citizenship: Optional[str] = None
    backgrounds: List[str] = Field(default_factory=list)
    states: Optional[List[str]] = None


class ScholarshipRequirements(BaseModel):
    """Application requirements for a scholarship"""
    essay: bool = False
    essay_prompts: List[str] = Field(default_factory=list)
    recommendation_letters: int = Field(default=0, ge=0)
    transcript: bool = False
    resume: bool = False
    other: List[str] = Field(default_factory=list)


# System Manifest V1 Schema (The "Refinery" Output)
class OpportunitySchema(BaseModel):
    """
    The Single Source of Truth for Enriched Opportunities.
    Topic: opportunity.enriched.v1
    """
    id: str = Field(..., description="Unique hash of source_url")
    title: Optional[str] = None
    name: str = Field(..., description="Opportunity Name")
    organization: Optional[str] = "Unknown Organization"
    amount: float = Field(default=0.0)
    amount_display: Optional[str] = None
    
    # CRITICAL: Expiry Logic
    deadline: Optional[str] = None  # ISO 8601
    deadline_timestamp: Optional[int] = Field(None, description="Unix timestamp for high-speed filtering")
    
    # Intelligence Tags
    geo_tags: List[str] = Field(default_factory=list, description="['Global', 'Nigeria', 'Lagos']")
    type_tags: List[str] = Field(default_factory=list, description="['Bounty', 'Hackathon', 'Grant']")
    tags: List[str] = Field(default_factory=list, description="Legacy tags field for compatibility")
    
    # Metadata
    source_url: str
    description: Optional[str] = "No description provided"
    match_score: float = 0.0
    match_reasons: List[str] = Field(default_factory=list)
    
    # Enriched Fields (The missing link)
    priority_level: Optional[PriorityLevel] = "MEDIUM"
    match_tier: Optional[MatchTier] = "Fair"
    competition_level: Optional[CompetitionLevel] = "Medium"

    # Vectorization
    embedding: Optional[List[float]] = Field(None, description="768-dim vector embedding")
    
    # Raw Eligibility (for deeper checks)
    eligibility_text: Optional[str] = None

    # Structured Requirements (Added for compatibility with MatchingEngine)
    eligibility: ScholarshipEligibility = Field(default_factory=ScholarshipEligibility)
    requirements: ScholarshipRequirements = Field(default_factory=ScholarshipRequirements)
    
    # System Metadata
    last_verified: Optional[str] = None
    source_type: Optional[str] = Field(None, description="Platform source: devpost, dorahacks, immunefi, superteam, etc.")
    
    class Config:
        extra = "ignore" 

# Alias for backward compatibility if needed, but prefer OpportunitySchema
Scholarship = OpportunitySchema


# API Request/Response Models
class DiscoverRequest(BaseModel):
    """Request body for scholarship discovery"""
    user_id: str = Field(..., min_length=1)
    profile: UserProfile


class DiscoveryJobResponse(BaseModel):
    """Response for discovery job status"""
    status: DiscoveryStatus
    immediate_results: Optional[List[Scholarship]] = None
    job_id: Optional[str] = None
    estimated_completion: Optional[int] = None  # seconds
    progress: Optional[float] = Field(None, ge=0, le=100)
    new_scholarships: Optional[List[Scholarship]] = None
    total_found: Optional[int] = None


class MatchedScholarshipsResponse(BaseModel):
    """Response for matched scholarships list"""
    scholarships: List[Scholarship]
    total_value: float
    last_updated: str  # ISO format datetime string


class SaveScholarshipRequest(BaseModel):
    """Request to save/unsave a scholarship"""
    user_id: str = Field(..., min_length=1)
    scholarship_id: str = Field(..., min_length=1)


class StartApplicationRequest(BaseModel):
    """Request to start an application"""
    user_id: str = Field(..., min_length=1)
    scholarship_id: str = Field(..., min_length=1)


# Application Management Models
ApplicationStatus = Literal["draft", "submitted", "under_review", "finalist", "awarded", "declined", "expired"]


class PersonalInfoData(BaseModel):
    """Personal information section of application"""
    full_name: str
    preferred_name: Optional[str] = None
    email: str
    phone: str
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    mailing_address: Dict[str, str] = Field(default_factory=dict)
    permanent_address: Optional[Dict[str, str]] = None
    school_name: str
    student_id: Optional[str] = None
    grade_level: str
    major: Optional[str] = None
    minor: Optional[str] = None
    expected_graduation: Optional[str] = None
    gpa: Optional[float] = None
    gpa_scale: str = "4.0"
    citizenship_status: Optional[str] = None
    ethnicity: List[str] = Field(default_factory=list)


class DocumentData(BaseModel):
    """Document upload data"""
    document_type: str
    file_name: str
    file_url: str
    cloudinary_public_id: str
    uploaded_at: str
    file_size: Optional[int] = None


class EssayData(BaseModel):
    """Essay/short answer data"""
    prompt: str
    content: str
    word_count: int
    last_edited: str


class RecommenderData(BaseModel):
    """Recommendation letter tracking"""
    name: str
    email: str
    relationship: str
    subject_context: Optional[str] = None
    phone: Optional[str] = None
    status: Literal["not_requested", "requested", "agreed", "submitted", "declined"]
    requested_at: Optional[str] = None
    submitted_at: Optional[str] = None
    letter_url: Optional[str] = None


class ApplicationDraft(BaseModel):
    """Draft application data (auto-saved)"""
    application_id: str
    user_id: str
    scholarship_id: str
    status: ApplicationStatus = "draft"
    current_step: int = 1
    progress_percentage: float = 0.0
    personal_info: Optional[PersonalInfoData] = None
    documents: List[DocumentData] = Field(default_factory=list)
    essays: List[EssayData] = Field(default_factory=list)
    recommenders: List[RecommenderData] = Field(default_factory=list)
    additional_answers: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str
    last_saved: str


class ApplicationSubmission(BaseModel):
    """Complete submitted application"""
    application_id: str
    user_id: str
    scholarship_id: str
    scholarship_name: str
    scholarship_amount: float
    status: ApplicationStatus = "submitted"
    confirmation_number: str
    personal_info: PersonalInfoData
    documents: List[DocumentData]
    essays: List[EssayData]
    recommenders: List[RecommenderData]
    additional_answers: Dict[str, Any] = Field(default_factory=dict)
    submitted_at: str
    decision_date: Optional[str] = None
    award_amount: Optional[float] = None
    notes: Optional[str] = None


# API Request Models
class SaveDraftRequest(BaseModel):
    """Request to save application draft"""
    user_id: str = Field(..., min_length=1)
    scholarship_id: str = Field(..., min_length=1)
    current_step: int = Field(..., ge=1, le=6)
    progress_percentage: float = Field(..., ge=0, le=100)
    personal_info: Optional[PersonalInfoData] = None
    documents: Optional[List[DocumentData]] = None
    essays: Optional[List[EssayData]] = None
    recommenders: Optional[List[RecommenderData]] = None
    additional_answers: Optional[Dict[str, Any]] = None


class SubmitApplicationRequest(BaseModel):
    """Request to submit final application"""
    user_id: str = Field(..., min_length=1)
    scholarship_id: str = Field(..., min_length=1)
    scholarship_name: str
    scholarship_amount: float
    personal_info: PersonalInfoData
    documents: List[DocumentData]
    essays: List[EssayData]
    recommenders: List[RecommenderData]
    additional_answers: Dict[str, Any] = Field(default_factory=dict)
    certifications: Dict[str, bool] = Field(default_factory=dict)


class UploadDocumentRequest(BaseModel):
    """Request to upload document to Cloudinary"""
    user_id: str
    scholarship_id: str
    document_type: str
    file_data: str  # Base64 encoded file
    file_name: str


class SaveEssayRequest(BaseModel):
    """Request to save essay draft"""
    user_id: str
    scholarship_id: str
    prompt: str
    content: str
    word_count: int


class ErrorResponse(BaseModel):
    """Standard error response format"""
    error: str
    detail: Optional[str] = None
    status_code: int


# Internal Models for Processing
class ScrapedScholarship(BaseModel):
    """Raw scholarship data from scraping"""
    name: str
    organization: str
    amount: float
    deadline: str
    description: str
    source_url: str
    eligibility_raw: Optional[str] = None
    requirements_raw: Optional[str] = None


class AIEnrichmentRequest(BaseModel):
    """Request for AI to enrich scholarship data"""
    scholarship: ScrapedScholarship
    user_profile: UserProfile


class AIEnrichmentResponse(BaseModel):
    """AI-enriched scholarship data"""
    eligibility: ScholarshipEligibility
    requirements: ScholarshipRequirements
    tags: List[str]
    match_score: float
    match_tier: MatchTier
    priority_level: PriorityLevel
    competition_level: CompetitionLevel
    estimated_time: str
