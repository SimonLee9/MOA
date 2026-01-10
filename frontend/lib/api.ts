import axios from 'axios';
import type { Meeting, MeetingCreate, MeetingListResponse } from '@/types/meeting';

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

export default apiClient;
