'use client';

import { useState } from 'react';
import { Mic, Square, Pause, Play, Trash2, Upload, AlertCircle } from 'lucide-react';
import { useAudioRecorder, formatRecordingDuration } from '@/lib/useAudioRecorder';

interface AudioRecorderProps {
  onRecordingComplete: (blob: Blob, duration: number) => void;
  maxDuration?: number; // seconds
  className?: string;
}

export default function AudioRecorder({
  onRecordingComplete,
  maxDuration = 3600, // 1 hour default
  className = '',
}: AudioRecorderProps) {
  const {
    isRecording,
    isPaused,
    duration,
    audioBlob,
    audioUrl,
    error,
    volume,
    isSupported,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    clearRecording,
  } = useAudioRecorder({ maxDuration });

  const [isUploading, setIsUploading] = useState(false);

  if (!isSupported) {
    return (
      <div className={`p-6 bg-yellow-50 dark:bg-yellow-900/20 rounded-xl border border-yellow-200 dark:border-yellow-800 ${className}`}>
        <div className="flex items-center gap-3 text-yellow-700 dark:text-yellow-400">
          <AlertCircle className="w-5 h-5" />
          <p>이 브라우저는 오디오 녹음을 지원하지 않습니다.</p>
        </div>
      </div>
    );
  }

  const handleUpload = async () => {
    if (!audioBlob) return;
    setIsUploading(true);
    try {
      onRecordingComplete(audioBlob, duration);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className={`p-6 bg-white dark:bg-gray-900 rounded-xl border ${className}`}>
      {error && (
        <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
          <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Recording visualization */}
      {isRecording && (
        <div className="mb-6">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className={`w-3 h-3 rounded-full ${isPaused ? 'bg-yellow-500' : 'bg-red-500 animate-pulse'}`} />
            <span className="text-2xl font-mono font-bold">
              {formatRecordingDuration(duration)}
            </span>
            {maxDuration > 0 && (
              <span className="text-gray-400 text-sm">
                / {formatRecordingDuration(maxDuration)}
              </span>
            )}
          </div>

          {/* Volume meter */}
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 transition-all duration-100"
              style={{ width: `${volume}%` }}
            />
          </div>

          {/* Waveform visualization */}
          <div className="flex items-center justify-center gap-1 h-16 mt-4">
            {Array.from({ length: 30 }).map((_, i) => {
              const height = isPaused ? 4 : Math.max(4, Math.random() * volume * 0.6);
              return (
                <div
                  key={i}
                  className="w-1.5 bg-blue-500 rounded-full transition-all duration-100"
                  style={{ height: `${height}px` }}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* Audio preview */}
      {audioUrl && !isRecording && (
        <div className="mb-6">
          <p className="text-sm text-gray-500 mb-2">녹음된 오디오 ({formatRecordingDuration(duration)})</p>
          <audio
            src={audioUrl}
            controls
            className="w-full"
          />
        </div>
      )}

      {/* Controls */}
      <div className="flex items-center justify-center gap-4">
        {!isRecording && !audioBlob && (
          <button
            onClick={startRecording}
            className="flex items-center gap-2 px-6 py-3 bg-red-600 text-white rounded-full hover:bg-red-700 transition-colors"
          >
            <Mic className="w-5 h-5" />
            녹음 시작
          </button>
        )}

        {isRecording && (
          <>
            {isPaused ? (
              <button
                onClick={resumeRecording}
                className="p-4 bg-green-600 text-white rounded-full hover:bg-green-700 transition-colors"
                aria-label="녹음 계속"
              >
                <Play className="w-6 h-6" />
              </button>
            ) : (
              <button
                onClick={pauseRecording}
                className="p-4 bg-yellow-600 text-white rounded-full hover:bg-yellow-700 transition-colors"
                aria-label="녹음 일시정지"
              >
                <Pause className="w-6 h-6" />
              </button>
            )}
            <button
              onClick={stopRecording}
              className="p-4 bg-gray-600 text-white rounded-full hover:bg-gray-700 transition-colors"
              aria-label="녹음 중지"
            >
              <Square className="w-6 h-6" />
            </button>
          </>
        )}

        {audioBlob && !isRecording && (
          <>
            <button
              onClick={clearRecording}
              className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              <Trash2 className="w-5 h-5" />
              다시 녹음
            </button>
            <button
              onClick={handleUpload}
              disabled={isUploading}
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              <Upload className="w-5 h-5" />
              {isUploading ? '업로드 중...' : '이 녹음 사용'}
            </button>
          </>
        )}
      </div>

      {/* Recording tips */}
      {!isRecording && !audioBlob && (
        <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <h4 className="font-medium mb-2">녹음 팁</h4>
          <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
            <li>• 조용한 환경에서 녹음하세요</li>
            <li>• 마이크와 적절한 거리를 유지하세요</li>
            <li>• 최대 녹음 시간: {formatRecordingDuration(maxDuration)}</li>
          </ul>
        </div>
      )}
    </div>
  );
}
