'use client';

import { useCallback, useEffect, useRef } from 'react';

/**
 * Custom hook for keyboard navigation in lists
 * Implements arrow key navigation and selection patterns
 */

interface UseKeyboardNavigationOptions<T> {
  items: T[];
  onSelect?: (item: T, index: number) => void;
  onEscape?: () => void;
  enabled?: boolean;
  loop?: boolean; // Loop around at the ends
  orientation?: 'vertical' | 'horizontal' | 'both';
  initialIndex?: number;
}

export function useKeyboardNavigation<T>({
  items,
  onSelect,
  onEscape,
  enabled = true,
  loop = true,
  orientation = 'vertical',
  initialIndex = -1,
}: UseKeyboardNavigationOptions<T>) {
  const activeIndex = useRef(initialIndex);
  const containerRef = useRef<HTMLElement | null>(null);

  const setActiveIndex = useCallback((index: number) => {
    activeIndex.current = index;

    // Focus the element at the new index
    if (containerRef.current) {
      const focusableElements = containerRef.current.querySelectorAll<HTMLElement>(
        '[data-keyboard-item]'
      );
      if (focusableElements[index]) {
        focusableElements[index].focus();
      }
    }
  }, []);

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!enabled || items.length === 0) return;

    const isVertical = orientation === 'vertical' || orientation === 'both';
    const isHorizontal = orientation === 'horizontal' || orientation === 'both';

    let newIndex = activeIndex.current;
    let handled = false;

    switch (event.key) {
      case 'ArrowDown':
        if (isVertical) {
          event.preventDefault();
          handled = true;
          if (newIndex < items.length - 1) {
            newIndex++;
          } else if (loop) {
            newIndex = 0;
          }
        }
        break;

      case 'ArrowUp':
        if (isVertical) {
          event.preventDefault();
          handled = true;
          if (newIndex > 0) {
            newIndex--;
          } else if (loop) {
            newIndex = items.length - 1;
          }
        }
        break;

      case 'ArrowRight':
        if (isHorizontal) {
          event.preventDefault();
          handled = true;
          if (newIndex < items.length - 1) {
            newIndex++;
          } else if (loop) {
            newIndex = 0;
          }
        }
        break;

      case 'ArrowLeft':
        if (isHorizontal) {
          event.preventDefault();
          handled = true;
          if (newIndex > 0) {
            newIndex--;
          } else if (loop) {
            newIndex = items.length - 1;
          }
        }
        break;

      case 'Home':
        event.preventDefault();
        handled = true;
        newIndex = 0;
        break;

      case 'End':
        event.preventDefault();
        handled = true;
        newIndex = items.length - 1;
        break;

      case 'Enter':
      case ' ':
        if (activeIndex.current >= 0 && onSelect) {
          event.preventDefault();
          handled = true;
          onSelect(items[activeIndex.current], activeIndex.current);
        }
        break;

      case 'Escape':
        if (onEscape) {
          event.preventDefault();
          handled = true;
          onEscape();
        }
        break;
    }

    if (handled && newIndex !== activeIndex.current && newIndex >= 0) {
      setActiveIndex(newIndex);
    }
  }, [enabled, items, orientation, loop, onSelect, onEscape, setActiveIndex]);

  const getContainerProps = useCallback(() => ({
    ref: (node: HTMLElement | null) => {
      containerRef.current = node;
    },
    onKeyDown: handleKeyDown as unknown as React.KeyboardEventHandler,
    role: 'listbox',
    'aria-activedescendant': activeIndex.current >= 0
      ? `keyboard-item-${activeIndex.current}`
      : undefined,
  }), [handleKeyDown]);

  const getItemProps = useCallback((index: number) => ({
    'data-keyboard-item': true,
    id: `keyboard-item-${index}`,
    tabIndex: activeIndex.current === index ? 0 : -1,
    role: 'option',
    'aria-selected': activeIndex.current === index,
    onFocus: () => {
      activeIndex.current = index;
    },
  }), []);

  return {
    activeIndex: activeIndex.current,
    setActiveIndex,
    getContainerProps,
    getItemProps,
  };
}

/**
 * Hook for managing focus within a form
 * Provides Enter key to submit and Tab navigation
 */
export function useFormKeyboardNavigation(onSubmit?: () => void) {
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      // Don't submit if focus is on a textarea
      if (event.target instanceof HTMLTextAreaElement) return;
      // Don't submit if focus is on a button
      if (event.target instanceof HTMLButtonElement) return;

      event.preventDefault();
      onSubmit?.();
    }
  }, [onSubmit]);

  return { handleKeyDown };
}

/**
 * Hook for roving tabindex pattern
 * Only one item in a group is focusable at a time
 */
export function useRovingTabIndex(itemCount: number, initialIndex = 0) {
  const currentIndex = useRef(initialIndex);

  const getTabIndex = useCallback((index: number) => {
    return currentIndex.current === index ? 0 : -1;
  }, []);

  const setFocusIndex = useCallback((index: number) => {
    currentIndex.current = Math.max(0, Math.min(index, itemCount - 1));
  }, [itemCount]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent, index: number) => {
    let newIndex = index;

    switch (event.key) {
      case 'ArrowRight':
      case 'ArrowDown':
        event.preventDefault();
        newIndex = index < itemCount - 1 ? index + 1 : 0;
        break;
      case 'ArrowLeft':
      case 'ArrowUp':
        event.preventDefault();
        newIndex = index > 0 ? index - 1 : itemCount - 1;
        break;
      case 'Home':
        event.preventDefault();
        newIndex = 0;
        break;
      case 'End':
        event.preventDefault();
        newIndex = itemCount - 1;
        break;
      default:
        return;
    }

    setFocusIndex(newIndex);
    // Focus the new element - caller needs to handle this
    return newIndex;
  }, [itemCount, setFocusIndex]);

  return {
    currentIndex: currentIndex.current,
    getTabIndex,
    setFocusIndex,
    handleKeyDown,
  };
}
