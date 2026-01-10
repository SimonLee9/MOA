'use client';

import { useMemo } from 'react';
import type { DailyStats } from '@/lib/api';

interface DailyChartProps {
  data: DailyStats[];
  height?: number;
}

export default function DailyChart({ data, height = 200 }: DailyChartProps) {
  const chartData = useMemo(() => {
    if (!data.length) return { maxValue: 0, bars: [] };

    const maxValue = Math.max(
      ...data.map(d => Math.max(d.meetingsCreated, d.meetingsCompleted, d.meetingsFailed)),
      1
    );

    const bars = data.map(d => ({
      date: d.date,
      dayLabel: new Date(d.date).toLocaleDateString('ko-KR', { weekday: 'short' }),
      dateLabel: new Date(d.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
      created: d.meetingsCreated,
      completed: d.meetingsCompleted,
      failed: d.meetingsFailed,
      createdHeight: (d.meetingsCreated / maxValue) * 100,
      completedHeight: (d.meetingsCompleted / maxValue) * 100,
      failedHeight: (d.meetingsFailed / maxValue) * 100,
    }));

    return { maxValue, bars };
  }, [data]);

  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-400">
        데이터가 없습니다
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-blue-500" />
          <span>생성</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-green-500" />
          <span>완료</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-red-500" />
          <span>실패</span>
        </div>
      </div>

      <div className="flex items-end justify-between gap-2" style={{ height }}>
        {chartData.bars.map((bar) => (
          <div key={bar.date} className="flex-1 flex flex-col items-center gap-1">
            <div className="w-full flex items-end justify-center gap-1" style={{ height: height - 40 }}>
              <div
                className="w-3 bg-blue-500 rounded-t transition-all duration-300"
                style={{ height: `${bar.createdHeight}%`, minHeight: bar.created > 0 ? 4 : 0 }}
                title={`생성: ${bar.created}`}
              />
              <div
                className="w-3 bg-green-500 rounded-t transition-all duration-300"
                style={{ height: `${bar.completedHeight}%`, minHeight: bar.completed > 0 ? 4 : 0 }}
                title={`완료: ${bar.completed}`}
              />
              <div
                className="w-3 bg-red-500 rounded-t transition-all duration-300"
                style={{ height: `${bar.failedHeight}%`, minHeight: bar.failed > 0 ? 4 : 0 }}
                title={`실패: ${bar.failed}`}
              />
            </div>
            <div className="text-center">
              <p className="text-xs font-medium">{bar.dayLabel}</p>
              <p className="text-xs text-gray-400">{bar.dateLabel}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
