import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Providers from '@/components/providers/Providers';
import SkipLink from '@/components/ui/SkipLink';
import ServiceWorkerRegister from '@/components/ServiceWorkerRegister';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'MOA - Minutes Of Action',
  description: '회의를 기록하지 않는다. 실행을 만든다.',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'MOA',
  },
  formatDetection: {
    telephone: false,
  },
  openGraph: {
    title: 'MOA - Minutes Of Action',
    description: '회의를 기록하지 않는다. 실행을 만든다.',
    type: 'website',
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#111827' },
  ],
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <head>
        <link rel="apple-touch-icon" href="/icons/icon-192x192.png" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
      </head>
      <body className={`${inter.className} bg-gray-50 dark:bg-gray-950 min-h-screen`}>
        <Providers>
          <SkipLink />
          <main id="main-content">
            {children}
          </main>
        </Providers>
        <ServiceWorkerRegister />
      </body>
    </html>
  );
}
