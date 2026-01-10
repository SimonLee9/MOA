import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });
}

export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}시간 ${minutes}분`;
  return `${minutes}분`;
}

export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  
  if (minutes < 1) return '방금 전';
  if (minutes < 60) return `${minutes}분 전`;
  if (hours < 24) return `${hours}시간 전`;
  if (days < 7) return `${days}일 전`;
  return formatDate(d);
}

export function formatTimestamp(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export type MeetingStatus = 'uploaded' | 'processing' | 'completed' | 'failed' | 'review_pending';

export function getStatusLabel(status: MeetingStatus): string {
  const labels: Record<MeetingStatus, string> = {
    uploaded: '업로드됨',
    processing: '처리 중',
    completed: '완료',
    failed: '실패',
    review_pending: '검토 대기',
  };
  return labels[status] || status;
}

export function getStatusColor(status: MeetingStatus): string {
  const colors: Record<MeetingStatus, string> = {
    uploaded: 'bg-gray-500',
    processing: 'bg-blue-500',
    completed: 'bg-green-500',
    failed: 'bg-red-500',
    review_pending: 'bg-yellow-500',
  };
  return colors[status] || 'bg-gray-500';
}

export type ActionItemPriority = 'low' | 'medium' | 'high' | 'urgent';

export function getPriorityLabel(priority: ActionItemPriority): string {
  const labels: Record<ActionItemPriority, string> = {
    low: '낮음', medium: '보통', high: '높음', urgent: '긴급',
  };
  return labels[priority] || priority;
}

export function getPriorityColor(priority: ActionItemPriority): string {
  const colors: Record<ActionItemPriority, string> = {
    low: 'text-gray-500 bg-gray-100',
    medium: 'text-blue-600 bg-blue-100',
    high: 'text-orange-600 bg-orange-100',
    urgent: 'text-red-600 bg-red-100',
  };
  return colors[priority] || 'text-gray-500 bg-gray-100';
}

export type ActionItemStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled';

export function getActionStatusLabel(status: ActionItemStatus): string {
  const labels: Record<ActionItemStatus, string> = {
    pending: '대기', in_progress: '진행 중', completed: '완료', cancelled: '취소',
  };
  return labels[status] || status;
}
