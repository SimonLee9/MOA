'use client';

import { ReactNode } from 'react';
import ThemeProvider from './ThemeProvider';
import I18nProvider from './I18nProvider';

interface ProvidersProps {
  children: ReactNode;
}

export default function Providers({ children }: ProvidersProps) {
  return (
    <ThemeProvider>
      <I18nProvider>
        {children}
      </I18nProvider>
    </ThemeProvider>
  );
}
