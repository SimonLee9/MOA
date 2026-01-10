import axios from 'axios';
import type { Meeting, MeetingCreate, MeetingListResponse, ReviewStatus, ReviewDecision } from '@/types/meeting';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authApi = {
  async login(email: string, password: string) {
    const res = await apiClient.post('/auth/login', { email, password });
    localStorage.setItem('access_token', res.data.access_token);
    return res.data;
  },
  async register(email: string, password: string, name: string) {
    return (await apiClient.post('/auth/register', { email, password, name })).data;
  },
  logout() { localStorage.removeItem('access_token'); },
  isAuthenticated() { return typeof window !== 'undefined' && !!localStorage.getItem('access_token'); },
};

export const meetingsApi = {
  async list(page = 1, size = 20): Promise<MeetingListResponse> {
    return (await apiClient.get('/meetings', { params: { page, size } })).data;
  },
  async get(id: string): Promise<Meeting> {
    return (await apiClient.get(`/meetings/${id}`)).data;
  },
  async create(data: MeetingCreate): Promise<Meeting> {
    return (await apiClient.post('/meetings', data)).data;
  },
  async delete(id: string): Promise<void> {
    await apiClient.delete(`/meetings/${id}`);
  },
  async uploadAudio(meetingId: string, file: File, onProgress?: (p: number) => void) {
    const formData = new FormData();
    formData.append('audio_file', file);
    return (await apiClient.post(`/meetings/${meetingId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => onProgress && e.total && onProgress(Math.round((e.loaded * 100) / e.total)),
    })).data;
  },
  async startProcessing(meetingId: string) {
    return (await apiClient.post(`/meetings/${meetingId}/process`)).data;
  },
};

export const reviewApi = {
  async getStatus(meetingId: string): Promise<ReviewStatus> {
    const res = await apiClient.get(`/meetings/${meetingId}/review`);
    // Convert snake_case to camelCase
    return {
      meetingId: res.data.meeting_id,
      status: res.data.status,
      requiresReview: res.data.requires_review,
      reviewData: res.data.review_data ? {
        minutes: res.data.review_data.minutes,
        keyPoints: res.data.review_data.key_points,
        decisions: res.data.review_data.decisions,
        proposedActions: res.data.review_data.proposed_actions,
        critique: res.data.review_data.critique,
        retryCount: res.data.review_data.retry_count,
      } : undefined,
    };
  },
  async submit(meetingId: string, decision: ReviewDecision) {
    // Convert camelCase to snake_case
    const payload = {
      action: decision.action,
      feedback: decision.feedback,
      updated_summary: decision.updatedSummary,
      updated_key_points: decision.updatedKeyPoints,
      updated_decisions: decision.updatedDecisions,
      updated_actions: decision.updatedActions?.map(a => ({
        id: a.id,
        content: a.content,
        assignee: a.assignee,
        due_date: a.dueDate,
        priority: a.priority,
        status: a.status || 'approved',
      })),
    };
    return (await apiClient.post(`/meetings/${meetingId}/review`, payload)).data;
  },
  async getResults(meetingId: string) {
    return (await apiClient.get(`/meetings/${meetingId}/results`)).data;
  },
};

export default apiClient;
