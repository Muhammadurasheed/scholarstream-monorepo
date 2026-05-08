// API Service Layer for ScholarStream Backend Integration
import { Scholarship, DiscoveryJobResponse, UserProfile } from '@/types/scholarship';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://scholarstream-backend-opdnpd6bsq-uc.a.run.app';

class ApiService {
  private async fetchWithAuth(endpoint: string, options: RequestInit = {}) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'Request failed' }));
        throw new Error(error.message || `HTTP ${response.status}`);
      }

      return response.json();
    } catch (error: any) {
      // Log detailed error for debugging
      console.error('API Request Failed:', {
        endpoint,
        error: error.message,
        baseUrl: API_BASE_URL,
      });

      // Provide more helpful error messages
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        throw new Error('Backend is not reachable. Please check your internet connection or backend URL.');
      }

      throw error;
    }
  }

  // Initial scholarship discovery after onboarding
  async discoverScholarships(userId: string, profile: UserProfile): Promise<DiscoveryJobResponse> {
    return this.fetchWithAuth('/api/scholarships/discover', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, profile }),
    });
  }

  // Poll for discovery progress
  async getDiscoveryProgress(jobId: string): Promise<DiscoveryJobResponse> {
    return this.fetchWithAuth(`/api/scholarships/discover/${jobId}`);
  }

  // Get all matched scholarships for a user
  async getMatchedScholarships(userId: string): Promise<{ scholarships: Scholarship[]; total_value: number; last_updated: string }> {
    return this.fetchWithAuth(`/api/scholarships/matched?user_id=${userId}`);
  }

  // Get single scholarship details
  async getScholarshipById(scholarshipId: string): Promise<Scholarship> {
    return this.fetchWithAuth(`/api/scholarships/${scholarshipId}`);
  }

  // Save scholarship to favorites
  async saveScholarship(userId: string, scholarshipId: string): Promise<void> {
    return this.fetchWithAuth('/api/scholarships/save', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, scholarship_id: scholarshipId }),
    });
  }

  // Remove from favorites
  async unsaveScholarship(userId: string, scholarshipId: string): Promise<void> {
    return this.fetchWithAuth('/api/scholarships/unsave', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, scholarship_id: scholarshipId }),
    });
  }

  // Application Management

  // Track application start
  async startApplication(userId: string, scholarshipId: string): Promise<{ application_id: string }> {
    return this.fetchWithAuth('/api/applications/start', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, scholarship_id: scholarshipId }),
    });
  }

  // Save application draft (auto-save)
  async saveDraft(
    userId: string,
    scholarshipId: string,
    draftData: Partial<ApplicationDraft>
  ): Promise<{ application_id: string; last_saved: string }> {
    return this.fetchWithAuth('/api/applications/draft/save', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        scholarship_id: scholarshipId,
        ...draftData,
      }),
    });
  }

  // Get application draft
  async getDraft(userId: string, scholarshipId: string): Promise<{ exists: boolean; draft: ApplicationDraft | null }> {
    return this.fetchWithAuth(`/api/applications/draft/${userId}/${scholarshipId}`);
  }

  // Submit final application
  async submitApplication(submissionData: any): Promise<{ confirmation_number: string; application_id: string }> {
    return this.fetchWithAuth('/api/applications/submit', {
      method: 'POST',
      body: JSON.stringify(submissionData),
    });
  }

  // Upload document
  async uploadDocument(
    file: File,
    userId: string,
    scholarshipId: string,
    documentType: string
  ): Promise<{ document: DocumentData }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);
    formData.append('scholarship_id', scholarshipId);
    formData.append('document_type', documentType);

    const response = await fetch(`${API_BASE_URL}/api/applications/document/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to upload document');
    }

    return response.json();
  }

  // Save essay
  async saveEssay(
    userId: string,
    scholarshipId: string,
    prompt: string,
    content: string,
    wordCount: number
  ): Promise<void> {
    return this.fetchWithAuth('/api/applications/essay/save', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        scholarship_id: scholarshipId,
        prompt,
        content,
        word_count: wordCount,
      }),
    });
  }

  // Get all user applications
  async getUserApplications(userId: string, status?: string): Promise<{ applications: ApplicationSubmission[]; stats: any }> {
    const url = status
      ? `/api/applications/user/${userId}?status=${status}`
      : `/api/applications/user/${userId}`;
    return this.fetchWithAuth(url);
  }

  // Get specific application
  async getApplication(applicationId: string): Promise<{ application: ApplicationSubmission }> {
    return this.fetchWithAuth(`/api/applications/${applicationId}`);
  }

  // Delete application draft
  async deleteApplication(applicationId: string): Promise<void> {
    return this.fetchWithAuth(`/api/applications/${applicationId}`, {
      method: 'DELETE',
    });
  }

  // Get real-time discovery pulse
  async getDiscoveryPulse(): Promise<{ status: 'active' | 'idle'; missions: any[]; timestamp: number }> {
    return this.fetchWithAuth('/api/scholarships/discovery-pulse');
  }
}

import type { ApplicationDraft, DocumentData, ApplicationSubmission } from '@/types/scholarship';

export const apiService = new ApiService();
