/**
 * Team Types
 */

export type TeamRole = 'owner' | 'admin' | 'member' | 'viewer';

export interface TeamMember {
  id: string;
  userId: string;
  userEmail: string;
  userName: string;
  role: TeamRole;
  joinedAt: string;
}

export interface Team {
  id: string;
  name: string;
  description?: string;
  slug: string;
  ownerId: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
  memberCount?: number;
}

export interface TeamDetail extends Team {
  members: TeamMember[];
}

export interface TeamCreate {
  name: string;
  description?: string;
  slug: string;
}

export interface TeamUpdate {
  name?: string;
  description?: string;
}

export interface TeamListResponse {
  items: Team[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface TeamMemberAdd {
  userId: string;
  role: TeamRole;
}

export interface TeamMemberUpdate {
  role: TeamRole;
}

export interface TeamInvitation {
  id: string;
  teamId: string;
  teamName: string;
  email: string;
  role: TeamRole;
  invitedByName: string;
  expiresAt: string;
  createdAt: string;
  isExpired: boolean;
}

export interface TeamInvitationCreate {
  email: string;
  role?: TeamRole;
}

export interface TeamInvitationAccept {
  token: string;
}

export const ROLE_LABELS: Record<TeamRole, string> = {
  owner: '소유자',
  admin: '관리자',
  member: '멤버',
  viewer: '뷰어',
};

export const ROLE_DESCRIPTIONS: Record<TeamRole, string> = {
  owner: '팀의 모든 권한을 가집니다',
  admin: '멤버 관리 및 설정 변경 가능',
  member: '회의 생성 및 편집 가능',
  viewer: '회의 조회만 가능',
};

export function canManageTeam(role: TeamRole): boolean {
  return role === 'owner' || role === 'admin';
}

export function canEditMeeting(role: TeamRole): boolean {
  return role !== 'viewer';
}
