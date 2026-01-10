'use client';

/**
 * Visually Hidden Component
 * Hides content visually but keeps it accessible to screen readers
 * Use for providing additional context to assistive technologies
 */

interface VisuallyHiddenProps {
  children: React.ReactNode;
  as?: 'span' | 'div' | 'label' | 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
}

export default function VisuallyHidden({ children, as: Component = 'span' }: VisuallyHiddenProps) {
  return (
    <Component className="sr-only">
      {children}
    </Component>
  );
}
