'use client';

import { useState, useEffect, useRef } from 'react';
import { X, Plus, Tag, Check } from 'lucide-react';
import { tagsApi } from '@/lib/api';

interface TagManagerProps {
  meetingId: string;
  tags: string[];
  onTagsChange: (tags: string[]) => void;
  readonly?: boolean;
}

export default function TagManager({
  meetingId,
  tags,
  onTagsChange,
  readonly = false,
}: TagManagerProps) {
  const [showInput, setShowInput] = useState(false);
  const [newTag, setNewTag] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [allTags, setAllTags] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadAllTags();
  }, []);

  useEffect(() => {
    if (showInput && inputRef.current) {
      inputRef.current.focus();
    }
  }, [showInput]);

  useEffect(() => {
    if (newTag.trim()) {
      const filtered = allTags.filter(
        t => t.toLowerCase().includes(newTag.toLowerCase()) && !tags.includes(t)
      );
      setSuggestions(filtered.slice(0, 5));
    } else {
      setSuggestions([]);
    }
  }, [newTag, allTags, tags]);

  const loadAllTags = async () => {
    try {
      const tagList = await tagsApi.listAll();
      setAllTags(tagList);
    } catch (error) {
      console.error('Failed to load tags:', error);
    }
  };

  const handleAddTag = async (tagToAdd: string) => {
    const trimmed = tagToAdd.trim();
    if (!trimmed || tags.includes(trimmed)) return;

    setSaving(true);
    try {
      const updatedTags = await tagsApi.addTags(meetingId, [trimmed]);
      onTagsChange(updatedTags);
      setNewTag('');
      setSuggestions([]);
      // Add to all tags if new
      if (!allTags.includes(trimmed)) {
        setAllTags([...allTags, trimmed].sort());
      }
    } catch (error) {
      console.error('Failed to add tag:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveTag = async (tag: string) => {
    setSaving(true);
    try {
      const updatedTags = await tagsApi.removeTag(meetingId, tag);
      onTagsChange(updatedTags);
    } catch (error) {
      console.error('Failed to remove tag:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag(newTag);
    } else if (e.key === 'Escape') {
      setShowInput(false);
      setNewTag('');
    }
  };

  // Tag colors based on hash
  const getTagColor = (tag: string) => {
    const colors = [
      'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
      'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
      'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
      'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
      'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300',
      'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300',
    ];
    const hash = tag.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    return colors[hash % colors.length];
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Tag className="w-4 h-4 text-gray-400" />

      {/* Existing Tags */}
      {tags.map((tag) => (
        <span
          key={tag}
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-sm ${getTagColor(tag)}`}
        >
          {tag}
          {!readonly && (
            <button
              onClick={() => handleRemoveTag(tag)}
              disabled={saving}
              className="hover:bg-black/10 dark:hover:bg-white/10 rounded-full p-0.5"
            >
              <X className="w-3 h-3" />
            </button>
          )}
        </span>
      ))}

      {/* Add Tag Input */}
      {!readonly && (
        <>
          {showInput ? (
            <div className="relative">
              <input
                ref={inputRef}
                type="text"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyDown={handleKeyDown}
                onBlur={() => {
                  setTimeout(() => {
                    if (!newTag) setShowInput(false);
                  }, 200);
                }}
                placeholder="태그 입력..."
                className="w-32 px-2 py-0.5 text-sm border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-700"
                disabled={saving}
              />

              {/* Suggestions Dropdown */}
              {suggestions.length > 0 && (
                <div className="absolute top-full left-0 mt-1 w-48 bg-white dark:bg-gray-800 border rounded-lg shadow-lg z-10">
                  {suggestions.map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => handleAddTag(suggestion)}
                      className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                    >
                      <Tag className="w-3 h-3 text-gray-400" />
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}

              {/* Add button */}
              {newTag.trim() && !suggestions.includes(newTag.trim()) && (
                <button
                  onClick={() => handleAddTag(newTag)}
                  disabled={saving}
                  className="absolute right-1 top-1/2 -translate-y-1/2 p-0.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                >
                  <Check className="w-4 h-4 text-green-600" />
                </button>
              )}
            </div>
          ) : (
            <button
              onClick={() => setShowInput(true)}
              className="inline-flex items-center gap-1 px-2 py-0.5 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 border border-dashed rounded-full hover:border-gray-400"
            >
              <Plus className="w-3 h-3" />
              태그 추가
            </button>
          )}
        </>
      )}

      {/* Empty State */}
      {tags.length === 0 && readonly && (
        <span className="text-sm text-gray-400">태그 없음</span>
      )}
    </div>
  );
}
