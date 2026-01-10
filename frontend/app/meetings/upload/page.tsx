'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Upload, ArrowLeft, FileAudio, X, Loader2, Mic } from 'lucide-react';
import { meetingsApi } from '@/lib/api';
import AudioRecorder from '@/components/meeting/AudioRecorder';

type InputMode = 'file' | 'record';

export default function UploadPage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [meetingDate, setMeetingDate] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [inputMode, setInputMode] = useState<InputMode>('file');
  const [recordedDuration, setRecordedDuration] = useState(0);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      const ext = f.name.split('.').pop()?.toLowerCase();
      if (!['m4a', 'mp3', 'wav', 'webm', 'ogg'].includes(ext || '')) {
        setError('지원하지 않는 파일 형식입니다.');
        return;
      }
      setFile(f);
      setError('');
      if (!title) setTitle(f.name.replace(/\.[^/.]+$/, ''));
    }
  };

  const handleRecordingComplete = (blob: Blob, duration: number) => {
    // Convert blob to File
    const timestamp = new Date().toISOString().slice(0, 10);
    const fileName = `recording_${timestamp}.webm`;
    const audioFile = new File([blob], fileName, { type: blob.type });
    setFile(audioFile);
    setRecordedDuration(duration);
    if (!title) setTitle(`녹음_${timestamp}`);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !title) return;

    setUploading(true);
    setError('');

    try {
      // 1. Create meeting
      const meeting = await meetingsApi.create({ title, meetingDate: meetingDate || undefined });
      
      // 2. Upload audio
      await meetingsApi.uploadAudio(meeting.id, file, setProgress);
      
      // 3. Start processing
      await meetingsApi.startProcessing(meeting.id);
      
      // 4. Redirect to meeting page
      router.push(`/meetings/${meeting.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || '업로드에 실패했습니다.');
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <header className="border-b bg-white dark:bg-gray-900">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center gap-4">
          <Link href="/meetings" className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <h1 className="text-xl font-semibold">새 회의 업로드</h1>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium mb-2">회의 제목 *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900 dark:border-gray-700"
              placeholder="예: 2025년 1분기 기획 회의"
              required
            />
          </div>

          {/* Date */}
          <div>
            <label className="block text-sm font-medium mb-2">회의 날짜</label>
            <input
              type="date"
              value={meetingDate}
              onChange={(e) => setMeetingDate(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900 dark:border-gray-700"
            />
          </div>

          {/* Input Mode Selection */}
          <div>
            <label className="block text-sm font-medium mb-2">오디오 입력 방식 *</label>
            <div className="flex gap-2 mb-4">
              <button
                type="button"
                onClick={() => { setInputMode('file'); setFile(null); }}
                className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg border-2 transition-colors ${
                  inputMode === 'file'
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                }`}
              >
                <Upload className="w-5 h-5" />
                파일 업로드
              </button>
              <button
                type="button"
                onClick={() => { setInputMode('record'); setFile(null); }}
                className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg border-2 transition-colors ${
                  inputMode === 'record'
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                }`}
              >
                <Mic className="w-5 h-5" />
                직접 녹음
              </button>
            </div>

            {/* File Upload Mode */}
            {inputMode === 'file' && (
              <>
                {!file ? (
                  <label className="block border-2 border-dashed rounded-xl p-8 text-center cursor-pointer hover:border-gray-400 dark:border-gray-700">
                    <input type="file" accept="audio/*" onChange={handleFileChange} className="hidden" />
                    <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                    <p className="text-gray-600 dark:text-gray-400">클릭하여 파일 선택</p>
                    <p className="text-sm text-gray-400 mt-1">m4a, mp3, wav, webm, ogg (최대 500MB)</p>
                  </label>
                ) : (
                  <div className="flex items-center gap-4 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
                    <FileAudio className="w-10 h-10 text-blue-600" />
                    <div className="flex-1">
                      <p className="font-medium truncate">{file.name}</p>
                      <p className="text-sm text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                    <button type="button" onClick={() => setFile(null)} className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg">
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                )}
              </>
            )}

            {/* Recording Mode */}
            {inputMode === 'record' && (
              <>
                {!file ? (
                  <AudioRecorder
                    onRecordingComplete={handleRecordingComplete}
                    maxDuration={3600}
                  />
                ) : (
                  <div className="flex items-center gap-4 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
                    <Mic className="w-10 h-10 text-red-600" />
                    <div className="flex-1">
                      <p className="font-medium truncate">{file.name}</p>
                      <p className="text-sm text-gray-500">
                        {Math.floor(recordedDuration / 60)}분 {recordedDuration % 60}초 녹음됨
                      </p>
                    </div>
                    <button type="button" onClick={() => setFile(null)} className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg">
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 rounded-lg">{error}</div>
          )}

          {/* Progress */}
          {uploading && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>업로드 중...</span>
                <span>{progress}%</span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-blue-600 transition-all" style={{ width: `${progress}%` }} />
              </div>
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={!file || !title || uploading}
            className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {uploading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                처리 중...
              </>
            ) : (
              <>
                <Upload className="w-5 h-5" />
                업로드 및 분석 시작
              </>
            )}
          </button>
        </form>
      </main>
    </div>
  );
}
