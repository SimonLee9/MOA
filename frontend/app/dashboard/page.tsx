'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  LayoutDashboard, FileText, Clock, CheckCircle,
  AlertTriangle, TrendingUp, Plus, ArrowRight
} from 'lucide-react';
import { metricsApi, meetingsApi } from '@/lib/api';
import type { WorkflowMetrics, DailyStats, SystemHealth } from '@/lib/api';
import type { Meeting } from '@/types/meeting';
import StatsCard from '@/components/dashboard/StatsCard';
import DailyChart from '@/components/dashboard/DailyChart';
import StatusPieChart from '@/components/dashboard/StatusPieChart';
import RecentActivity from '@/components/dashboard/RecentActivity';
import SystemStatus from '@/components/dashboard/SystemStatus';

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<WorkflowMetrics | null>(null);
  const [dailyStats, setDailyStats] = useState<DailyStats[]>([]);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [recentMeetings, setRecentMeetings] = useState<Meeting[]>([]);
  const [pendingReviewMeetings, setPendingReviewMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [workflowData, dailyData, healthData, recentData, pendingData] = await Promise.all([
        metricsApi.getWorkflows(),
        metricsApi.getDaily(7),
        metricsApi.getHealth().catch(() => null),
        meetingsApi.search({ sortBy: 'created_at', sortOrder: 'desc', size: 5 }),
        meetingsApi.search({ status: 'review_pending', sortBy: 'created_at', sortOrder: 'desc', size: 5 }),
      ]);

      setMetrics(workflowData);
      setDailyStats(dailyData);
      setHealth(healthData);
      setRecentMeetings(recentData.items);
      setPendingReviewMeetings(pendingData.items);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatProcessingTime = (seconds: number | null): string => {
    if (!seconds) return '-';
    if (seconds < 60) return `${Math.round(seconds)}초`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}분`;
    return `${Math.round(seconds / 3600)}시간`;
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="border-b bg-white dark:bg-gray-900 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="text-2xl font-bold text-blue-600">MOA</Link>
            <span className="text-gray-300">/</span>
            <div className="flex items-center gap-2">
              <LayoutDashboard className="w-5 h-5 text-gray-500" />
              <span className="font-medium">대시보드</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/meetings"
              className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
            >
              회의 목록
            </Link>
            <Link
              href="/meetings/upload"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              새 회의
            </Link>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatsCard
            title="총 회의"
            value={metrics?.totalMeetings ?? '-'}
            icon={FileText}
            color="blue"
          />
          <StatsCard
            title="처리 중"
            value={metrics?.processing ?? '-'}
            icon={Clock}
            color="yellow"
          />
          <StatsCard
            title="검토 대기"
            value={metrics?.pendingReview ?? '-'}
            icon={AlertTriangle}
            color="purple"
          />
          <StatsCard
            title="성공률"
            value={metrics ? `${metrics.successRate}%` : '-'}
            subtitle={formatProcessingTime(metrics?.avgProcessingTimeSeconds ?? null)}
            icon={TrendingUp}
            color="green"
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Daily Activity Chart */}
          <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">일별 활동</h2>
              <span className="text-sm text-gray-500">최근 7일</span>
            </div>
            <DailyChart data={dailyStats} height={200} />
          </div>

          {/* Status Distribution */}
          <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border">
            <h2 className="text-lg font-semibold mb-4">상태 분포</h2>
            {metrics && <StatusPieChart metrics={metrics} size={180} />}
          </div>
        </div>

        {/* Activity and Status Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Activity */}
          <div className="lg:col-span-2 p-6 bg-white dark:bg-gray-900 rounded-xl border">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">최근 회의</h2>
              <Link
                href="/meetings"
                className="text-sm text-blue-600 hover:underline flex items-center gap-1"
              >
                전체 보기
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <RecentActivity meetings={recentMeetings} loading={loading} />
          </div>

          {/* System Status */}
          <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border">
            <h2 className="text-lg font-semibold mb-4">시스템 상태</h2>
            <SystemStatus
              health={health}
              loading={loading}
              onRefresh={loadDashboardData}
            />
          </div>
        </div>

        {/* Pending Review Section */}
        {pendingReviewMeetings.length > 0 && (
          <div className="mt-8 p-6 bg-yellow-50 dark:bg-yellow-900/20 rounded-xl border border-yellow-200 dark:border-yellow-800">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-yellow-600" />
                <h2 className="text-lg font-semibold text-yellow-800 dark:text-yellow-200">
                  검토 대기 중인 회의
                </h2>
              </div>
              <Link
                href="/meetings?status=review_pending"
                className="text-sm text-yellow-700 hover:underline flex items-center gap-1"
              >
                전체 보기
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {pendingReviewMeetings.map((meeting) => (
                <Link key={meeting.id} href={`/meetings/${meeting.id}`}>
                  <div className="p-3 bg-white dark:bg-gray-900 rounded-lg hover:shadow-md transition-shadow cursor-pointer">
                    <p className="font-medium truncate">{meeting.title}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(meeting.createdAt).toLocaleDateString('ko-KR')}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
