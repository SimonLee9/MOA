import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'MOA - Minutes Of Action',
  description: '회의를 기록하지 않는다. 실행을 만든다.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className={`${inter.className} bg-gray-50 dark:bg-gray-950 min-h-screen`}>
        {children}
      </body>
    </html>
  );
}
