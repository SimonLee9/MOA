'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Plus, FileAudio, Calendar, Clock, ChevronRight } from 'lucide-react';
import { meetingsApi } from '@/lib/api';
import { formatDate, formatDuration, formatRelativeTime, getStatusLabel, getStatusColor } from '@/lib/utils';
import type { Meeting } from '@/types/meeting';

export default function MeetingsPage() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMeetings();
  }, []);

  const loadMeetings = async () => {
    try {
      const data = await meetingsApi.list();
      setMeetings(data.items);
    } catch (error) {
      console.error('Failed to load meetings:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="border-b bg-white dark:bg-gray-900 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="text-2xl font-bold text-blue-600">MOA</Link>
          <Link
            href="/meetings/upload"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-5 h-5" />
            새 회의
          </Link>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">회의 목록</h1>

        {loading ? (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="p-6 bg-white dark:bg-gray-900 rounded-xl border animate-pulse">
                <div className="h-6 w-1/3 bg-gray-200 dark:bg-gray-700 rounded mb-4" />
                <div className="h-4 w-1/2 bg-gray-200 dark:bg-gray-700 rounded" />
              </div>
            ))}
          </div>
        ) : meetings.length === 0 ? (
          <div className="text-center py-16">
            <FileAudio className="w-16 h-16 mx-auto text-gray-300 mb-4" />
            <h2 className="text-xl font-semibold mb-2">아직 회의가 없습니다</h2>
            <p className="text-gray-500 mb-6">첫 번째 회의를 업로드해보세요.</p>
            <Link
              href="/meetings/upload"
              className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg"
            >
              <Plus className="w-5 h-5" />
              회의 업로드
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {meetings.map((meeting) => (
              <Link key={meeting.id} href={`/meetings/${meeting.id}`}>
                <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border hover:shadow-md transition-shadow cursor-pointer">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold">{meeting.title}</h3>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium text-white ${getStatusColor(meeting.status)}`}>
                          {getStatusLabel(meeting.status)}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        {meeting.meetingDate && (
                          <span className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {formatDate(meeting.meetingDate)}
                          </span>
                        )}
                        {meeting.audioDuration && (
                          <span className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            {formatDuration(meeting.audioDuration)}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-400 mt-2">{formatRelativeTime(meeting.createdAt)}</p>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
