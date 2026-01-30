import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

// Mock the useTheme hook
const mockSetTheme = jest.fn();
const mockToggleTheme = jest.fn();

jest.mock('@/lib/useTheme', () => ({
  useTheme: () => ({
    theme: 'light',
    resolvedTheme: 'light',
    setTheme: mockSetTheme,
    toggleTheme: mockToggleTheme,
  }),
}));

// Import after mocking
import ThemeToggle from '@/components/ui/ThemeToggle';

describe('ThemeToggle', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Simple toggle mode (default)', () => {
    it('should render toggle button', () => {
      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('should have correct aria-label for light mode', () => {
      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label', '다크 모드로 전환');
    });

    it('should call toggleTheme when clicked', () => {
      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(mockToggleTheme).toHaveBeenCalledTimes(1);
    });

    it('should apply custom className', () => {
      render(<ThemeToggle className="custom-class" />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('custom-class');
    });
  });

  describe('System option mode', () => {
    it('should render three theme buttons when showSystemOption is true', () => {
      render(<ThemeToggle showSystemOption />);

      const buttons = screen.getAllByRole('button');
      expect(buttons).toHaveLength(3);
    });

    it('should have correct aria-labels for all buttons', () => {
      render(<ThemeToggle showSystemOption />);

      expect(screen.getByLabelText('라이트 모드로 전환')).toBeInTheDocument();
      expect(screen.getByLabelText('다크 모드로 전환')).toBeInTheDocument();
      expect(screen.getByLabelText('시스템 설정 따르기')).toBeInTheDocument();
    });

    it('should call setTheme with "light" when light button clicked', () => {
      render(<ThemeToggle showSystemOption />);

      const lightButton = screen.getByLabelText('라이트 모드로 전환');
      fireEvent.click(lightButton);

      expect(mockSetTheme).toHaveBeenCalledWith('light');
    });

    it('should call setTheme with "dark" when dark button clicked', () => {
      render(<ThemeToggle showSystemOption />);

      const darkButton = screen.getByLabelText('다크 모드로 전환');
      fireEvent.click(darkButton);

      expect(mockSetTheme).toHaveBeenCalledWith('dark');
    });

    it('should call setTheme with "system" when system button clicked', () => {
      render(<ThemeToggle showSystemOption />);

      const systemButton = screen.getByLabelText('시스템 설정 따르기');
      fireEvent.click(systemButton);

      expect(mockSetTheme).toHaveBeenCalledWith('system');
    });
  });
});
