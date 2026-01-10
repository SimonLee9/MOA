'use client';

import { useState } from 'react';
import { Search, Filter, X, ChevronDown, ArrowUpDown } from 'lucide-react';
import type { MeetingStatus, MeetingSearchParams } from '@/types/meeting';

interface MeetingFiltersProps {
  onSearch: (params: MeetingSearchParams) => void;
  isLoading?: boolean;
}

const STATUS_OPTIONS: { value: MeetingStatus | ''; label: string }[] = [
  { value: '', label: '전체 상태' },
  { value: 'uploaded', label: '업로드됨' },
  { value: 'processing', label: '처리 중' },
  { value: 'review_pending', label: '검토 대기' },
  { value: 'completed', label: '완료' },
  { value: 'failed', label: '실패' },
];

const SORT_OPTIONS: { value: MeetingSearchParams['sortBy']; label: string }[] = [
  { value: 'created_at', label: '생성일' },
  { value: 'meeting_date', label: '회의일' },
  { value: 'title', label: '제목' },
];

export default function MeetingFilters({ onSearch, isLoading }: MeetingFiltersProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [status, setStatus] = useState<MeetingStatus | ''>('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [sortBy, setSortBy] = useState<MeetingSearchParams['sortBy']>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [showFilters, setShowFilters] = useState(false);

  const hasActiveFilters = status || dateFrom || dateTo;

  const handleSearch = () => {
    const params: MeetingSearchParams = {
      page: 1,
      size: 20,
      sortBy,
      sortOrder,
    };
    if (searchQuery) params.q = searchQuery;
    if (status) params.status = status;
    if (dateFrom) params.dateFrom = dateFrom;
    if (dateTo) params.dateTo = dateTo;
    onSearch(params);
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setStatus('');
    setDateFrom('');
    setDateTo('');
    setSortBy('created_at');
    setSortOrder('desc');
    onSearch({ page: 1, size: 20 });
  };

  const toggleSortOrder = () => {
    const newOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    setSortOrder(newOrder);
    const params: MeetingSearchParams = {
      page: 1,
      size: 20,
      sortBy,
      sortOrder: newOrder,
    };
    if (searchQuery) params.q = searchQuery;
    if (status) params.status = status;
    if (dateFrom) params.dateFrom = dateFrom;
    if (dateTo) params.dateTo = dateTo;
    onSearch(params);
  };

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="회의 제목으로 검색..."
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-700"
          />
        </div>
        <button
          onClick={handleSearch}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          검색
        </button>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`px-4 py-2 border rounded-lg flex items-center gap-2 ${
            hasActiveFilters
              ? 'border-blue-500 text-blue-600 bg-blue-50 dark:bg-blue-900/20'
              : 'hover:bg-gray-50 dark:hover:bg-gray-800'
          }`}
        >
          <Filter className="w-5 h-5" />
          필터
          {hasActiveFilters && (
            <span className="bg-blue-500 text-white text-xs px-1.5 py-0.5 rounded-full">
              {[status, dateFrom, dateTo].filter(Boolean).length}
            </span>
          )}
          <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
        </button>
      </div>

      {/* Expanded Filters */}
      {showFilters && (
        <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                상태
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as MeetingStatus | '')}
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
              >
                {STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Date From */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                시작일
              </label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
              />
            </div>

            {/* Date To */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                종료일
              </label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
              />
            </div>

            {/* Sort By */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                정렬
              </label>
              <div className="flex gap-2">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as MeetingSearchParams['sortBy'])}
                  className="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                >
                  {SORT_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                <button
                  onClick={toggleSortOrder}
                  className="px-3 py-2 border rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                  title={sortOrder === 'asc' ? '오름차순' : '내림차순'}
                >
                  <ArrowUpDown className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          <div className="flex justify-between items-center pt-2 border-t">
            <button
              onClick={handleClearFilters}
              className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
            >
              <X className="w-4 h-4" />
              필터 초기화
            </button>
            <button
              onClick={handleSearch}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              적용
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
