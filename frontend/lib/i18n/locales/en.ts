/**
 * English translations
 */

const en = {
  // Common
  'common.loading': 'Loading...',
  'common.error': 'An error occurred',
  'common.retry': 'Retry',
  'common.cancel': 'Cancel',
  'common.save': 'Save',
  'common.delete': 'Delete',
  'common.edit': 'Edit',
  'common.confirm': 'Confirm',
  'common.close': 'Close',
  'common.search': 'Search',
  'common.filter': 'Filter',
  'common.clear': 'Clear',
  'common.all': 'All',
  'common.none': 'None',
  'common.yes': 'Yes',
  'common.no': 'No',

  // Navigation
  'nav.home': 'Home',
  'nav.meetings': 'Meetings',
  'nav.dashboard': 'Dashboard',
  'nav.notifications': 'Notifications',
  'nav.settings': 'Settings',
  'nav.logout': 'Logout',
  'nav.skipToMain': 'Skip to main content',

  // Auth
  'auth.login': 'Login',
  'auth.register': 'Register',
  'auth.email': 'Email',
  'auth.password': 'Password',
  'auth.name': 'Name',
  'auth.forgotPassword': 'Forgot Password',
  'auth.loginSuccess': 'Successfully logged in',
  'auth.logoutSuccess': 'Successfully logged out',

  // Meetings
  'meetings.title': 'Meetings',
  'meetings.new': 'New Meeting',
  'meetings.upload': 'Upload Meeting',
  'meetings.noMeetings': 'No meetings yet',
  'meetings.noMeetingsDesc': 'Upload your first meeting to get started.',
  'meetings.total': '{{count}} meetings total',
  'meetings.processing': 'AI is analyzing the meeting...',
  'meetings.searchPlaceholder': 'Search meetings by title...',

  // Meeting Status
  'status.uploaded': 'Uploaded',
  'status.processing': 'Processing',
  'status.completed': 'Completed',
  'status.failed': 'Failed',
  'status.reviewPending': 'Review Pending',

  // Meeting Detail
  'meeting.summary': 'Summary',
  'meeting.keyPoints': 'Key Points',
  'meeting.decisions': 'Decisions',
  'meeting.actionItems': 'Action Items',
  'meeting.transcript': 'Transcript',
  'meeting.review': 'Review',
  'meeting.progress': 'Progress',
  'meeting.noSummary': 'No analysis results yet.',
  'meeting.noTranscript': 'No transcript available.',

  // Action Items
  'action.add': 'Add Action Item',
  'action.content': 'Content',
  'action.assignee': 'Assignee',
  'action.dueDate': 'Due Date',
  'action.priority': 'Priority',
  'action.status': 'Status',
  'action.pending': 'Pending',
  'action.inProgress': 'In Progress',
  'action.completed': 'Completed',
  'action.low': 'Low',
  'action.medium': 'Medium',
  'action.high': 'High',
  'action.urgent': 'Urgent',

  // Review
  'review.title': 'Review Meeting',
  'review.approve': 'Approve',
  'review.reject': 'Reject',
  'review.requestChanges': 'Request Changes',
  'review.feedback': 'Feedback',
  'review.feedbackPlaceholder': 'Describe what needs to be changed...',

  // Export
  'export.title': 'Export',
  'export.markdown': 'Markdown (.md)',
  'export.markdownDesc': 'Good for document editing',
  'export.html': 'HTML (.html)',
  'export.htmlDesc': 'For PDF conversion/printing',
  'export.json': 'JSON (.json)',
  'export.jsonDesc': 'For data backup/integration',
  'export.selectFormat': 'Select export format',

  // Notifications
  'notifications.title': 'Notifications',
  'notifications.empty': 'No notifications',
  'notifications.markAllRead': 'Mark all as read',
  'notifications.viewAll': 'View all notifications',
  'notifications.unread': '{{count}} unread notifications',
  'notifications.reviewPending': 'Review Required',
  'notifications.processingComplete': 'Processing Complete',
  'notifications.processingFailed': 'Processing Failed',
  'notifications.actionDueSoon': 'Due Soon',
  'notifications.actionOverdue': 'Overdue',
  'notifications.system': 'System',

  // Dashboard
  'dashboard.title': 'Dashboard',
  'dashboard.totalMeetings': 'Total Meetings',
  'dashboard.processing': 'Processing',
  'dashboard.completed': 'Completed',
  'dashboard.pendingReview': 'Pending Review',
  'dashboard.successRate': 'Success Rate',
  'dashboard.avgProcessingTime': 'Avg Processing Time',
  'dashboard.recentActivity': 'Recent Activity',
  'dashboard.systemStatus': 'System Status',
  'dashboard.dailyStats': 'Daily Stats',

  // Tags
  'tags.add': 'Add Tag',
  'tags.noTags': 'No tags',
  'tags.placeholder': 'Enter tag...',

  // Settings
  'settings.title': 'Settings',
  'settings.theme': 'Theme',
  'settings.themeLight': 'Light',
  'settings.themeDark': 'Dark',
  'settings.themeSystem': 'System',
  'settings.language': 'Language',
  'settings.languageKo': '한국어',
  'settings.languageEn': 'English',

  // Errors
  'error.notFound': 'Page not found',
  'error.unauthorized': 'Please log in',
  'error.forbidden': 'Access denied',
  'error.serverError': 'Server error occurred',
  'error.networkError': 'Network error occurred',
  'error.uploadFailed': 'Upload failed',
  'error.exportFailed': 'Export failed',

  // Time
  'time.justNow': 'Just now',
  'time.minutesAgo': '{{count}} minutes ago',
  'time.hoursAgo': '{{count}} hours ago',
  'time.daysAgo': '{{count}} days ago',
  'time.minutes': '{{count}} min',
  'time.hours': '{{count}} hr',
  'time.seconds': '{{count}} sec',
} as const;

export default en;
