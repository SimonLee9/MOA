'use client';

import Link from 'next/link';
import { FileText, AlertTriangle, CheckCircle, Loader2, XCircle } from 'lucide-react';
import { formatRelativeTime, getStatusLabel, getStatusColor } from '@/lib/utils';
import type { Meeting } from '@/types/meeting';

interface RecentActivityProps {
  meetings: Meeting[];
  loading?: boolean;
}

const statusIcons = {
  uploaded: FileText,
  processing: Loader2,
  review_pending: AlertTriangle,
  completed: CheckCircle,
  failed: XCircle,
};

export default function RecentActivity({ meetings, loading }: RecentActivityProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg animate-pulse">
            <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-full" />
            <div className="flex-1">
              <div className="h-4 w-1/3 bg-gray-200 dark:bg-gray-700 rounded mb-2" />
              <div className="h-3 w-1/4 bg-gray-200 dark:bg-gray-700 rounded" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!meetings.length) {
    return (
      <div className="text-center py-8 text-gray-400">
        <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>최근 활동이 없습니다</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {meetings.map((meeting) => {
        const StatusIcon = statusIcons[meeting.status] || FileText;
        const isProcessing = meeting.status === 'processing';

        return (
          <Link key={meeting.id} href={`/meetings/${meeting.id}`}>
            <div className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer">
              <div className={`p-2 rounded-full ${getStatusColor(meeting.status)} bg-opacity-20`}>
                <StatusIcon
                  className={`w-5 h-5 ${isProcessing ? 'animate-spin' : ''}`}
                />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{meeting.title}</p>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <span className={`px-1.5 py-0.5 rounded text-xs ${getStatusColor(meeting.status)} text-white`}>
                    {getStatusLabel(meeting.status)}
                  </span>
                  <span>{formatRelativeTime(meeting.updatedAt || meeting.createdAt)}</span>
                </div>
              </div>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
