'use client';

/**
 * Skip Link Component
 * Provides a skip-to-main-content link for keyboard users
 * Improves accessibility by allowing users to skip repetitive navigation
 */

interface SkipLinkProps {
  href?: string;
  children?: React.ReactNode;
}

export default function SkipLink({ href = '#main-content', children = '본문으로 바로가기' }: SkipLinkProps) {
  return (
    <a
      href={href}
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
    >
      {children}
    </a>
  );
}
