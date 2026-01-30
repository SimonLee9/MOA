import {
  cn,
  formatDuration,
  formatTimestamp,
  getStatusLabel,
  getStatusColor,
  getPriorityLabel,
  getPriorityColor,
  getActionStatusLabel,
  getActionStatusColor,
} from '@/lib/utils';

describe('Utility Functions', () => {
  describe('cn (className merger)', () => {
    it('should merge simple class names', () => {
      expect(cn('foo', 'bar')).toBe('foo bar');
    });

    it('should handle conditional classes', () => {
      expect(cn('base', true && 'included', false && 'excluded')).toBe('base included');
    });

    it('should merge Tailwind classes correctly', () => {
      expect(cn('p-4', 'p-2')).toBe('p-2'); // Later class wins
      expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500');
    });

    it('should handle arrays', () => {
      expect(cn(['foo', 'bar'], 'baz')).toBe('foo bar baz');
    });

    it('should handle undefined and null', () => {
      expect(cn('foo', undefined, null, 'bar')).toBe('foo bar');
    });
  });

  describe('formatDuration', () => {
    it('should format minutes only', () => {
      expect(formatDuration(300)).toBe('5분');
      expect(formatDuration(1800)).toBe('30분');
    });

    it('should format hours and minutes', () => {
      expect(formatDuration(3600)).toBe('1시간 0분');
      expect(formatDuration(5400)).toBe('1시간 30분');
      expect(formatDuration(7200)).toBe('2시간 0분');
    });

    it('should handle zero', () => {
      expect(formatDuration(0)).toBe('0분');
    });
  });

  describe('formatTimestamp', () => {
    it('should format seconds to mm:ss', () => {
      expect(formatTimestamp(0)).toBe('00:00');
      expect(formatTimestamp(65)).toBe('01:05');
      expect(formatTimestamp(3661)).toBe('61:01');
    });

    it('should handle decimal seconds', () => {
      expect(formatTimestamp(65.5)).toBe('01:05');
    });
  });

  describe('getStatusLabel', () => {
    it('should return correct Korean labels', () => {
      expect(getStatusLabel('uploaded')).toBe('업로드됨');
      expect(getStatusLabel('processing')).toBe('처리 중');
      expect(getStatusLabel('completed')).toBe('완료');
      expect(getStatusLabel('failed')).toBe('실패');
      expect(getStatusLabel('review_pending')).toBe('검토 대기');
    });

    it('should return original value for unknown status', () => {
      expect(getStatusLabel('unknown' as any)).toBe('unknown');
    });
  });

  describe('getStatusColor', () => {
    it('should return correct color classes', () => {
      expect(getStatusColor('uploaded')).toBe('bg-gray-500');
      expect(getStatusColor('processing')).toBe('bg-blue-500');
      expect(getStatusColor('completed')).toBe('bg-green-500');
      expect(getStatusColor('failed')).toBe('bg-red-500');
      expect(getStatusColor('review_pending')).toBe('bg-yellow-500');
    });

    it('should return default color for unknown status', () => {
      expect(getStatusColor('unknown' as any)).toBe('bg-gray-500');
    });
  });

  describe('getPriorityLabel', () => {
    it('should return correct Korean labels', () => {
      expect(getPriorityLabel('low')).toBe('낮음');
      expect(getPriorityLabel('medium')).toBe('보통');
      expect(getPriorityLabel('high')).toBe('높음');
      expect(getPriorityLabel('urgent')).toBe('긴급');
    });

    it('should return original value for unknown priority', () => {
      expect(getPriorityLabel('unknown' as any)).toBe('unknown');
    });
  });

  describe('getPriorityColor', () => {
    it('should return correct color classes', () => {
      expect(getPriorityColor('low')).toBe('text-gray-500 bg-gray-100');
      expect(getPriorityColor('medium')).toBe('text-blue-600 bg-blue-100');
      expect(getPriorityColor('high')).toBe('text-orange-600 bg-orange-100');
      expect(getPriorityColor('urgent')).toBe('text-red-600 bg-red-100');
    });

    it('should return default color for unknown priority', () => {
      expect(getPriorityColor('unknown' as any)).toBe('text-gray-500 bg-gray-100');
    });
  });

  describe('getActionStatusLabel', () => {
    it('should return correct Korean labels', () => {
      expect(getActionStatusLabel('pending')).toBe('대기');
      expect(getActionStatusLabel('in_progress')).toBe('진행 중');
      expect(getActionStatusLabel('completed')).toBe('완료');
      expect(getActionStatusLabel('cancelled')).toBe('취소');
    });

    it('should return original value for unknown status', () => {
      expect(getActionStatusLabel('unknown' as any)).toBe('unknown');
    });
  });

  describe('getActionStatusColor', () => {
    it('should return correct color classes', () => {
      expect(getActionStatusColor('pending')).toBe('text-gray-600 bg-gray-100');
      expect(getActionStatusColor('in_progress')).toBe('text-blue-600 bg-blue-100');
      expect(getActionStatusColor('completed')).toBe('text-green-600 bg-green-100');
      expect(getActionStatusColor('cancelled')).toBe('text-gray-400 bg-gray-50');
    });

    it('should return default color for unknown status', () => {
      expect(getActionStatusColor('unknown' as any)).toBe('text-gray-600 bg-gray-100');
    });
  });
});
