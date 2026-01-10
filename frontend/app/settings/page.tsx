'use client';

import Link from 'next/link';
import { ArrowLeft, Sun, Moon, Monitor, Globe, Smartphone, Bell, Shield, Info, Link2, ChevronRight } from 'lucide-react';
import { useTheme } from '@/lib/useTheme';
import { useI18n } from '@/lib/i18n';
import { LanguageSelector } from '@/components/ui/LanguageToggle';

export default function SettingsPage() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const { locale, setLocale, t } = useI18n();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="border-b bg-white dark:bg-gray-900 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Link href="/meetings" className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <h1 className="text-xl font-semibold">{t('settings.title')}</h1>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-2xl mx-auto px-4 py-8 space-y-6">
        {/* Theme Settings */}
        <section className="bg-white dark:bg-gray-900 rounded-xl border p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            {resolvedTheme === 'dark' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            {t('settings.theme')}
          </h2>
          <div className="space-y-3">
            <ThemeOption
              icon={<Sun className="w-5 h-5" />}
              label={t('settings.themeLight')}
              description="밝은 배경의 라이트 모드"
              selected={theme === 'light'}
              onClick={() => setTheme('light')}
            />
            <ThemeOption
              icon={<Moon className="w-5 h-5" />}
              label={t('settings.themeDark')}
              description="어두운 배경의 다크 모드"
              selected={theme === 'dark'}
              onClick={() => setTheme('dark')}
            />
            <ThemeOption
              icon={<Monitor className="w-5 h-5" />}
              label={t('settings.themeSystem')}
              description="운영체제 설정을 따릅니다"
              selected={theme === 'system'}
              onClick={() => setTheme('system')}
            />
          </div>
        </section>

        {/* Language Settings */}
        <section className="bg-white dark:bg-gray-900 rounded-xl border p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Globe className="w-5 h-5" />
            {t('settings.language')}
          </h2>
          <div className="space-y-3">
            <LanguageOption
              label={t('settings.languageKo')}
              nativeLabel="한국어"
              selected={locale === 'ko'}
              onClick={() => setLocale('ko')}
            />
            <LanguageOption
              label={t('settings.languageEn')}
              nativeLabel="English"
              selected={locale === 'en'}
              onClick={() => setLocale('en')}
            />
          </div>
        </section>

        {/* External Integrations */}
        <section className="bg-white dark:bg-gray-900 rounded-xl border p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Link2 className="w-5 h-5" />
            외부 서비스 연동
          </h2>
          <Link
            href="/settings/integrations"
            className="flex items-center justify-between p-4 rounded-lg border hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            <div>
              <p className="font-medium">연동 설정 관리</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Slack, Google Calendar, Notion, Jira 연동
              </p>
            </div>
            <ChevronRight className="w-5 h-5 text-gray-400" />
          </Link>
        </section>

        {/* Notification Settings */}
        <section className="bg-white dark:bg-gray-900 rounded-xl border p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Bell className="w-5 h-5" />
            알림 설정
          </h2>
          <div className="space-y-4">
            <ToggleSetting
              label="리뷰 요청 알림"
              description="회의 검토가 필요할 때 알림을 받습니다"
              defaultChecked={true}
            />
            <ToggleSetting
              label="처리 완료 알림"
              description="회의 처리가 완료되면 알림을 받습니다"
              defaultChecked={true}
            />
            <ToggleSetting
              label="액션 아이템 마감 알림"
              description="액션 아이템 마감일이 다가오면 알림을 받습니다"
              defaultChecked={false}
            />
          </div>
        </section>

        {/* Accessibility */}
        <section className="bg-white dark:bg-gray-900 rounded-xl border p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Smartphone className="w-5 h-5" />
            접근성
          </h2>
          <div className="space-y-4">
            <ToggleSetting
              label="키보드 네비게이션 힌트"
              description="키보드 단축키 힌트를 표시합니다"
              defaultChecked={false}
            />
            <ToggleSetting
              label="애니메이션 줄이기"
              description="움직임 효과를 최소화합니다"
              defaultChecked={false}
            />
          </div>
        </section>

        {/* App Info */}
        <section className="bg-white dark:bg-gray-900 rounded-xl border p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Info className="w-5 h-5" />
            앱 정보
          </h2>
          <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
            <div className="flex justify-between">
              <span>버전</span>
              <span>2.1.0</span>
            </div>
            <div className="flex justify-between">
              <span>빌드</span>
              <span>{process.env.NODE_ENV}</span>
            </div>
          </div>
        </section>
      </main>

      {/* Bottom padding for mobile nav */}
      <div className="h-20 md:h-0" />
    </div>
  );
}

interface ThemeOptionProps {
  icon: React.ReactNode;
  label: string;
  description: string;
  selected: boolean;
  onClick: () => void;
}

function ThemeOption({ icon, label, description, selected, onClick }: ThemeOptionProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-4 p-4 rounded-lg border-2 transition-colors ${
        selected
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
      }`}
      role="radio"
      aria-checked={selected}
    >
      <div className={`p-2 rounded-lg ${selected ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-600' : 'bg-gray-100 dark:bg-gray-800'}`}>
        {icon}
      </div>
      <div className="flex-1 text-left">
        <p className="font-medium">{label}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
      </div>
      {selected && (
        <div className="w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center">
          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </div>
      )}
    </button>
  );
}

interface LanguageOptionProps {
  label: string;
  nativeLabel: string;
  selected: boolean;
  onClick: () => void;
}

function LanguageOption({ label, nativeLabel, selected, onClick }: LanguageOptionProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center justify-between p-4 rounded-lg border-2 transition-colors ${
        selected
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
      }`}
      role="radio"
      aria-checked={selected}
    >
      <div className="text-left">
        <p className="font-medium">{nativeLabel}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
      </div>
      {selected && (
        <div className="w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center">
          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </div>
      )}
    </button>
  );
}

interface ToggleSettingProps {
  label: string;
  description: string;
  defaultChecked?: boolean;
}

function ToggleSetting({ label, description, defaultChecked = false }: ToggleSettingProps) {
  return (
    <label className="flex items-center justify-between cursor-pointer">
      <div>
        <p className="font-medium">{label}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
      </div>
      <input
        type="checkbox"
        defaultChecked={defaultChecked}
        className="sr-only peer"
      />
      <div className="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
    </label>
  );
}
