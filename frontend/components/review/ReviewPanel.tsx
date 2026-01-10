'use client';

import { useState, useEffect } from 'react';
import {
  AlertCircle,
  CheckCircle,
  Edit2,
  Save,
  X,
  ThumbsUp,
  ThumbsDown,
  Loader2,
  Plus,
  Trash2,
} from 'lucide-react';
import { reviewApi } from '@/lib/api';
import { formatDate, getPriorityColor, getPriorityLabel } from '@/lib/utils';
import type { ReviewData, ActionItemReview, ActionItemPriority } from '@/types/meeting';

interface ReviewPanelProps {
  meetingId: string;
  onReviewComplete: () => void;
}

export default function ReviewPanel({ meetingId, onReviewComplete }: ReviewPanelProps) {
  const [reviewData, setReviewData] = useState<ReviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Editable states
  const [editingSummary, setEditingSummary] = useState(false);
  const [summary, setSummary] = useState('');
  const [keyPoints, setKeyPoints] = useState<string[]>([]);
  const [decisions, setDecisions] = useState<string[]>([]);
  const [actions, setActions] = useState<ActionItemReview[]>([]);
  const [feedback, setFeedback] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);

  useEffect(() => {
    loadReviewData();
  }, [meetingId]);

  const loadReviewData = async () => {
    try {
      setLoading(true);
      const status = await reviewApi.getStatus(meetingId);
      if (status.requiresReview && status.reviewData) {
        setReviewData(status.reviewData);
        setSummary(status.reviewData.minutes);
        setKeyPoints([...status.reviewData.keyPoints]);
        setDecisions([...status.reviewData.decisions]);
        setActions(status.reviewData.proposedActions.map(a => ({ ...a })));
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '리뷰 데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    setSubmitting(true);
    setError('');
    try {
      await reviewApi.submit(meetingId, {
        action: 'approve',
        updatedSummary: summary,
        updatedKeyPoints: keyPoints,
        updatedDecisions: decisions,
        updatedActions: actions,
      });
      onReviewComplete();
    } catch (err: any) {
      setError(err.response?.data?.detail || '승인에 실패했습니다.');
      setSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!feedback.trim()) {
      setError('수정 요청 사유를 입력해주세요.');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      await reviewApi.submit(meetingId, {
        action: 'reject',
        feedback,
      });
      setShowRejectModal(false);
      onReviewComplete();
    } catch (err: any) {
      setError(err.response?.data?.detail || '수정 요청에 실패했습니다.');
      setSubmitting(false);
    }
  };

  // Key Points management
  const addKeyPoint = () => setKeyPoints([...keyPoints, '']);
  const updateKeyPoint = (index: number, value: string) => {
    const updated = [...keyPoints];
    updated[index] = value;
    setKeyPoints(updated);
  };
  const removeKeyPoint = (index: number) => {
    setKeyPoints(keyPoints.filter((_, i) => i !== index));
  };

  // Decisions management
  const addDecision = () => setDecisions([...decisions, '']);
  const updateDecision = (index: number, value: string) => {
    const updated = [...decisions];
    updated[index] = value;
    setDecisions(updated);
  };
  const removeDecision = (index: number) => {
    setDecisions(decisions.filter((_, i) => i !== index));
  };

  // Actions management
  const updateAction = (index: number, field: keyof ActionItemReview, value: any) => {
    const updated = [...actions];
    updated[index] = { ...updated[index], [field]: value };
    setActions(updated);
  };
  const removeAction = (index: number) => {
    setActions(actions.filter((_, i) => i !== index));
  };
  const addAction = () => {
    setActions([
      ...actions,
      {
        id: `new-${Date.now()}`,
        content: '',
        priority: 'medium' as ActionItemPriority,
      },
    ]);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-2">리뷰 데이터 불러오는 중...</span>
      </div>
    );
  }

  if (!reviewData) {
    return (
      <div className="p-6 bg-gray-100 dark:bg-gray-800 rounded-xl text-center">
        <AlertCircle className="w-12 h-12 mx-auto text-gray-400 mb-4" />
        <p className="text-gray-600 dark:text-gray-400">현재 리뷰가 필요한 내용이 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Review Header */}
      <div className="flex items-center gap-3 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-xl border border-yellow-200 dark:border-yellow-800">
        <AlertCircle className="w-6 h-6 text-yellow-600 flex-shrink-0" />
        <div>
          <h2 className="font-semibold text-yellow-800 dark:text-yellow-200">검토가 필요합니다</h2>
          <p className="text-sm text-yellow-700 dark:text-yellow-300">
            AI가 생성한 회의 요약을 검토하고 수정 후 승인해주세요.
            {reviewData.retryCount > 0 && ` (수정 요청: ${reviewData.retryCount}회)`}
          </p>
        </div>
      </div>

      {/* AI Critique (if any) */}
      {reviewData.critique && (
        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
          <h3 className="font-medium text-blue-800 dark:text-blue-200 mb-2">AI 자체 평가</h3>
          <p className="text-sm text-blue-700 dark:text-blue-300">{reviewData.critique}</p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 rounded-xl flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      {/* Summary Section */}
      <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">회의 요약</h3>
          <button
            onClick={() => setEditingSummary(!editingSummary)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
          >
            {editingSummary ? <X className="w-5 h-5" /> : <Edit2 className="w-5 h-5" />}
          </button>
        </div>
        {editingSummary ? (
          <textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            className="w-full h-40 p-3 border rounded-lg resize-none dark:bg-gray-800 dark:border-gray-700"
            placeholder="회의 요약을 입력하세요..."
          />
        ) : (
          <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{summary}</p>
        )}
      </div>

      {/* Key Points Section */}
      <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">핵심 포인트</h3>
          <button
            onClick={addKeyPoint}
            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300 rounded-lg hover:bg-blue-200"
          >
            <Plus className="w-4 h-4" />
            추가
          </button>
        </div>
        <ul className="space-y-2">
          {keyPoints.map((point, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="w-6 h-6 rounded-full bg-yellow-100 text-yellow-800 text-sm flex items-center justify-center flex-shrink-0 mt-1">
                {i + 1}
              </span>
              <input
                type="text"
                value={point}
                onChange={(e) => updateKeyPoint(i, e.target.value)}
                className="flex-1 px-3 py-1.5 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                placeholder="핵심 포인트..."
              />
              <button
                onClick={() => removeKeyPoint(i)}
                className="p-1.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg text-red-600"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </li>
          ))}
        </ul>
      </div>

      {/* Decisions Section */}
      <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">결정 사항</h3>
          <button
            onClick={addDecision}
            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300 rounded-lg hover:bg-green-200"
          >
            <Plus className="w-4 h-4" />
            추가
          </button>
        </div>
        <ul className="space-y-2">
          {decisions.map((decision, i) => (
            <li key={i} className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-1.5" />
              <input
                type="text"
                value={decision}
                onChange={(e) => updateDecision(i, e.target.value)}
                className="flex-1 px-3 py-1.5 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                placeholder="결정 사항..."
              />
              <button
                onClick={() => removeDecision(i)}
                className="p-1.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg text-red-600"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </li>
          ))}
        </ul>
        {decisions.length === 0 && (
          <p className="text-gray-500 text-sm">결정 사항이 없습니다.</p>
        )}
      </div>

      {/* Action Items Section */}
      <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">액션 아이템</h3>
          <button
            onClick={addAction}
            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300 rounded-lg hover:bg-purple-200"
          >
            <Plus className="w-4 h-4" />
            추가
          </button>
        </div>
        <div className="space-y-4">
          {actions.map((action, i) => (
            <div key={action.id} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex items-start gap-2 mb-3">
                <input
                  type="text"
                  value={action.content}
                  onChange={(e) => updateAction(i, 'content', e.target.value)}
                  className="flex-1 px-3 py-1.5 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  placeholder="할 일 내용..."
                />
                <button
                  onClick={() => removeAction(i)}
                  className="p-1.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg text-red-600"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">담당자</label>
                  <input
                    type="text"
                    value={action.assignee || ''}
                    onChange={(e) => updateAction(i, 'assignee', e.target.value)}
                    className="w-full px-2 py-1 text-sm border rounded dark:bg-gray-700 dark:border-gray-600"
                    placeholder="미정"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">마감일</label>
                  <input
                    type="date"
                    value={action.dueDate || ''}
                    onChange={(e) => updateAction(i, 'dueDate', e.target.value)}
                    className="w-full px-2 py-1 text-sm border rounded dark:bg-gray-700 dark:border-gray-600"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">우선순위</label>
                  <select
                    value={action.priority}
                    onChange={(e) => updateAction(i, 'priority', e.target.value)}
                    className="w-full px-2 py-1 text-sm border rounded dark:bg-gray-700 dark:border-gray-600"
                  >
                    <option value="low">낮음</option>
                    <option value="medium">보통</option>
                    <option value="high">높음</option>
                    <option value="urgent">긴급</option>
                  </select>
                </div>
              </div>
            </div>
          ))}
        </div>
        {actions.length === 0 && (
          <p className="text-gray-500 text-sm">액션 아이템이 없습니다.</p>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-4 p-4 bg-gray-100 dark:bg-gray-800 rounded-xl">
        <button
          onClick={handleApprove}
          disabled={submitting}
          className="flex-1 flex items-center justify-center gap-2 py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50"
        >
          {submitting ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <ThumbsUp className="w-5 h-5" />
          )}
          승인
        </button>
        <button
          onClick={() => setShowRejectModal(true)}
          disabled={submitting}
          className="flex-1 flex items-center justify-center gap-2 py-3 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 disabled:opacity-50"
        >
          <ThumbsDown className="w-5 h-5" />
          수정 요청
        </button>
      </div>

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-900 rounded-xl p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">수정 요청</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              AI에게 어떤 부분을 수정해야 하는지 피드백을 입력해주세요.
            </p>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              className="w-full h-32 p-3 border rounded-lg resize-none dark:bg-gray-800 dark:border-gray-700 mb-4"
              placeholder="예: 요약이 너무 짧습니다. 더 자세하게 작성해주세요. / 액션 아이템의 담당자가 잘못되었습니다."
            />
            <div className="flex gap-3">
              <button
                onClick={() => setShowRejectModal(false)}
                className="flex-1 py-2 border rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                취소
              </button>
              <button
                onClick={handleReject}
                disabled={submitting || !feedback.trim()}
                className="flex-1 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {submitting ? '처리 중...' : '수정 요청'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
