// Scholarship Type Definitions for ScholarStream

export type DeadlineType = 'rolling' | 'fixed' | 'ongoing';
export type MatchTier = 'excellent' | 'great' | 'good' | 'potential' | 'low' | 'Excellent' | 'Good' | 'Fair' | 'Poor' | 'Low';
export type PriorityLevel = 'urgent' | 'high' | 'medium' | 'low' | 'URGENT' | 'HIGH' | 'MEDIUM' | 'LOW';
export type CompetitionLevel = 'Low' | 'Medium' | 'High';
export type SourceType = 'platform' | 'devpost' | 'gitcoin' | 'kaggle' | 'mlh' | 'government' | 'scholarships_com' | 'ai_discovered' | 'curated';

export interface ScholarshipEligibility {
  gpa_min: number | null;
  grades_eligible: string[];
  majors: string[] | null;
  gender: string | null;
  citizenship: string | null;
  backgrounds: string[];
  states: string[] | null;
}

export interface ScholarshipRequirements {
  essay: boolean;
  essay_prompts: string[];
  recommendation_letters: number;
  transcript: boolean;
  resume: boolean;
  other: string[];
}

export interface Scholarship {
  id: string;
  name: string;
  organization: string;
  logo_url: string | null;

  amount: number;
  amount_display: string;
  deadline: string;
  deadline_type: DeadlineType;

  eligibility: ScholarshipEligibility;
  requirements: ScholarshipRequirements;

  match_score: number;
  match_tier: MatchTier;
  priority_level: PriorityLevel;

  tags: string[];
  description: string;
  competition_level: CompetitionLevel;
  estimated_time: string;
  expected_value: number;

  source_url: string;
  source_type: SourceType;
  discovered_at: string;
  last_verified: string;
}

export interface DiscoveryJobResponse {
  status: 'processing' | 'completed' | 'failed';
  immediate_results?: Scholarship[];
  job_id?: string;
  estimated_completion?: number;
  progress?: number;
  new_scholarships?: Scholarship[];
  total_found?: number;
}

export interface UserProfile {
  name: string;
  academic_status: string;
  school: string;
  year?: string;
  gpa?: number;
  major?: string;
  graduation_year?: string;
  background?: string[];
  financial_need?: number;
  interests?: string[];
  country?: string;
  state?: string;
  city?: string;
}

export interface DashboardStats {
  opportunities_matched: number;
  total_value: number;
  urgent_deadlines: number;
  applications_started: number;
}

export type ViewMode = 'grid' | 'list';
export type SortOption = 'best_match' | 'deadline' | 'amount' | 'time' | 'recent';
export type FilterTab = 'all' | 'high_priority' | 'closing_soon' | 'high_value' | 'best_match';

// Application Management Types
export type ApplicationStatus = 'draft' | 'submitted' | 'under_review' | 'finalist' | 'awarded' | 'declined' | 'expired';

export interface PersonalInfoData {
  full_name: string;
  preferred_name?: string;
  email: string;
  phone: string;
  date_of_birth?: string;
  gender?: string;
  mailing_address: Record<string, string>;
  permanent_address?: Record<string, string>;
  school_name: string;
  student_id?: string;
  grade_level: string;
  major?: string;
  minor?: string;
  expected_graduation?: string;
  gpa?: number;
  gpa_scale: string;
  citizenship_status?: string;
  ethnicity: string[];
}

export interface DocumentData {
  document_type: string;
  file_name: string;
  file_url: string;
  cloudinary_public_id: string;
  uploaded_at: string;
  file_size?: number;
}

export interface EssayData {
  prompt: string;
  content: string;
  word_count: number;
  last_edited: string;
}

export interface RecommenderData {
  name: string;
  email: string;
  relationship: string;
  subject_context?: string;
  phone?: string;
  status: 'not_requested' | 'requested' | 'agreed' | 'submitted' | 'declined';
  requested_at?: string;
  submitted_at?: string;
  letter_url?: string;
}

export interface ApplicationDraft {
  application_id: string;
  user_id: string;
  scholarship_id: string;
  status: ApplicationStatus;
  current_step: number;
  progress_percentage: number;
  personal_info?: PersonalInfoData;
  documents: DocumentData[];
  essays: EssayData[];
  recommenders: RecommenderData[];
  additional_answers: Record<string, any>;
  created_at: string;
  updated_at: string;
  last_saved: string;
}

export interface ApplicationSubmission {
  application_id: string;
  user_id: string;
  scholarship_id: string;
  scholarship_name: string;
  scholarship_amount: number;
  status: ApplicationStatus;
  confirmation_number: string;
  personal_info: PersonalInfoData;
  documents: DocumentData[];
  essays: EssayData[];
  recommenders: RecommenderData[];
  additional_answers: Record<string, any>;
  submitted_at: string;
  decision_date?: string;
  award_amount?: number;
  notes?: string;
}
