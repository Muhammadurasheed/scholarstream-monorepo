/**
 * Extension Configuration
 * Centralizes all environment-dependent settings
 */

// API Configuration
export const API_URL = 'https://scholarstream-backend-opdnpd6bsq-uc.a.run.app';
// export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8081';

// Derived API endpoints
export const ENDPOINTS = {
  chat: `${API_URL}/api/extension/chat`,
  mapFields: `${API_URL}/api/extension/map-fields`,
  userProfile: `${API_URL}/api/extension/user-profile`,
  saveApplicationData: `${API_URL}/api/extension/save-application-data`,
  parseDocument: `${API_URL}/api/documents/parse`,
  supportedTypes: `${API_URL}/api/documents/supported-types`,
};

// WebSocket URL (derived from API URL)
export const WS_URL = API_URL.replace('http', 'ws') + '/ws/opportunities';

// Platform detection patterns
export const PLATFORM_PATTERNS = {
  devpost: /devpost\.com/i,
  dorahacks: /dorahacks\.io/i,
  mlh: /mlh\.io/i,
  hackathon: /hackathon|hack\s*a\s*thon/i,
  scholarship: /scholarship|grant|fellowship/i,
  bounty: /bounty|bug\s*bounty|intigriti|hackerone/i,
  taikai: /taikai\.network/i,
};

/**
 * Detect the platform from a URL
 */
export function detectPlatform(url: string): string {
  if (PLATFORM_PATTERNS.devpost.test(url)) return 'DevPost';
  if (PLATFORM_PATTERNS.dorahacks.test(url)) return 'DoraHacks';
  if (PLATFORM_PATTERNS.mlh.test(url)) return 'MLH';
  if (PLATFORM_PATTERNS.taikai.test(url)) return 'Taikai';
  if (PLATFORM_PATTERNS.bounty.test(url)) return 'Bug Bounty';
  if (PLATFORM_PATTERNS.scholarship.test(url)) return 'Scholarship';
  if (PLATFORM_PATTERNS.hackathon.test(url)) return 'Hackathon';
  return 'Unknown';
}

/**
 * Calculate profile completeness percentage
 */
export function calculateProfileCompleteness(profile: any): number {
  if (!profile) return 0;

  const weights = {
    // Core identity (40%)
    full_name: 10,
    email: 10,
    bio: 20,

    // Academic (20%)
    school_name: 5,
    major: 5,
    graduation_year: 5,
    gpa: 5,

    // Skills (20%)
    hard_skills: 10,
    soft_skills: 10,

    // Portfolio (20%)
    projects: 10,
    experience: 10,
  };

  let score = 0;

  // Check each field
  if (profile.full_name || (profile.first_name && profile.last_name)) score += weights.full_name;
  if (profile.email) score += weights.email;
  if (profile.bio && profile.bio.length > 20) score += weights.bio;
  if (profile.academic?.school_name || profile.school) score += weights.school_name;
  if (profile.academic?.major || profile.major) score += weights.major;
  if (profile.academic?.graduation_year || profile.graduation_year) score += weights.graduation_year;
  if (profile.academic?.gpa || profile.gpa) score += weights.gpa;
  if (profile.hard_skills?.length > 0 || profile.skills?.length > 0) score += weights.hard_skills;
  if (profile.soft_skills?.length > 0) score += weights.soft_skills;
  if (profile.projects?.length > 0) score += weights.projects;
  if (profile.experience?.length > 0) score += weights.experience;

  return Math.min(100, score);
}

// ========== DOCUMENT CONTEXT TYPES ==========

/**
 * Uploaded document context interface
 */
export interface UploadedDocument {
  id: string;
  filename: string;
  content: string;
  uploadedAt: number; // timestamp
  charCount: number;
  fileType: string;
  platformHint?: string;
}

/**
 * Context status for sidebar display
 */
export interface ContextStatus {
  profileCompleteness: number;
  hasDocument: boolean;
  documentName: string | null;
  documentCharCount: number;
  platform: string;
  pageUrl: string;
  isProcessing: boolean;
  processingError: string | null;
}

/**
 * Parse a document via backend API
 * Supports PDF, DOCX, TXT, MD, JSON
 */
export async function parseDocument(
  file: File,
  authToken: string
): Promise<{
  success: boolean;
  content: string;
  charCount: number;
  fileType: string;
  error?: string
}> {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(ENDPOINTS.parseDocument, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      content: data.content,
      charCount: data.char_count,
      fileType: data.file_type,
    };
  } catch (error) {
    return {
      success: false,
      content: '',
      charCount: 0,
      fileType: 'unknown',
      error: error instanceof Error ? error.message : 'Failed to parse document',
    };
  }
}

/**
 * Generate a unique document ID
 */
export function generateDocumentId(): string {
  return `doc_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}
