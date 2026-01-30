import {
  transformToCamelCase,
  transformToSnakeCase,
  toCamelCase,
  toSnakeCase,
  createApiTransformer,
} from '@/lib/apiTransform';

describe('API Transform Utilities', () => {
  describe('transformToCamelCase', () => {
    it('should convert snake_case keys to camelCase', () => {
      const input = {
        meeting_id: '123',
        created_at: '2024-01-15',
        user_name: 'Test User',
      };

      const result = transformToCamelCase(input);

      expect(result).toEqual({
        meetingId: '123',
        createdAt: '2024-01-15',
        userName: 'Test User',
      });
    });

    it('should handle nested objects', () => {
      const input = {
        user_data: {
          first_name: 'John',
          last_name: 'Doe',
        },
      };

      const result = transformToCamelCase(input);

      expect(result).toEqual({
        userData: {
          firstName: 'John',
          lastName: 'Doe',
        },
      });
    });

    it('should handle arrays', () => {
      const input = {
        action_items: [
          { item_id: '1', due_date: '2024-01-20' },
          { item_id: '2', due_date: '2024-01-25' },
        ],
      };

      const result = transformToCamelCase(input);

      expect(result).toEqual({
        actionItems: [
          { itemId: '1', dueDate: '2024-01-20' },
          { itemId: '2', dueDate: '2024-01-25' },
        ],
      });
    });

    it('should handle null and undefined values', () => {
      const input = {
        meeting_id: null,
        user_name: undefined,
      };

      const result = transformToCamelCase(input);

      expect(result).toEqual({
        meetingId: null,
        userName: undefined,
      });
    });

    it('should not modify already camelCase keys', () => {
      const input = {
        meetingId: '123',
        userName: 'Test',
      };

      const result = transformToCamelCase(input);

      expect(result).toEqual(input);
    });
  });

  describe('transformToSnakeCase', () => {
    it('should convert camelCase keys to snake_case', () => {
      const input = {
        meetingId: '123',
        createdAt: '2024-01-15',
        userName: 'Test User',
      };

      const result = transformToSnakeCase(input);

      expect(result).toEqual({
        meeting_id: '123',
        created_at: '2024-01-15',
        user_name: 'Test User',
      });
    });

    it('should handle nested objects', () => {
      const input = {
        userData: {
          firstName: 'John',
          lastName: 'Doe',
        },
      };

      const result = transformToSnakeCase(input);

      expect(result).toEqual({
        user_data: {
          first_name: 'John',
          last_name: 'Doe',
        },
      });
    });

    it('should handle arrays', () => {
      const input = {
        actionItems: [
          { itemId: '1', dueDate: '2024-01-20' },
          { itemId: '2', dueDate: '2024-01-25' },
        ],
      };

      const result = transformToSnakeCase(input);

      expect(result).toEqual({
        action_items: [
          { item_id: '1', due_date: '2024-01-20' },
          { item_id: '2', due_date: '2024-01-25' },
        ],
      });
    });

    it('should handle null and undefined values', () => {
      const input = {
        meetingId: null,
        userName: undefined,
      };

      const result = transformToSnakeCase(input);

      expect(result).toEqual({
        meeting_id: null,
        user_name: undefined,
      });
    });

    it('should not modify already snake_case keys', () => {
      const input = {
        meeting_id: '123',
        user_name: 'Test',
      };

      const result = transformToSnakeCase(input);

      expect(result).toEqual(input);
    });
  });

  describe('round-trip transformation', () => {
    it('should maintain data integrity through both transformations', () => {
      const original = {
        meetingId: '123',
        createdAt: '2024-01-15T10:00:00Z',
        userData: {
          firstName: 'John',
          lastName: 'Doe',
          actionItems: [
            { itemId: '1', isCompleted: false },
          ],
        },
      };

      const toSnake = transformToSnakeCase(original);
      const backToCamel = transformToCamelCase(toSnake);

      expect(backToCamel).toEqual(original);
    });
  });

  describe('string conversion functions', () => {
    describe('toCamelCase', () => {
      it('should convert snake_case to camelCase', () => {
        expect(toCamelCase('meeting_id')).toBe('meetingId');
        expect(toCamelCase('created_at')).toBe('createdAt');
        expect(toCamelCase('user_first_name')).toBe('userFirstName');
      });

      it('should handle already camelCase strings', () => {
        expect(toCamelCase('meetingId')).toBe('meetingId');
      });

      it('should handle strings without underscores', () => {
        expect(toCamelCase('meeting')).toBe('meeting');
      });
    });

    describe('toSnakeCase', () => {
      it('should convert camelCase to snake_case', () => {
        expect(toSnakeCase('meetingId')).toBe('meeting_id');
        expect(toSnakeCase('createdAt')).toBe('created_at');
        expect(toSnakeCase('userFirstName')).toBe('user_first_name');
      });

      it('should handle already snake_case strings', () => {
        expect(toSnakeCase('meeting_id')).toBe('meeting_id');
      });

      it('should handle strings without capitals', () => {
        expect(toSnakeCase('meeting')).toBe('meeting');
      });
    });
  });

  describe('createApiTransformer', () => {
    interface ApiType {
      user_id: string;
      first_name: string;
    }

    interface ClientType {
      userId: string;
      firstName: string;
    }

    it('should transform from API format to client format', () => {
      const transformer = createApiTransformer<ApiType, ClientType>();
      const apiData: ApiType = {
        user_id: '123',
        first_name: 'John',
      };

      const result = transformer.fromApi(apiData);

      expect(result).toEqual({
        userId: '123',
        firstName: 'John',
      });
    });

    it('should transform from client format to API format', () => {
      const transformer = createApiTransformer<ApiType, ClientType>();
      const clientData: Partial<ClientType> = {
        userId: '123',
        firstName: 'John',
      };

      const result = transformer.toApi(clientData);

      expect(result).toEqual({
        user_id: '123',
        first_name: 'John',
      });
    });
  });
});
