'use client';

import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import ko from './locales/ko';
import en from './locales/en';

export type Locale = 'ko' | 'en';
export type TranslationKey = keyof typeof ko;

const translations = { ko, en } as const;

const LOCALE_STORAGE_KEY = 'moa-locale';

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}

export const I18nContext = createContext<I18nContextType | undefined>(undefined);

export function useI18n() {
  const context = useContext(I18nContext);
  if (context === undefined) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
}

/**
 * Get stored locale preference
 */
function getStoredLocale(): Locale {
  if (typeof window === 'undefined') return 'ko';
  const stored = localStorage.getItem(LOCALE_STORAGE_KEY);
  if (stored === 'ko' || stored === 'en') {
    return stored;
  }
  // Detect browser language
  const browserLang = navigator.language.split('-')[0];
  return browserLang === 'en' ? 'en' : 'ko';
}

/**
 * Hook for initializing i18n
 */
export function useI18nInit() {
  const [locale, setLocaleState] = useState<Locale>('ko');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const stored = getStoredLocale();
    setLocaleState(stored);
    setMounted(true);
    // Update html lang attribute
    document.documentElement.lang = stored;
  }, []);

  const setLocale = useCallback((newLocale: Locale) => {
    setLocaleState(newLocale);
    localStorage.setItem(LOCALE_STORAGE_KEY, newLocale);
    document.documentElement.lang = newLocale;
  }, []);

  const t = useCallback((key: TranslationKey, params?: Record<string, string | number>): string => {
    let text = translations[locale][key] || translations['ko'][key] || key;

    if (params) {
      Object.entries(params).forEach(([paramKey, value]) => {
        text = text.replace(new RegExp(`{{${paramKey}}}`, 'g'), String(value));
      });
    }

    return text;
  }, [locale]);

  return { locale, setLocale, t, mounted };
}

export { translations };
