'use client';

import { useMemo } from 'react';
import type { WorkflowMetrics } from '@/lib/api';

interface StatusPieChartProps {
  metrics: WorkflowMetrics;
  size?: number;
}

const statusColors = [
  { key: 'completed', label: '완료', color: '#22c55e' },
  { key: 'processing', label: '처리 중', color: '#3b82f6' },
  { key: 'pendingReview', label: '검토 대기', color: '#eab308' },
  { key: 'failed', label: '실패', color: '#ef4444' },
];

export default function StatusPieChart({ metrics, size = 180 }: StatusPieChartProps) {
  const chartData = useMemo(() => {
    const total = metrics.totalMeetings || 1;
    const data = statusColors.map(({ key, label, color }) => {
      const value = metrics[key as keyof WorkflowMetrics] as number || 0;
      return {
        key,
        label,
        color,
        value,
        percentage: Math.round((value / total) * 100),
      };
    }).filter(d => d.value > 0);

    // Calculate SVG arcs
    let startAngle = -90;
    const arcs = data.map((d) => {
      const angle = (d.value / total) * 360;
      const endAngle = startAngle + angle;

      const startRad = (startAngle * Math.PI) / 180;
      const endRad = (endAngle * Math.PI) / 180;

      const radius = size / 2 - 10;
      const centerX = size / 2;
      const centerY = size / 2;

      const x1 = centerX + radius * Math.cos(startRad);
      const y1 = centerY + radius * Math.sin(startRad);
      const x2 = centerX + radius * Math.cos(endRad);
      const y2 = centerY + radius * Math.sin(endRad);

      const largeArcFlag = angle > 180 ? 1 : 0;

      const path = `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;

      startAngle = endAngle;

      return { ...d, path };
    });

    return arcs;
  }, [metrics, size]);

  if (metrics.totalMeetings === 0) {
    return (
      <div className="flex items-center justify-center" style={{ height: size }}>
        <p className="text-gray-400">데이터가 없습니다</p>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-6">
      <svg width={size} height={size} className="transform -rotate-0">
        {chartData.map((arc) => (
          <path
            key={arc.key}
            d={arc.path}
            fill={arc.color}
            className="transition-all duration-300 hover:opacity-80"
          />
        ))}
        {/* Center circle for donut effect */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={size / 4}
          fill="white"
          className="dark:fill-gray-900"
        />
        <text
          x={size / 2}
          y={size / 2}
          textAnchor="middle"
          dominantBaseline="middle"
          className="fill-current text-2xl font-bold"
        >
          {metrics.totalMeetings}
        </text>
      </svg>

      <div className="space-y-2">
        {chartData.map((d) => (
          <div key={d.key} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: d.color }}
            />
            <span className="text-sm">{d.label}</span>
            <span className="text-sm font-medium">{d.value}</span>
            <span className="text-xs text-gray-400">({d.percentage}%)</span>
          </div>
        ))}
      </div>
    </div>
  );
}
