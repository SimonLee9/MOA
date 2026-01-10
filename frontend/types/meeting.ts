/**
 * Meeting Types
 */

export type MeetingStatus = 'uploaded' | 'processing' | 'completed' | 'failed' | 'review_pending';
export type ActionItemStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled';
export type ActionItemPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface TranscriptSegment {
  id?: string;
  speaker: string;
  text: string;
  startTime: number;
  endTime: number;
  confidence?: number;
}

export interface ActionItem {
  id: string;
  meetingId: string;
  content: string;
  assignee?: string;
  dueDate?: string;
  priority: ActionItemPriority;
  status: ActionItemStatus;
  sourceText?: string;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
}

export interface ActionItemCreate {
  content: string;
  assignee?: string;
  dueDate?: string;
  priority?: ActionItemPriority;
}

export interface MeetingSummary {
  id: string;
  meetingId: string;
  summary: string;
  keyPoints: string[];
  decisions: string[];
  modelUsed?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Meeting {
  id: string;
  userId: string;
  title: string;
  description?: string;
  status: MeetingStatus;
  audioFileUrl?: string;
  audioFileName?: string;
  audioDuration?: number;
  audioFormat?: string;
  meetingDate?: string;
  errorMessage?: string;
  createdAt: string;
  updatedAt: string;
  processedAt?: string;
  summary?: MeetingSummary;
  transcripts?: TranscriptSegment[];
  actionItems?: ActionItem[];
}

export interface MeetingCreate {
  title: string;
  description?: string;
  meetingDate?: string;
}

export interface MeetingListResponse {
  items: Meeting[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ProcessingStatus {
  meetingId: string;
  status: MeetingStatus;
  progress?: number;
  currentStep?: string;
  errorMessage?: string;
}
