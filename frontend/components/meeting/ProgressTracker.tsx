'use client';

import { Loader2, Check, AlertCircle, FileAudio, FileText, ListTodo, Shield, UserCheck } from 'lucide-react';
import type { ProgressUpdate } from '@/lib/useProgress';

interface ProgressTrackerProps {
  progress: number;
  message: string;
  updates: ProgressUpdate[];
  status: string;
}

interface Step {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  minProgress: number;
}

const STEPS: Step[] = [
  { id: 'stt', label: '음성 인식', icon: FileAudio, minProgress: 5 },
  { id: 'summarize', label: '요약 생성', icon: FileText, minProgress: 45 },
  { id: 'actions', label: '액션 추출', icon: ListTodo, minProgress: 65 },
  { id: 'critique', label: '품질 검증', icon: Shield, minProgress: 80 },
  { id: 'review', label: '검토 대기', icon: UserCheck, minProgress: 95 },
];

export default function ProgressTracker({
  progress,
  message,
  updates,
  status,
}: ProgressTrackerProps) {
  const getCurrentStep = () => {
    for (let i = STEPS.length - 1; i >= 0; i--) {
      if (progress >= STEPS[i].minProgress) {
        return i;
      }
    }
    return -1;
  };

  const currentStepIndex = getCurrentStep();
  const isError = status === 'error';
  const isComplete = status === 'completed' || progress === 100;

  return (
    <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border">
      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            처리 진행률
          </span>
          <span className="text-sm font-medium text-blue-600">
            {progress}%
          </span>
        </div>
        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              isError
                ? 'bg-red-500'
                : isComplete
                  ? 'bg-green-500'
                  : 'bg-blue-600'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Current Status Message */}
      <div className={`flex items-center gap-3 p-4 rounded-lg mb-6 ${
        isError
          ? 'bg-red-50 dark:bg-red-900/20'
          : isComplete
            ? 'bg-green-50 dark:bg-green-900/20'
            : 'bg-blue-50 dark:bg-blue-900/20'
      }`}>
        {isError ? (
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
        ) : isComplete ? (
          <Check className="w-5 h-5 text-green-600 flex-shrink-0" />
        ) : (
          <Loader2 className="w-5 h-5 text-blue-600 animate-spin flex-shrink-0" />
        )}
        <span className={
          isError
            ? 'text-red-700 dark:text-red-300'
            : isComplete
              ? 'text-green-700 dark:text-green-300'
              : 'text-blue-700 dark:text-blue-300'
        }>
          {message || '처리를 준비하고 있습니다...'}
        </span>
      </div>

      {/* Step Indicators */}
      <div className="space-y-3">
        {STEPS.map((step, index) => {
          const Icon = step.icon;
          const isActive = index === currentStepIndex && !isComplete && !isError;
          const isCompleted = index < currentStepIndex || isComplete;
          const isPending = index > currentStepIndex;

          return (
            <div
              key={step.id}
              className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
                  : isCompleted
                    ? 'bg-gray-50 dark:bg-gray-800'
                    : ''
              }`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                isCompleted
                  ? 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400'
                  : isActive
                    ? 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400'
                    : 'bg-gray-100 text-gray-400 dark:bg-gray-700'
              }`}>
                {isCompleted ? (
                  <Check className="w-4 h-4" />
                ) : isActive ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Icon className="w-4 h-4" />
                )}
              </div>
              <span className={`font-medium ${
                isCompleted
                  ? 'text-green-700 dark:text-green-400'
                  : isActive
                    ? 'text-blue-700 dark:text-blue-400'
                    : 'text-gray-400'
              }`}>
                {step.label}
              </span>
              {isActive && (
                <span className="ml-auto text-xs text-blue-600 dark:text-blue-400">
                  진행 중
                </span>
              )}
              {isCompleted && (
                <span className="ml-auto text-xs text-green-600 dark:text-green-400">
                  완료
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Recent Updates (collapsible) */}
      {updates.length > 0 && (
        <details className="mt-6">
          <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
            최근 업데이트 보기 ({updates.length})
          </summary>
          <div className="mt-3 max-h-40 overflow-y-auto space-y-1">
            {updates.slice(-10).reverse().map((update, i) => (
              <div
                key={i}
                className="text-xs text-gray-500 dark:text-gray-400 p-2 bg-gray-50 dark:bg-gray-800 rounded"
              >
                <span className="font-mono text-gray-400">[{update.type}]</span>{' '}
                {update.message}
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
