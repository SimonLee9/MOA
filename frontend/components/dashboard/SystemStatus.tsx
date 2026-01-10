'use client';

import { CheckCircle, AlertTriangle, XCircle, RefreshCw } from 'lucide-react';
import type { SystemHealth } from '@/lib/api';

interface SystemStatusProps {
  health: SystemHealth | null;
  loading?: boolean;
  onRefresh?: () => void;
}

const statusConfig = {
  healthy: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-100 dark:bg-green-900/20' },
  degraded: { icon: AlertTriangle, color: 'text-yellow-500', bg: 'bg-yellow-100 dark:bg-yellow-900/20' },
  unhealthy: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-100 dark:bg-red-900/20' },
};

function getServiceStatus(status: string): 'healthy' | 'degraded' | 'unhealthy' {
  if (status === 'healthy') return 'healthy';
  if (status.includes('unhealthy')) return 'unhealthy';
  return 'degraded';
}

export default function SystemStatus({ health, loading, onRefresh }: SystemStatusProps) {
  if (loading || !health) {
    return (
      <div className="space-y-3 animate-pulse">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="flex items-center gap-3 p-3 bg-gray-100 dark:bg-gray-800 rounded-lg">
            <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full" />
            <div className="flex-1 h-4 bg-gray-200 dark:bg-gray-700 rounded" />
          </div>
        ))}
      </div>
    );
  }

  const overallStatus = statusConfig[health.status];
  const OverallIcon = overallStatus.icon;

  const services = [
    { key: 'database', label: '데이터베이스', status: health.database },
    { key: 'redis', label: 'Redis 캐시', status: health.redis },
    { key: 'aiPipeline', label: 'AI 파이프라인', status: health.aiPipeline },
  ];

  return (
    <div className="space-y-4">
      {/* Overall Status */}
      <div className={`flex items-center justify-between p-4 rounded-lg ${overallStatus.bg}`}>
        <div className="flex items-center gap-3">
          <OverallIcon className={`w-6 h-6 ${overallStatus.color}`} />
          <div>
            <p className="font-medium">시스템 상태</p>
            <p className={`text-sm ${overallStatus.color}`}>
              {health.status === 'healthy' ? '정상' : health.status === 'degraded' ? '일부 문제' : '오류'}
            </p>
          </div>
        </div>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-2 hover:bg-white/50 dark:hover:bg-black/20 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Individual Services */}
      <div className="space-y-2">
        {services.map((service) => {
          const svcStatus = getServiceStatus(service.status);
          const config = statusConfig[svcStatus];
          const Icon = config.icon;

          return (
            <div
              key={service.key}
              className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-5 h-5 ${config.color}`} />
                <span>{service.label}</span>
              </div>
              <span className={`text-sm ${config.color}`}>
                {svcStatus === 'healthy' ? '정상' : service.status}
              </span>
            </div>
          );
        })}
      </div>

      {/* Last Updated */}
      <p className="text-xs text-gray-400 text-right">
        마지막 확인: {new Date(health.timestamp).toLocaleTimeString('ko-KR')}
      </p>
    </div>
  );
}
