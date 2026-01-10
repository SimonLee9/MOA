/**
 * API Response Transformation Utilities
 * Converts snake_case API responses to camelCase TypeScript interfaces
 */

type CamelCase<S extends string> = S extends `${infer P1}_${infer P2}${infer P3}`
  ? `${Lowercase<P1>}${Uppercase<P2>}${CamelCase<P3>}`
  : Lowercase<S>;

type KeysToCamelCase<T> = {
  [K in keyof T as CamelCase<string & K>]: T[K] extends object
    ? KeysToCamelCase<T[K]>
    : T[K];
};

type SnakeCase<S extends string> = S extends `${infer T}${infer U}`
  ? U extends Uncapitalize<U>
    ? `${Lowercase<T>}${SnakeCase<U>}`
    : `${Lowercase<T>}_${SnakeCase<U>}`
  : S;

type KeysToSnakeCase<T> = {
  [K in keyof T as SnakeCase<string & K>]: T[K] extends object
    ? KeysToSnakeCase<T[K]>
    : T[K];
};

/**
 * Convert string from snake_case to camelCase
 */
export function toCamelCase(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

/**
 * Convert string from camelCase to snake_case
 */
export function toSnakeCase(str: string): string {
  return str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
}

/**
 * Transform object keys from snake_case to camelCase
 */
export function transformToCamelCase<T extends Record<string, unknown>>(
  obj: T
): KeysToCamelCase<T> {
  if (obj === null || typeof obj !== 'object') {
    return obj as KeysToCamelCase<T>;
  }

  if (Array.isArray(obj)) {
    return obj.map((item) =>
      typeof item === 'object' && item !== null
        ? transformToCamelCase(item as Record<string, unknown>)
        : item
    ) as unknown as KeysToCamelCase<T>;
  }

  const result: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(obj)) {
    const camelKey = toCamelCase(key);
    if (value !== null && typeof value === 'object') {
      result[camelKey] = transformToCamelCase(value as Record<string, unknown>);
    } else {
      result[camelKey] = value;
    }
  }

  return result as KeysToCamelCase<T>;
}

/**
 * Transform object keys from camelCase to snake_case
 */
export function transformToSnakeCase<T extends Record<string, unknown>>(
  obj: T
): KeysToSnakeCase<T> {
  if (obj === null || typeof obj !== 'object') {
    return obj as KeysToSnakeCase<T>;
  }

  if (Array.isArray(obj)) {
    return obj.map((item) =>
      typeof item === 'object' && item !== null
        ? transformToSnakeCase(item as Record<string, unknown>)
        : item
    ) as unknown as KeysToSnakeCase<T>;
  }

  const result: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(obj)) {
    const snakeKey = toSnakeCase(key);
    if (value !== null && typeof value === 'object') {
      result[snakeKey] = transformToSnakeCase(value as Record<string, unknown>);
    } else {
      result[snakeKey] = value;
    }
  }

  return result as KeysToSnakeCase<T>;
}

/**
 * Field mapping for specific API endpoints
 */
export interface FieldMapping {
  apiField: string;
  clientField: string;
}

/**
 * Create a typed transformer for specific API response types
 */
export function createApiTransformer<TApi, TClient>(
  mappings?: FieldMapping[]
) {
  return {
    fromApi: (apiData: TApi): TClient => {
      if (mappings) {
        const result = { ...apiData } as Record<string, unknown>;
        for (const mapping of mappings) {
          if (mapping.apiField in result) {
            result[mapping.clientField] = result[mapping.apiField];
            delete result[mapping.apiField];
          }
        }
        return transformToCamelCase(result) as TClient;
      }
      return transformToCamelCase(apiData as Record<string, unknown>) as TClient;
    },
    toApi: (clientData: Partial<TClient>): Partial<TApi> => {
      const snakeData = transformToSnakeCase(clientData as Record<string, unknown>);
      if (mappings) {
        const result = { ...snakeData } as Record<string, unknown>;
        for (const mapping of mappings) {
          const snakeClientField = toSnakeCase(mapping.clientField);
          if (snakeClientField in result) {
            result[mapping.apiField] = result[snakeClientField];
            delete result[snakeClientField];
          }
        }
        return result as Partial<TApi>;
      }
      return snakeData as Partial<TApi>;
    },
  };
}

// ============ API Response Types (snake_case) ============

export interface ApiMeeting {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  status: string;
  audio_file_url?: string;
  audio_file_name?: string;
  audio_duration?: number;
  audio_format?: string;
  meeting_date?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
  processed_at?: string;
  summary?: ApiMeetingSummary;
  transcripts?: ApiTranscriptSegment[];
  action_items?: ApiActionItem[];
}

export interface ApiMeetingSummary {
  id: string;
  meeting_id: string;
  summary: string;
  key_points: string[];
  decisions: string[];
  model_used?: string;
  created_at: string;
  updated_at: string;
}

export interface ApiTranscriptSegment {
  id?: string;
  speaker: string;
  text: string;
  start_time: number;
  end_time: number;
  confidence?: number;
}

export interface ApiActionItem {
  id: string;
  meeting_id: string;
  content: string;
  assignee?: string;
  due_date?: string;
  priority: string;
  status: string;
  source_text?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface ApiPaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// ============ Transformers ============

export const meetingTransformer = createApiTransformer<ApiMeeting, import('@/types/meeting').Meeting>();
export const actionItemTransformer = createApiTransformer<ApiActionItem, import('@/types/meeting').ActionItem>();
export const summaryTransformer = createApiTransformer<ApiMeetingSummary, import('@/types/meeting').MeetingSummary>();

/**
 * Transform a paginated API response
 */
export function transformPaginatedResponse<TApi, TClient>(
  response: ApiPaginatedResponse<TApi>,
  itemTransformer: ReturnType<typeof createApiTransformer<TApi, TClient>>
): import('@/types/meeting').MeetingListResponse {
  return {
    items: response.items.map(item => itemTransformer.fromApi(item)),
    total: response.total,
    page: response.page,
    size: response.size,
    pages: response.pages,
  } as import('@/types/meeting').MeetingListResponse;
}
