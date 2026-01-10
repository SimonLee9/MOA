'use client';

import { useState } from 'react';
import {
  Plus, CheckSquare, Edit2, Trash2, Save, X,
  User, Calendar, AlertTriangle, Clock
} from 'lucide-react';
import { formatDate, getPriorityColor, getPriorityLabel, getActionStatusColor, getActionStatusLabel } from '@/lib/utils';
import type { ActionItem, ActionItemPriority, ActionItemStatus, ActionItemCreate } from '@/types/meeting';

interface ActionItemManagerProps {
  meetingId: string;
  items: ActionItem[];
  onAdd: (item: ActionItemCreate) => Promise<void>;
  onUpdate: (id: string, data: Partial<ActionItem>) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  readonly?: boolean;
}

const PRIORITY_OPTIONS: { value: ActionItemPriority; label: string }[] = [
  { value: 'low', label: '낮음' },
  { value: 'medium', label: '보통' },
  { value: 'high', label: '높음' },
  { value: 'urgent', label: '긴급' },
];

const STATUS_OPTIONS: { value: ActionItemStatus; label: string }[] = [
  { value: 'pending', label: '대기 중' },
  { value: 'in_progress', label: '진행 중' },
  { value: 'completed', label: '완료' },
  { value: 'cancelled', label: '취소' },
];

export default function ActionItemManager({
  meetingId,
  items,
  onAdd,
  onUpdate,
  onDelete,
  readonly = false,
}: ActionItemManagerProps) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state for new item
  const [newItem, setNewItem] = useState<ActionItemCreate>({
    content: '',
    assignee: '',
    dueDate: '',
    priority: 'medium',
  });

  // Form state for editing
  const [editItem, setEditItem] = useState<Partial<ActionItem>>({});

  const handleAdd = async () => {
    if (!newItem.content.trim()) {
      setError('내용을 입력해주세요.');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      await onAdd({
        ...newItem,
        dueDate: newItem.dueDate || undefined,
        assignee: newItem.assignee || undefined,
      });
      setNewItem({ content: '', assignee: '', dueDate: '', priority: 'medium' });
      setShowAddForm(false);
    } catch (err) {
      setError('액션 아이템 추가에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdate = async (id: string) => {
    if (!editItem.content?.trim()) {
      setError('내용을 입력해주세요.');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      await onUpdate(id, editItem);
      setEditingId(null);
      setEditItem({});
    } catch (err) {
      setError('액션 아이템 수정에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('정말 삭제하시겠습니까?')) return;

    setSaving(true);
    setError(null);
    try {
      await onDelete(id);
    } catch (err) {
      setError('액션 아이템 삭제에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (item: ActionItem) => {
    setEditingId(item.id);
    setEditItem({
      content: item.content,
      assignee: item.assignee,
      dueDate: item.dueDate,
      priority: item.priority,
      status: item.status,
    });
  };

  const toggleStatus = async (item: ActionItem) => {
    const nextStatus: Record<ActionItemStatus, ActionItemStatus> = {
      pending: 'in_progress',
      in_progress: 'completed',
      completed: 'pending',
      cancelled: 'pending',
    };
    await onUpdate(item.id, { status: nextStatus[item.status] });
  };

  // Group items by status
  const groupedItems = {
    pending: items.filter(i => i.status === 'pending'),
    in_progress: items.filter(i => i.status === 'in_progress'),
    completed: items.filter(i => i.status === 'completed'),
    cancelled: items.filter(i => i.status === 'cancelled'),
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold">액션 아이템</h2>
          <span className="text-sm text-gray-500">
            {items.filter(i => i.status === 'completed').length}/{items.length} 완료
          </span>
        </div>
        {!readonly && (
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
          >
            <Plus className="w-4 h-4" />
            추가
          </button>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 text-red-600 rounded-lg text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Add Form */}
      {showAddForm && (
        <div className="p-4 bg-white dark:bg-gray-900 rounded-xl border space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">내용 *</label>
            <input
              type="text"
              value={newItem.content}
              onChange={(e) => setNewItem({ ...newItem, content: e.target.value })}
              placeholder="액션 아이템 내용을 입력하세요"
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">담당자</label>
              <input
                type="text"
                value={newItem.assignee || ''}
                onChange={(e) => setNewItem({ ...newItem, assignee: e.target.value })}
                placeholder="담당자 이름"
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">마감일</label>
              <input
                type="date"
                value={newItem.dueDate || ''}
                onChange={(e) => setNewItem({ ...newItem, dueDate: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">우선순위</label>
              <select
                value={newItem.priority}
                onChange={(e) => setNewItem({ ...newItem, priority: e.target.value as ActionItemPriority })}
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
              >
                {PRIORITY_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <button
              onClick={() => setShowAddForm(false)}
              className="px-4 py-2 border rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
              disabled={saving}
            >
              취소
            </button>
            <button
              onClick={handleAdd}
              disabled={saving}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {saving ? <Clock className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              저장
            </button>
          </div>
        </div>
      )}

      {/* Item Groups */}
      {items.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <CheckSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p>아직 액션 아이템이 없습니다.</p>
          {!readonly && (
            <button
              onClick={() => setShowAddForm(true)}
              className="mt-4 text-blue-600 hover:underline"
            >
              첫 번째 액션 아이템 추가하기
            </button>
          )}
        </div>
      ) : (
        <>
          {/* In Progress */}
          {groupedItems.in_progress.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-blue-600 flex items-center gap-2">
                <Clock className="w-4 h-4" />
                진행 중 ({groupedItems.in_progress.length})
              </h3>
              {groupedItems.in_progress.map((item) => (
                <ActionItemCard
                  key={item.id}
                  item={item}
                  editing={editingId === item.id}
                  editData={editItem}
                  readonly={readonly}
                  saving={saving}
                  onEdit={() => startEdit(item)}
                  onEditChange={setEditItem}
                  onSave={() => handleUpdate(item.id)}
                  onCancel={() => { setEditingId(null); setEditItem({}); }}
                  onDelete={() => handleDelete(item.id)}
                  onToggleStatus={() => toggleStatus(item)}
                />
              ))}
            </div>
          )}

          {/* Pending */}
          {groupedItems.pending.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-gray-600 flex items-center gap-2">
                <CheckSquare className="w-4 h-4" />
                대기 중 ({groupedItems.pending.length})
              </h3>
              {groupedItems.pending.map((item) => (
                <ActionItemCard
                  key={item.id}
                  item={item}
                  editing={editingId === item.id}
                  editData={editItem}
                  readonly={readonly}
                  saving={saving}
                  onEdit={() => startEdit(item)}
                  onEditChange={setEditItem}
                  onSave={() => handleUpdate(item.id)}
                  onCancel={() => { setEditingId(null); setEditItem({}); }}
                  onDelete={() => handleDelete(item.id)}
                  onToggleStatus={() => toggleStatus(item)}
                />
              ))}
            </div>
          )}

          {/* Completed */}
          {groupedItems.completed.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-green-600 flex items-center gap-2">
                <CheckSquare className="w-4 h-4" />
                완료 ({groupedItems.completed.length})
              </h3>
              {groupedItems.completed.map((item) => (
                <ActionItemCard
                  key={item.id}
                  item={item}
                  editing={editingId === item.id}
                  editData={editItem}
                  readonly={readonly}
                  saving={saving}
                  onEdit={() => startEdit(item)}
                  onEditChange={setEditItem}
                  onSave={() => handleUpdate(item.id)}
                  onCancel={() => { setEditingId(null); setEditItem({}); }}
                  onDelete={() => handleDelete(item.id)}
                  onToggleStatus={() => toggleStatus(item)}
                />
              ))}
            </div>
          )}

          {/* Cancelled */}
          {groupedItems.cancelled.length > 0 && (
            <div className="space-y-2 opacity-60">
              <h3 className="text-sm font-medium text-gray-400 flex items-center gap-2">
                <X className="w-4 h-4" />
                취소됨 ({groupedItems.cancelled.length})
              </h3>
              {groupedItems.cancelled.map((item) => (
                <ActionItemCard
                  key={item.id}
                  item={item}
                  editing={editingId === item.id}
                  editData={editItem}
                  readonly={readonly}
                  saving={saving}
                  onEdit={() => startEdit(item)}
                  onEditChange={setEditItem}
                  onSave={() => handleUpdate(item.id)}
                  onCancel={() => { setEditingId(null); setEditItem({}); }}
                  onDelete={() => handleDelete(item.id)}
                  onToggleStatus={() => toggleStatus(item)}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

interface ActionItemCardProps {
  item: ActionItem;
  editing: boolean;
  editData: Partial<ActionItem>;
  readonly: boolean;
  saving: boolean;
  onEdit: () => void;
  onEditChange: (data: Partial<ActionItem>) => void;
  onSave: () => void;
  onCancel: () => void;
  onDelete: () => void;
  onToggleStatus: () => void;
}

function ActionItemCard({
  item,
  editing,
  editData,
  readonly,
  saving,
  onEdit,
  onEditChange,
  onSave,
  onCancel,
  onDelete,
  onToggleStatus,
}: ActionItemCardProps) {
  if (editing) {
    return (
      <div className="p-4 bg-white dark:bg-gray-900 rounded-xl border border-blue-500 space-y-3">
        <input
          type="text"
          value={editData.content || ''}
          onChange={(e) => onEditChange({ ...editData, content: e.target.value })}
          className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
        />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <input
            type="text"
            value={editData.assignee || ''}
            onChange={(e) => onEditChange({ ...editData, assignee: e.target.value })}
            placeholder="담당자"
            className="px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
          />
          <input
            type="date"
            value={editData.dueDate || ''}
            onChange={(e) => onEditChange({ ...editData, dueDate: e.target.value })}
            className="px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
          />
          <select
            value={editData.priority}
            onChange={(e) => onEditChange({ ...editData, priority: e.target.value as ActionItemPriority })}
            className="px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
          >
            {PRIORITY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <select
            value={editData.status}
            onChange={(e) => onEditChange({ ...editData, status: e.target.value as ActionItemStatus })}
            className="px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
        <div className="flex justify-end gap-2">
          <button
            onClick={onCancel}
            disabled={saving}
            className="px-3 py-1.5 border rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-sm"
          >
            취소
          </button>
          <button
            onClick={onSave}
            disabled={saving}
            className="px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm flex items-center gap-1"
          >
            {saving ? <Clock className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}
            저장
          </button>
        </div>
      </div>
    );
  }

  const isCompleted = item.status === 'completed';
  const isCancelled = item.status === 'cancelled';

  return (
    <div className={`p-4 bg-white dark:bg-gray-900 rounded-xl border group ${isCompleted || isCancelled ? 'opacity-60' : ''}`}>
      <div className="flex items-start gap-3">
        {!readonly && (
          <button
            onClick={onToggleStatus}
            className={`w-5 h-5 rounded border-2 flex-shrink-0 mt-0.5 flex items-center justify-center transition-colors ${
              isCompleted
                ? 'bg-green-500 border-green-500 text-white'
                : item.status === 'in_progress'
                  ? 'border-blue-500 bg-blue-100'
                  : 'border-gray-300 hover:border-blue-500'
            }`}
          >
            {isCompleted && <CheckSquare className="w-3 h-3" />}
          </button>
        )}
        <div className="flex-1 min-w-0">
          <p className={`${isCompleted ? 'line-through text-gray-400' : ''}`}>
            {item.content}
          </p>
          <div className="flex flex-wrap items-center gap-2 mt-2 text-sm">
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getPriorityColor(item.priority)}`}>
              {getPriorityLabel(item.priority)}
            </span>
            {item.assignee && (
              <span className="flex items-center gap-1 text-gray-500">
                <User className="w-3 h-3" />
                {item.assignee}
              </span>
            )}
            {item.dueDate && (
              <span className="flex items-center gap-1 text-gray-500">
                <Calendar className="w-3 h-3" />
                {formatDate(item.dueDate)}
              </span>
            )}
          </div>
        </div>
        {!readonly && (
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={onEdit}
              className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
            >
              <Edit2 className="w-4 h-4 text-gray-500" />
            </button>
            <button
              onClick={onDelete}
              className="p-1.5 hover:bg-red-100 dark:hover:bg-red-900/20 rounded"
            >
              <Trash2 className="w-4 h-4 text-red-500" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
