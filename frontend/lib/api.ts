import axios from 'axios';
import type { Meeting, MeetingCreate, MeetingListResponse, MeetingSearchParams, ReviewStatus, ReviewDecision, ActionItem, ActionItemCreate } from '@/types/meeting';
import type { Team, TeamDetail, TeamCreate, TeamUpdate, TeamListResponse, TeamMember, TeamMemberAdd, TeamMemberUpdate, TeamInvitation, TeamInvitationCreate, TeamInvitationAccept } from '@/types/team';
import { transformToCamelCase, transformToSnakeCase } from './apiTransform';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor: Add auth token and transform body to snake_case
apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  // Transform request body to snake_case (except for FormData)
  if (config.data && !(config.data instanceof FormData)) {
    config.data = transformToSnakeCase(config.data as Record<string, unknown>);
  }
  return config;
});

// Response interceptor: Transform response data to camelCase
apiClient.interceptors.response.use(
  (response) => {
    if (response.data && typeof response.data === 'object') {
      response.data = transformToCamelCase(response.data as Record<string, unknown>);
    }
    return response;
  },
  (error) => {
    // Transform error response too
    if (error.response?.data && typeof error.response.data === 'object') {
      error.response.data = transformToCamelCase(error.response.data as Record<string, unknown>);
    }
    return Promise.reject(error);
  }
);

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
  async search(params: MeetingSearchParams): Promise<MeetingListResponse> {
    const queryParams: Record<string, string | number> = {};
    if (params.q) queryParams.q = params.q;
    if (params.status) queryParams.status = params.status;
    if (params.dateFrom) queryParams.date_from = params.dateFrom;
    if (params.dateTo) queryParams.date_to = params.dateTo;
    if (params.tag) queryParams.tag = params.tag;
    if (params.sortBy) queryParams.sort_by = params.sortBy;
    if (params.sortOrder) queryParams.sort_order = params.sortOrder;
    queryParams.page = params.page || 1;
    queryParams.size = params.size || 20;
    return (await apiClient.get('/meetings', { params: queryParams })).data;
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

export const tagsApi = {
  async listAll(): Promise<string[]> {
    const res = await apiClient.get('/meetings/tags/list');
    return res.data.tags || [];
  },
  async addTags(meetingId: string, tags: string[]): Promise<string[]> {
    const res = await apiClient.post(`/meetings/${meetingId}/tags`, tags);
    return res.data.tags || [];
  },
  async removeTag(meetingId: string, tag: string): Promise<string[]> {
    const res = await apiClient.delete(`/meetings/${meetingId}/tags/${encodeURIComponent(tag)}`);
    return res.data.tags || [];
  },
};

export const actionItemsApi = {
  async list(meetingId: string): Promise<ActionItem[]> {
    const res = await apiClient.get(`/meetings/${meetingId}/actions`);
    return res.data.map((item: any) => ({
      id: item.id,
      meetingId: item.meeting_id,
      content: item.content,
      assignee: item.assignee,
      dueDate: item.due_date,
      priority: item.priority,
      status: item.status,
      sourceText: item.source_text,
      createdAt: item.created_at,
      updatedAt: item.updated_at,
      completedAt: item.completed_at,
    }));
  },
  async create(meetingId: string, data: ActionItemCreate): Promise<ActionItem> {
    const payload = {
      content: data.content,
      assignee: data.assignee,
      due_date: data.dueDate,
      priority: data.priority || 'medium',
    };
    const res = await apiClient.post(`/meetings/${meetingId}/actions`, payload);
    return {
      id: res.data.id,
      meetingId: res.data.meeting_id,
      content: res.data.content,
      assignee: res.data.assignee,
      dueDate: res.data.due_date,
      priority: res.data.priority,
      status: res.data.status,
      sourceText: res.data.source_text,
      createdAt: res.data.created_at,
      updatedAt: res.data.updated_at,
      completedAt: res.data.completed_at,
    };
  },
  async update(meetingId: string, actionId: string, data: Partial<ActionItem>): Promise<ActionItem> {
    const payload: Record<string, any> = {};
    if (data.content !== undefined) payload.content = data.content;
    if (data.assignee !== undefined) payload.assignee = data.assignee;
    if (data.dueDate !== undefined) payload.due_date = data.dueDate;
    if (data.priority !== undefined) payload.priority = data.priority;
    if (data.status !== undefined) payload.status = data.status;
    const res = await apiClient.put(`/meetings/${meetingId}/actions/${actionId}`, payload);
    return {
      id: res.data.id,
      meetingId: res.data.meeting_id,
      content: res.data.content,
      assignee: res.data.assignee,
      dueDate: res.data.due_date,
      priority: res.data.priority,
      status: res.data.status,
      sourceText: res.data.source_text,
      createdAt: res.data.created_at,
      updatedAt: res.data.updated_at,
      completedAt: res.data.completed_at,
    };
  },
  async delete(meetingId: string, actionId: string): Promise<void> {
    await apiClient.delete(`/meetings/${meetingId}/actions/${actionId}`);
  },
};

// Dashboard metrics types
export interface WorkflowMetrics {
  totalMeetings: number;
  processing: number;
  completed: number;
  failed: number;
  pendingReview: number;
  avgProcessingTimeSeconds: number | null;
  successRate: number;
}

export interface DailyStats {
  date: string;
  meetingsCreated: number;
  meetingsCompleted: number;
  meetingsFailed: number;
}

export interface UserMetrics {
  totalMeetings: number;
  completedMeetings: number;
  pendingReview: number;
  totalActionItems: number;
  completedActionItems: number;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  database: string;
  redis: string;
  aiPipeline: string;
  timestamp: string;
}

export const metricsApi = {
  async getHealth(): Promise<SystemHealth> {
    return (await apiClient.get('/metrics/health')).data;
  },
  async getWorkflows(): Promise<WorkflowMetrics> {
    return (await apiClient.get('/metrics/workflows')).data;
  },
  async getDaily(days = 7): Promise<DailyStats[]> {
    return (await apiClient.get('/metrics/daily', { params: { days } })).data;
  },
  async getUser(): Promise<UserMetrics> {
    return (await apiClient.get('/metrics/user')).data;
  },
  async getPipelineStatus() {
    return (await apiClient.get('/metrics/pipeline/status')).data;
  },
};

export type ExportFormat = 'markdown' | 'html' | 'json';

export const exportApi = {
  async downloadMarkdown(meetingId: string): Promise<Blob> {
    const res = await apiClient.get(`/export/${meetingId}/markdown`, {
      responseType: 'blob',
    });
    return res.data;
  },
  async downloadHtml(meetingId: string): Promise<Blob> {
    const res = await apiClient.get(`/export/${meetingId}/html`, {
      responseType: 'blob',
    });
    return res.data;
  },
  async downloadJson(meetingId: string): Promise<Blob> {
    const res = await apiClient.get(`/export/${meetingId}/json`, {
      responseType: 'blob',
    });
    return res.data;
  },
  async download(meetingId: string, format: ExportFormat): Promise<void> {
    let blob: Blob;
    let extension: string;
    let mimeType: string;

    switch (format) {
      case 'markdown':
        blob = await this.downloadMarkdown(meetingId);
        extension = 'md';
        mimeType = 'text/markdown';
        break;
      case 'html':
        blob = await this.downloadHtml(meetingId);
        extension = 'html';
        mimeType = 'text/html';
        break;
      case 'json':
        blob = await this.downloadJson(meetingId);
        extension = 'json';
        mimeType = 'application/json';
        break;
    }

    // Create download link
    const url = window.URL.createObjectURL(new Blob([blob], { type: mimeType }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `meeting_${meetingId}.${extension}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};

// Notification types
export interface NotificationItem {
  id: string;
  type: string;
  title: string;
  message: string;
  isRead: boolean;
  meetingId?: string;
  createdAt: string;
  readAt?: string;
}

export interface NotificationListResponse {
  items: NotificationItem[];
  total: number;
  unreadCount: number;
}

export interface NotificationStats {
  total: number;
  unread: number;
  byType: Record<string, number>;
}

export const notificationsApi = {
  async list(params?: { unreadOnly?: boolean; type?: string; limit?: number; offset?: number }): Promise<NotificationListResponse> {
    const queryParams: Record<string, string | number | boolean> = {};
    if (params?.unreadOnly) queryParams.unread_only = params.unreadOnly;
    if (params?.type) queryParams.type = params.type;
    if (params?.limit) queryParams.limit = params.limit;
    if (params?.offset) queryParams.offset = params.offset;
    const res = await apiClient.get('/notifications', { params: queryParams });
    return {
      items: res.data.items.map((item: any) => ({
        id: item.id,
        type: item.type,
        title: item.title,
        message: item.message,
        isRead: item.isRead,
        meetingId: item.meetingId,
        createdAt: item.createdAt,
        readAt: item.readAt,
      })),
      total: res.data.total,
      unreadCount: res.data.unreadCount,
    };
  },
  async getStats(): Promise<NotificationStats> {
    const res = await apiClient.get('/notifications/stats');
    return {
      total: res.data.total,
      unread: res.data.unread,
      byType: res.data.byType,
    };
  },
  async markAsRead(notificationId: string): Promise<void> {
    await apiClient.post(`/notifications/${notificationId}/read`);
  },
  async markAllAsRead(): Promise<void> {
    await apiClient.post('/notifications/read-all');
  },
  async delete(notificationId: string): Promise<void> {
    await apiClient.delete(`/notifications/${notificationId}`);
  },
};

// Teams API
export const teamsApi = {
  async list(page = 1, size = 20): Promise<TeamListResponse> {
    const res = await apiClient.get('/teams', { params: { page, size } });
    return res.data;
  },
  async get(teamId: string): Promise<TeamDetail> {
    const res = await apiClient.get(`/teams/${teamId}`);
    return res.data;
  },
  async create(data: TeamCreate): Promise<Team> {
    const res = await apiClient.post('/teams', data);
    return res.data;
  },
  async update(teamId: string, data: TeamUpdate): Promise<Team> {
    const res = await apiClient.patch(`/teams/${teamId}`, data);
    return res.data;
  },
  async delete(teamId: string): Promise<void> {
    await apiClient.delete(`/teams/${teamId}`);
  },
  // Members
  async addMember(teamId: string, data: TeamMemberAdd): Promise<TeamMember> {
    const res = await apiClient.post(`/teams/${teamId}/members`, data);
    return res.data;
  },
  async updateMember(teamId: string, userId: string, data: TeamMemberUpdate): Promise<TeamMember> {
    const res = await apiClient.patch(`/teams/${teamId}/members/${userId}`, data);
    return res.data;
  },
  async removeMember(teamId: string, userId: string): Promise<void> {
    await apiClient.delete(`/teams/${teamId}/members/${userId}`);
  },
  // Invitations
  async createInvitation(teamId: string, data: TeamInvitationCreate): Promise<TeamInvitation> {
    const res = await apiClient.post(`/teams/${teamId}/invitations`, data);
    return res.data;
  },
  async getPendingInvitations(): Promise<TeamInvitation[]> {
    const res = await apiClient.get('/teams/invitations/pending');
    return res.data;
  },
  async acceptInvitation(data: TeamInvitationAccept): Promise<TeamMember> {
    const res = await apiClient.post('/teams/invitations/accept', data);
    return res.data;
  },
  async cancelInvitation(teamId: string, invitationId: string): Promise<void> {
    await apiClient.delete(`/teams/${teamId}/invitations/${invitationId}`);
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
