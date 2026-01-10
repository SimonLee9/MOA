'use client';

import { Globe } from 'lucide-react';
import { useI18n, Locale } from '@/lib/i18n';

interface LanguageToggleProps {
  showLabel?: boolean;
  className?: string;
}

const languages: { code: Locale; label: string; nativeLabel: string }[] = [
  { code: 'ko', label: 'Korean', nativeLabel: '한국어' },
  { code: 'en', label: 'English', nativeLabel: 'English' },
];

export default function LanguageToggle({ showLabel = false, className = '' }: LanguageToggleProps) {
  const { locale, setLocale, t } = useI18n();

  const toggleLanguage = () => {
    setLocale(locale === 'ko' ? 'en' : 'ko');
  };

  const currentLanguage = languages.find(l => l.code === locale);

  return (
    <button
      onClick={toggleLanguage}
      className={`flex items-center gap-2 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors ${className}`}
      aria-label={`${t('settings.language')}: ${currentLanguage?.nativeLabel}`}
    >
      <Globe className="w-5 h-5" />
      {showLabel && (
        <span className="text-sm font-medium">
          {currentLanguage?.nativeLabel}
        </span>
      )}
    </button>
  );
}

interface LanguageSelectorProps {
  className?: string;
}

export function LanguageSelector({ className = '' }: LanguageSelectorProps) {
  const { locale, setLocale, t } = useI18n();

  return (
    <div className={`flex items-center gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg ${className}`}>
      {languages.map(lang => (
        <button
          key={lang.code}
          onClick={() => setLocale(lang.code)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            locale === lang.code
              ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
          }`}
          aria-label={`${t('settings.language')}: ${lang.nativeLabel}`}
          aria-pressed={locale === lang.code}
        >
          {lang.nativeLabel}
        </button>
      ))}
    </div>
  );
}
