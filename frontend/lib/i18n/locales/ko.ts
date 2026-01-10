/**
 * Korean translations
 */

const ko = {
  // Common
  'common.loading': '로딩 중...',
  'common.error': '오류가 발생했습니다',
  'common.retry': '다시 시도',
  'common.cancel': '취소',
  'common.save': '저장',
  'common.delete': '삭제',
  'common.edit': '편집',
  'common.confirm': '확인',
  'common.close': '닫기',
  'common.search': '검색',
  'common.filter': '필터',
  'common.clear': '지우기',
  'common.all': '전체',
  'common.none': '없음',
  'common.yes': '예',
  'common.no': '아니오',

  // Navigation
  'nav.home': '홈',
  'nav.meetings': '회의',
  'nav.dashboard': '대시보드',
  'nav.notifications': '알림',
  'nav.settings': '설정',
  'nav.logout': '로그아웃',
  'nav.skipToMain': '본문으로 바로가기',

  // Auth
  'auth.login': '로그인',
  'auth.register': '회원가입',
  'auth.email': '이메일',
  'auth.password': '비밀번호',
  'auth.name': '이름',
  'auth.forgotPassword': '비밀번호 찾기',
  'auth.loginSuccess': '로그인되었습니다',
  'auth.logoutSuccess': '로그아웃되었습니다',

  // Meetings
  'meetings.title': '회의 목록',
  'meetings.new': '새 회의',
  'meetings.upload': '회의 업로드',
  'meetings.noMeetings': '아직 회의가 없습니다',
  'meetings.noMeetingsDesc': '첫 번째 회의를 업로드해보세요.',
  'meetings.total': '총 {{count}}개의 회의',
  'meetings.processing': 'AI가 회의 내용을 분석하고 있습니다...',
  'meetings.searchPlaceholder': '회의 제목으로 검색...',

  // Meeting Status
  'status.uploaded': '업로드됨',
  'status.processing': '처리 중',
  'status.completed': '완료',
  'status.failed': '실패',
  'status.reviewPending': '검토 대기',

  // Meeting Detail
  'meeting.summary': '요약',
  'meeting.keyPoints': '핵심 포인트',
  'meeting.decisions': '결정 사항',
  'meeting.actionItems': '액션 아이템',
  'meeting.transcript': '트랜스크립트',
  'meeting.review': '검토',
  'meeting.progress': '진행 상황',
  'meeting.noSummary': '아직 분석 결과가 없습니다.',
  'meeting.noTranscript': '트랜스크립트가 없습니다.',

  // Action Items
  'action.add': '액션 아이템 추가',
  'action.content': '내용',
  'action.assignee': '담당자',
  'action.dueDate': '마감일',
  'action.priority': '우선순위',
  'action.status': '상태',
  'action.pending': '대기',
  'action.inProgress': '진행 중',
  'action.completed': '완료',
  'action.low': '낮음',
  'action.medium': '보통',
  'action.high': '높음',
  'action.urgent': '긴급',

  // Review
  'review.title': '회의 검토',
  'review.approve': '승인',
  'review.reject': '거부',
  'review.requestChanges': '수정 요청',
  'review.feedback': '피드백',
  'review.feedbackPlaceholder': '수정이 필요한 부분을 설명해주세요...',

  // Export
  'export.title': '내보내기',
  'export.markdown': 'Markdown (.md)',
  'export.markdownDesc': '문서 편집에 적합',
  'export.html': 'HTML (.html)',
  'export.htmlDesc': 'PDF 변환/인쇄용',
  'export.json': 'JSON (.json)',
  'export.jsonDesc': '데이터 백업/연동용',
  'export.selectFormat': '내보내기 형식 선택',

  // Notifications
  'notifications.title': '알림',
  'notifications.empty': '알림이 없습니다',
  'notifications.markAllRead': '모두 읽음',
  'notifications.viewAll': '모든 알림 보기',
  'notifications.unread': '{{count}}개의 읽지 않은 알림',
  'notifications.reviewPending': '검토 필요',
  'notifications.processingComplete': '처리 완료',
  'notifications.processingFailed': '처리 실패',
  'notifications.actionDueSoon': '마감 임박',
  'notifications.actionOverdue': '마감 초과',
  'notifications.system': '시스템',

  // Dashboard
  'dashboard.title': '대시보드',
  'dashboard.totalMeetings': '총 회의',
  'dashboard.processing': '처리 중',
  'dashboard.completed': '완료',
  'dashboard.pendingReview': '검토 대기',
  'dashboard.successRate': '성공률',
  'dashboard.avgProcessingTime': '평균 처리 시간',
  'dashboard.recentActivity': '최근 활동',
  'dashboard.systemStatus': '시스템 상태',
  'dashboard.dailyStats': '일별 현황',

  // Tags
  'tags.add': '태그 추가',
  'tags.noTags': '태그 없음',
  'tags.placeholder': '태그 입력...',

  // Settings
  'settings.title': '설정',
  'settings.theme': '테마',
  'settings.themeLight': '라이트',
  'settings.themeDark': '다크',
  'settings.themeSystem': '시스템',
  'settings.language': '언어',
  'settings.languageKo': '한국어',
  'settings.languageEn': 'English',

  // Errors
  'error.notFound': '페이지를 찾을 수 없습니다',
  'error.unauthorized': '로그인이 필요합니다',
  'error.forbidden': '접근 권한이 없습니다',
  'error.serverError': '서버 오류가 발생했습니다',
  'error.networkError': '네트워크 오류가 발생했습니다',
  'error.uploadFailed': '업로드에 실패했습니다',
  'error.exportFailed': '내보내기에 실패했습니다',

  // Time
  'time.justNow': '방금 전',
  'time.minutesAgo': '{{count}}분 전',
  'time.hoursAgo': '{{count}}시간 전',
  'time.daysAgo': '{{count}}일 전',
  'time.minutes': '{{count}}분',
  'time.hours': '{{count}}시간',
  'time.seconds': '{{count}}초',
} as const;

export default ko;
