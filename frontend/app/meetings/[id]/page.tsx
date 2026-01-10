'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, FileText, CheckSquare, MessageSquare, Loader2, RefreshCw, AlertTriangle, Activity } from 'lucide-react';
import { meetingsApi, reviewApi } from '@/lib/api';
import { formatDate, formatDuration, getStatusLabel, getStatusColor, getPriorityColor, getPriorityLabel } from '@/lib/utils';
import useProgress from '@/lib/useProgress';
import type { Meeting, ReviewStatus } from '@/types/meeting';
import ReviewPanel from '@/components/review/ReviewPanel';
import ProgressTracker from '@/components/meeting/ProgressTracker';

export default function MeetingDetailPage() {
  const params = useParams();
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'summary' | 'actions' | 'transcript' | 'review' | 'progress'>('summary');
  const [reviewStatus, setReviewStatus] = useState<ReviewStatus | null>(null);
  const [checkingReview, setCheckingReview] = useState(false);

  // WebSocket progress tracking
  const progressMeetingId = meeting?.status === 'processing' ? params.id as string : null;
  const {
    progress,
    message,
    updates,
    status: wsStatus,
  } = useProgress(progressMeetingId, {
    onComplete: () => loadMeeting(),
    onReviewPending: () => {
      loadMeeting();
      checkReviewStatus();
    },
  });

  useEffect(() => {
    loadMeeting();
  }, [params.id]);

  useEffect(() => {
    if (meeting && (meeting.status === 'review_pending' || meeting.status === 'processing')) {
      checkReviewStatus();
    }
  }, [meeting?.status]);

  const loadMeeting = async () => {
    try {
      const data = await meetingsApi.get(params.id as string);
      setMeeting(data);
    } catch (error) {
      console.error('Failed to load meeting:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkReviewStatus = async () => {
    try {
      setCheckingReview(true);
      const status = await reviewApi.getStatus(params.id as string);
      setReviewStatus(status);
      if (status.requiresReview) {
        setActiveTab('review');
      }
    } catch (error) {
      console.error('Failed to check review status:', error);
    } finally {
      setCheckingReview(false);
    }
  };

  const handleReviewComplete = async () => {
    await loadMeeting();
    setReviewStatus(null);
    setActiveTab('summary');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!meeting) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>회의를 찾을 수 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="border-b bg-white dark:bg-gray-900 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4 mb-4">
            <Link href="/meetings" className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="flex-1">
              <div className="flex items-center gap-3">
                <h1 className="text-xl font-semibold">{meeting.title}</h1>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium text-white ${getStatusColor(meeting.status)}`}>
                  {getStatusLabel(meeting.status)}
                </span>
              </div>
              <p className="text-sm text-gray-500">
                {meeting.meetingDate && formatDate(meeting.meetingDate)}
                {meeting.audioDuration && ` · ${formatDuration(meeting.audioDuration)}`}
              </p>
            </div>
            <button onClick={loadMeeting} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>

          {/* Tabs */}
          <div className="flex gap-1">
            {[
              { id: 'summary', label: '요약', icon: FileText },
              { id: 'actions', label: '액션 아이템', icon: CheckSquare },
              { id: 'transcript', label: '트랜스크립트', icon: MessageSquare },
              ...(meeting.status === 'processing' ? [{ id: 'progress', label: '진행 상황', icon: Activity, processing: true }] : []),
              ...(reviewStatus?.requiresReview ? [{ id: 'review', label: '검토', icon: AlertTriangle, highlight: true }] : []),
            ].map(({ id, label, icon: Icon, highlight, processing }: any) => (
              <button
                key={id}
                onClick={() => setActiveTab(id as any)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === id
                    ? highlight
                      ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
                      : processing
                        ? 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300'
                        : 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                    : highlight
                      ? 'bg-yellow-50 text-yellow-600 hover:bg-yellow-100 dark:bg-yellow-900/30 dark:text-yellow-400'
                      : processing
                        ? 'bg-purple-50 text-purple-600 hover:bg-purple-100 dark:bg-purple-900/30 dark:text-purple-400'
                        : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                <Icon className={`w-4 h-4 ${processing ? 'animate-pulse' : ''}`} />
                {label}
                {(highlight || processing) && (
                  <span className={`w-2 h-2 rounded-full animate-pulse ${highlight ? 'bg-yellow-500' : 'bg-purple-500'}`} />
                )}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        {meeting.status === 'processing' && activeTab !== 'progress' && (
          <div
            className="flex items-center gap-3 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg mb-6 cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900/30"
            onClick={() => setActiveTab('progress')}
          >
            <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
            <div className="flex-1">
              <p className="font-medium">AI가 회의 내용을 분석하고 있습니다...</p>
              {message && <p className="text-sm text-blue-600">{message}</p>}
            </div>
            <div className="flex items-center gap-2">
              <div className="w-24 h-2 bg-blue-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-600 transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <span className="text-sm font-medium text-blue-600">{progress}%</span>
            </div>
          </div>
        )}

        {activeTab === 'progress' && meeting.status === 'processing' && (
          <ProgressTracker
            progress={progress}
            message={message}
            updates={updates}
            status={wsStatus}
          />
        )}

        {activeTab === 'summary' && meeting.summary && (
          <div className="space-y-6">
            <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-600" />
                회의 요약
              </h2>
              <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{meeting.summary.summary}</p>
            </div>

            {meeting.summary.keyPoints?.length > 0 && (
              <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border">
                <h2 className="text-lg font-semibold mb-4">핵심 포인트</h2>
                <ul className="space-y-2">
                  {meeting.summary.keyPoints.map((point, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="w-6 h-6 rounded-full bg-yellow-100 text-yellow-800 text-sm flex items-center justify-center flex-shrink-0">
                        {i + 1}
                      </span>
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {meeting.summary.decisions?.length > 0 && (
              <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border">
                <h2 className="text-lg font-semibold mb-4">결정 사항</h2>
                <ul className="space-y-2">
                  {meeting.summary.decisions.map((decision, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <CheckSquare className="w-5 h-5 text-green-600 flex-shrink-0" />
                      <span>{decision}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {activeTab === 'actions' && (
          <div className="space-y-3">
            {meeting.actionItems && meeting.actionItems.length > 0 ? (
              meeting.actionItems.map((item) => (
                <div key={item.id} className="p-4 bg-white dark:bg-gray-900 rounded-xl border">
                  <div className="flex items-start gap-3">
                    <CheckSquare className={`w-5 h-5 flex-shrink-0 ${item.status === 'completed' ? 'text-green-600' : 'text-gray-400'}`} />
                    <div className="flex-1">
                      <p className={item.status === 'completed' ? 'line-through text-gray-400' : ''}>{item.content}</p>
                      <div className="flex items-center gap-3 mt-2 text-sm">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getPriorityColor(item.priority)}`}>
                          {getPriorityLabel(item.priority)}
                        </span>
                        {item.assignee && <span className="text-gray-500">담당: {item.assignee}</span>}
                        {item.dueDate && <span className="text-gray-500">마감: {formatDate(item.dueDate)}</span>}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-center text-gray-500 py-8">추출된 액션 아이템이 없습니다.</p>
            )}
          </div>
        )}

        {activeTab === 'transcript' && (
          <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border">
            {meeting.transcripts && meeting.transcripts.length > 0 ? (
              <div className="space-y-4">
                {meeting.transcripts.map((segment, i) => (
                  <div key={i} className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-800 flex items-center justify-center text-sm font-medium flex-shrink-0">
                      {segment.speaker.charAt(0)}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-blue-600">{segment.speaker}</p>
                      <p className="text-gray-700 dark:text-gray-300">{segment.text}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-gray-500">트랜스크립트가 없습니다.</p>
            )}
          </div>
        )}

        {activeTab === 'review' && reviewStatus?.requiresReview && (
          <ReviewPanel
            meetingId={params.id as string}
            onReviewComplete={handleReviewComplete}
          />
        )}

        {!meeting.summary && meeting.status !== 'processing' && activeTab !== 'review' && (
          <p className="text-center text-gray-500 py-8">아직 분석 결과가 없습니다.</p>
        )}
      </main>
    </div>
  );
}
