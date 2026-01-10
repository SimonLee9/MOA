'use client';

import { useState, useRef, useEffect } from 'react';
import { Download, FileText, FileCode, FileJson, Loader2 } from 'lucide-react';
import { exportApi, ExportFormat } from '@/lib/api';

interface ExportButtonProps {
  meetingId: string;
  meetingTitle?: string;
  disabled?: boolean;
}

const exportFormats: { format: ExportFormat; label: string; icon: React.ReactNode; description: string }[] = [
  {
    format: 'markdown',
    label: 'Markdown (.md)',
    icon: <FileText className="w-4 h-4" />,
    description: '문서 편집에 적합',
  },
  {
    format: 'html',
    label: 'HTML (.html)',
    icon: <FileCode className="w-4 h-4" />,
    description: 'PDF 변환/인쇄용',
  },
  {
    format: 'json',
    label: 'JSON (.json)',
    icon: <FileJson className="w-4 h-4" />,
    description: '데이터 백업/연동용',
  },
];

export default function ExportButton({ meetingId, meetingTitle, disabled }: ExportButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [exporting, setExporting] = useState<ExportFormat | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleExport = async (format: ExportFormat) => {
    setExporting(format);
    try {
      await exportApi.download(meetingId, format);
      setIsOpen(false);
    } catch (error) {
      console.error('Export failed:', error);
      alert('내보내기에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || exporting !== null}
        className="inline-flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {exporting ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Download className="w-4 h-4" />
        )}
        <span>내보내기</span>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
          <div className="p-2">
            <p className="px-3 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
              내보내기 형식 선택
            </p>
            {exportFormats.map(({ format, label, icon, description }) => (
              <button
                key={format}
                onClick={() => handleExport(format)}
                disabled={exporting !== null}
                className="w-full flex items-start gap-3 px-3 py-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 text-left"
              >
                <span className="mt-0.5 text-gray-600 dark:text-gray-400">
                  {exporting === format ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    icon
                  )}
                </span>
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {label}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {description}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
