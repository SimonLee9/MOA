/**
 * E2E 테스트용 API 클라이언트
 */

import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

/**
 * API 클라이언트 인스턴스
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// 요청 인터셉터 (로깅)
apiClient.interceptors.request.use(
  (config) => {
    if (process.env.DEBUG) {
      console.log(`→ ${config.method?.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 응답 인터셉터 (로깅)
apiClient.interceptors.response.use(
  (response) => {
    if (process.env.DEBUG) {
      console.log(`← ${response.status} ${response.config.url}`);
    }
    return response;
  },
  (error: AxiosError) => {
    if (process.env.DEBUG) {
      console.error(`✗ ${error.response?.status || 'ERR'} ${error.config?.url}`);
    }
    return Promise.reject(error);
  }
);

/**
 * 인증된 API 클라이언트 생성
 */
export function createAuthenticatedClient(token: string): AxiosInstance {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });

  return client;
}

/**
 * API 응답 타입
 */
export interface ApiResponse<T = unknown> {
  data: T;
  message?: string;
}

export interface ApiListResponse<T = unknown> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
  code?: string;
  field?: string;
}

/**
 * 타입 안전한 API 호출 헬퍼
 */
export async function get<T>(url: string): Promise<AxiosResponse<ApiResponse<T>>> {
  return apiClient.get<ApiResponse<T>>(url);
}

export async function post<T>(url: string, data?: unknown): Promise<AxiosResponse<ApiResponse<T>>> {
  return apiClient.post<ApiResponse<T>>(url, data);
}

export async function put<T>(url: string, data?: unknown): Promise<AxiosResponse<ApiResponse<T>>> {
  return apiClient.put<ApiResponse<T>>(url, data);
}

export async function del<T>(url: string): Promise<AxiosResponse<ApiResponse<T>>> {
  return apiClient.delete<ApiResponse<T>>(url);
}

/**
 * 파일 업로드 헬퍼
 */
export async function uploadFile(
  url: string,
  file: Buffer | Blob,
  filename: string,
  additionalData?: Record<string, string>
): Promise<AxiosResponse> {
  const formData = new FormData();

  if (file instanceof Buffer) {
    formData.append('file', new Blob([file]), filename);
  } else {
    formData.append('file', file, filename);
  }

  if (additionalData) {
    Object.entries(additionalData).forEach(([key, value]) => {
      formData.append(key, value);
    });
  }

  return apiClient.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 120000, // 파일 업로드는 2분 타임아웃
  });
}
