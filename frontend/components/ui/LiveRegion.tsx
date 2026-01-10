'use client';

import { useEffect, useState } from 'react';

/**
 * Live Region Component
 * Announces dynamic content changes to screen readers
 * Use for status updates, form validation messages, etc.
 */

interface LiveRegionProps {
  message: string;
  politeness?: 'polite' | 'assertive' | 'off';
  clearAfter?: number; // ms to clear the message
  atomic?: boolean;
  relevant?: 'additions' | 'removals' | 'text' | 'all';
}

export default function LiveRegion({
  message,
  politeness = 'polite',
  clearAfter,
  atomic = true,
  relevant = 'additions',
}: LiveRegionProps) {
  const [currentMessage, setCurrentMessage] = useState(message);

  useEffect(() => {
    setCurrentMessage(message);

    if (clearAfter && message) {
      const timer = setTimeout(() => {
        setCurrentMessage('');
      }, clearAfter);
      return () => clearTimeout(timer);
    }
  }, [message, clearAfter]);

  return (
    <div
      role="status"
      aria-live={politeness}
      aria-atomic={atomic}
      aria-relevant={relevant}
      className="sr-only"
    >
      {currentMessage}
    </div>
  );
}

/**
 * Hook for managing live region announcements
 */
export function useLiveAnnouncer() {
  const [announcement, setAnnouncement] = useState('');

  const announce = (message: string, delay = 100) => {
    // Clear first to ensure the same message is announced again
    setAnnouncement('');
    setTimeout(() => {
      setAnnouncement(message);
    }, delay);
  };

  return { announcement, announce };
}
