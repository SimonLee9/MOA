'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { ArrowLeft, Link2, Check, X, RefreshCw, ExternalLink, MessageSquare, Calendar, FileText, ClipboardList } from 'lucide-react';
import { useI18n } from '@/lib/i18n';

interface Integration {
  name: string;
  enabled: boolean;
  configured: boolean;
  description: string;
  required_for: string[];
}

interface IntegrationIconProps {
  name: string;
  className?: string;
}

function IntegrationIcon({ name, className = "w-6 h-6" }: IntegrationIconProps) {
  switch (name.toLowerCase()) {
    case 'slack':
      return <MessageSquare className={className} />;
    case 'google calendar':
      return <Calendar className={className} />;
    case 'notion':
      return <FileText className={className} />;
    case 'jira':
      return <ClipboardList className={className} />;
    default:
      return <Link2 className={className} />;
  }
}

export default function IntegrationsPage() {
  const { t } = useI18n();
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [testingSlack, setTestingSlack] = useState(false);
  const [slackTestResult, setSlackTestResult] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const fetchIntegrations = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/integrations/details', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setIntegrations(data.integrations);
      }
    } catch (error) {
      console.error('Failed to fetch integrations:', error);
    } finally {
      setLoading(false);
    }
  };

  const testSlackIntegration = async () => {
    setTestingSlack(true);
    setSlackTestResult(null);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/integrations/slack/test', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: 'MOA 연동 테스트 메시지입니다.' }),
      });

      const data = await response.json();

      if (response.ok) {
        setSlackTestResult({ success: true, message: data.message });
      } else {
        setSlackTestResult({ success: false, message: data.detail || '테스트 실패' });
      }
    } catch (error) {
      setSlackTestResult({ success: false, message: '네트워크 오류가 발생했습니다.' });
    } finally {
      setTestingSlack(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="border-b bg-white dark:bg-gray-900 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Link href="/settings" className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <h1 className="text-xl font-semibold">외부 서비스 연동</h1>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-2xl mx-auto px-4 py-8 space-y-6">
        {/* Status Overview */}
        <section className="bg-white dark:bg-gray-900 rounded-xl border p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Link2 className="w-5 h-5" />
              연동 상태
            </h2>
            <button
              onClick={fetchIntegrations}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
              title="새로고침"
            >
              <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="animate-pulse flex items-center gap-4 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
                  <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-lg" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {integrations.map((integration) => (
                <IntegrationCard
                  key={integration.name}
                  integration={integration}
                  onTest={integration.name === 'Slack' ? testSlackIntegration : undefined}
                  testing={integration.name === 'Slack' && testingSlack}
                  testResult={integration.name === 'Slack' ? slackTestResult : null}
                />
              ))}
            </div>
          )}
        </section>

        {/* Setup Guide */}
        <section className="bg-white dark:bg-gray-900 rounded-xl border p-6">
          <h2 className="text-lg font-semibold mb-4">설정 가이드</h2>
          <div className="space-y-4 text-sm text-gray-600 dark:text-gray-400">
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <h3 className="font-medium text-blue-700 dark:text-blue-300 mb-2">Slack 연동</h3>
              <ol className="list-decimal list-inside space-y-1">
                <li>Slack 앱에서 Incoming Webhook을 생성합니다</li>
                <li>Webhook URL을 <code className="bg-blue-100 dark:bg-blue-900 px-1 rounded">SLACK_WEBHOOK_URL</code> 환경 변수에 설정합니다</li>
                <li>서버를 재시작합니다</li>
              </ol>
            </div>

            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <h3 className="font-medium text-green-700 dark:text-green-300 mb-2">Google Calendar 연동</h3>
              <ol className="list-decimal list-inside space-y-1">
                <li>Google Cloud Console에서 프로젝트를 생성합니다</li>
                <li>Calendar API를 활성화합니다</li>
                <li>OAuth 인증 정보를 다운로드하여 서버에 저장합니다</li>
                <li>경로를 <code className="bg-green-100 dark:bg-green-900 px-1 rounded">GOOGLE_CALENDAR_CREDENTIALS</code>에 설정합니다</li>
              </ol>
            </div>

            <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
              <h3 className="font-medium text-orange-700 dark:text-orange-300 mb-2">Notion 연동</h3>
              <ol className="list-decimal list-inside space-y-1">
                <li>Notion 개발자 포털에서 Integration을 생성합니다</li>
                <li>API 키를 <code className="bg-orange-100 dark:bg-orange-900 px-1 rounded">NOTION_API_KEY</code>에 설정합니다</li>
                <li>연동할 페이지에서 Integration을 허용합니다</li>
              </ol>
            </div>

            <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <h3 className="font-medium text-purple-700 dark:text-purple-300 mb-2">Jira 연동</h3>
              <ol className="list-decimal list-inside space-y-1">
                <li>Atlassian에서 API 토큰을 생성합니다</li>
                <li><code className="bg-purple-100 dark:bg-purple-900 px-1 rounded">JIRA_URL</code>, <code className="bg-purple-100 dark:bg-purple-900 px-1 rounded">JIRA_EMAIL</code>, <code className="bg-purple-100 dark:bg-purple-900 px-1 rounded">JIRA_API_TOKEN</code>을 설정합니다</li>
              </ol>
            </div>
          </div>
        </section>
      </main>

      {/* Bottom padding for mobile nav */}
      <div className="h-20 md:h-0" />
    </div>
  );
}

interface IntegrationCardProps {
  integration: Integration;
  onTest?: () => void;
  testing?: boolean;
  testResult?: { success: boolean; message: string } | null;
}

function IntegrationCard({ integration, onTest, testing, testResult }: IntegrationCardProps) {
  return (
    <div className={`p-4 rounded-lg border-2 transition-colors ${
      integration.enabled
        ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20'
        : 'border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800/50'
    }`}>
      <div className="flex items-start gap-4">
        <div className={`p-3 rounded-lg ${
          integration.enabled
            ? 'bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400'
            : 'bg-gray-200 dark:bg-gray-700 text-gray-500'
        }`}>
          <IntegrationIcon name={integration.name} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold">{integration.name}</h3>
            {integration.enabled ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300 rounded-full">
                <Check className="w-3 h-3" />
                연동됨
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 rounded-full">
                <X className="w-3 h-3" />
                미설정
              </span>
            )}
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            {integration.description}
          </p>
          {integration.required_for.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {integration.required_for.map((feature) => (
                <span
                  key={feature}
                  className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded"
                >
                  {feature}
                </span>
              ))}
            </div>
          )}
        </div>

        {onTest && integration.enabled && (
          <button
            onClick={onTest}
            disabled={testing}
            className="px-3 py-1.5 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {testing ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              '테스트'
            )}
          </button>
        )}
      </div>

      {testResult && (
        <div className={`mt-3 p-3 rounded-lg text-sm ${
          testResult.success
            ? 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300'
            : 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300'
        }`}>
          {testResult.success ? (
            <span className="flex items-center gap-2">
              <Check className="w-4 h-4" />
              {testResult.message}
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <X className="w-4 h-4" />
              {testResult.message}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
