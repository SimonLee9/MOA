'use client';

import { WifiOff, RefreshCw } from 'lucide-react';

export default function OfflinePage() {
  const handleRetry = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center p-4">
      <div className="text-center max-w-md">
        <div className="w-20 h-20 mx-auto mb-6 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center">
          <WifiOff className="w-10 h-10 text-gray-400" />
        </div>

        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
          오프라인 상태입니다
        </h1>

        <p className="text-gray-600 dark:text-gray-400 mb-6">
          인터넷 연결이 없습니다. 연결을 확인하고 다시 시도해주세요.
        </p>

        <button
          onClick={handleRetry}
          className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <RefreshCw className="w-5 h-5" />
          다시 시도
        </button>

        <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <p className="text-sm text-blue-700 dark:text-blue-300">
            MOA는 오프라인에서도 일부 기능을 사용할 수 있습니다.
            <br />
            이전에 본 회의 목록과 요약은 캐시되어 있을 수 있습니다.
          </p>
        </div>
      </div>
    </div>
  );
}
