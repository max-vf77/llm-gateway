import { User } from '../types';

// Ключи для localStorage
const AUTH_TOKEN_KEY = 'auth_token';
const USER_DATA_KEY = 'user_data';

// Утилиты для работы с токенами
export const tokenUtils = {
  // Получение токена из localStorage
  getToken: (): string | null => {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  },

  // Сохранение токена в localStorage
  setToken: (token: string): void => {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
  },

  // Удаление токена из localStorage
  removeToken: (): void => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
  },

  // Проверка наличия токена
  hasToken: (): boolean => {
    return !!localStorage.getItem(AUTH_TOKEN_KEY);
  },

  // Декодирование JWT токена (базовое)
  decodeToken: (token: string): any => {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('Ошибка декодирования токена:', error);
      return null;
    }
  },

  // Проверка истечения токена
  isTokenExpired: (token: string): boolean => {
    try {
      const decoded = tokenUtils.decodeToken(token);
      if (!decoded || !decoded.exp) return true;
      
      const currentTime = Date.now() / 1000;
      return decoded.exp < currentTime;
    } catch (error) {
      return true;
    }
  },

  // Получение времени истечения токена
  getTokenExpiration: (token: string): Date | null => {
    try {
      const decoded = tokenUtils.decodeToken(token);
      if (!decoded || !decoded.exp) return null;
      
      return new Date(decoded.exp * 1000);
    } catch (error) {
      return null;
    }
  },
};

// Утилиты для работы с данными пользователя
export const userUtils = {
  // Получение данных пользователя из localStorage
  getUser: (): User | null => {
    try {
      const userData = localStorage.getItem(USER_DATA_KEY);
      return userData ? JSON.parse(userData) : null;
    } catch (error) {
      console.error('Ошибка получения данных пользователя:', error);
      return null;
    }
  },

  // Сохранение данных пользователя в localStorage
  setUser: (user: User): void => {
    try {
      localStorage.setItem(USER_DATA_KEY, JSON.stringify(user));
    } catch (error) {
      console.error('Ошибка сохранения данных пользователя:', error);
    }
  },

  // Удаление данных пользователя из localStorage
  removeUser: (): void => {
    localStorage.removeItem(USER_DATA_KEY);
  },

  // Обновление данных пользователя
  updateUser: (updates: Partial<User>): User | null => {
    const currentUser = userUtils.getUser();
    if (!currentUser) return null;

    const updatedUser = { ...currentUser, ...updates };
    userUtils.setUser(updatedUser);
    return updatedUser;
  },
};

// Утилиты для проверки ролей и разрешений
export const permissionUtils = {
  // Проверка роли пользователя
  hasRole: (user: User | null, role: string): boolean => {
    return user?.role === role;
  },

  // Проверка, является ли пользователь администратором
  isAdmin: (user: User | null): boolean => {
    return permissionUtils.hasRole(user, 'admin');
  },

  // Проверка активности пользователя
  isActiveUser: (user: User | null): boolean => {
    return user?.isActive === true;
  },

  // Проверка возможности выполнения действия
  canPerformAction: (user: User | null, action: string): boolean => {
    if (!user || !user.isActive) return false;

    // Администраторы могут выполнять любые действия
    if (permissionUtils.isAdmin(user)) return true;

    // Здесь можно добавить более сложную логику разрешений
    switch (action) {
      case 'create_api_key':
      case 'view_usage_stats':
      case 'update_profile':
        return true;
      case 'manage_users':
      case 'view_admin_panel':
        return permissionUtils.isAdmin(user);
      default:
        return false;
    }
  },
};

// Утилиты для валидации
export const validationUtils = {
  // Валидация email
  isValidEmail: (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  },

  // Валидация пароля
  isValidPassword: (password: string): boolean => {
    // Минимум 8 символов, хотя бы одна буква и одна цифра
    const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$/;
    return passwordRegex.test(password);
  },

  // Валидация имени
  isValidName: (name: string): boolean => {
    return name.trim().length >= 2 && name.trim().length <= 50;
  },

  // Валидация Telegram ID
  isValidTelegramId: (telegramId: string): boolean => {
    const telegramRegex = /^@?[a-zA-Z0-9_]{5,32}$/;
    return telegramRegex.test(telegramId);
  },

  // Получение сообщений об ошибках валидации
  getPasswordValidationErrors: (password: string): string[] => {
    const errors: string[] = [];
    
    if (password.length < 8) {
      errors.push('Пароль должен содержать минимум 8 символов');
    }
    
    if (!/[A-Za-z]/.test(password)) {
      errors.push('Пароль должен содержать хотя бы одну букву');
    }
    
    if (!/\d/.test(password)) {
      errors.push('Пароль должен содержать хотя бы одну цифру');
    }
    
    return errors;
  },
};

// Утилиты для работы с сессией
export const sessionUtils = {
  // Очистка всех данных сессии
  clearSession: (): void => {
    tokenUtils.removeToken();
    userUtils.removeUser();
  },

  // Проверка валидности сессии
  isValidSession: (): boolean => {
    const token = tokenUtils.getToken();
    const user = userUtils.getUser();
    
    if (!token || !user) return false;
    
    // Проверяем истечение токена
    if (tokenUtils.isTokenExpired(token)) {
      sessionUtils.clearSession();
      return false;
    }
    
    return true;
  },

  // Инициализация сессии после входа
  initializeSession: (token: string, user: User): void => {
    tokenUtils.setToken(token);
    userUtils.setUser(user);
  },

  // Получение времени до истечения сессии
  getSessionTimeLeft: (): number => {
    const token = tokenUtils.getToken();
    if (!token) return 0;
    
    const expiration = tokenUtils.getTokenExpiration(token);
    if (!expiration) return 0;
    
    const now = new Date();
    const timeLeft = expiration.getTime() - now.getTime();
    
    return Math.max(0, timeLeft);
  },

  // Проверка необходимости обновления токена
  shouldRefreshToken: (): boolean => {
    const timeLeft = sessionUtils.getSessionTimeLeft();
    const fiveMinutes = 5 * 60 * 1000; // 5 минут в миллисекундах
    
    return timeLeft > 0 && timeLeft < fiveMinutes;
  },
};

// Утилиты для работы с API ключами
export const apiKeyUtils = {
  // Маскирование API ключа для отображения
  maskApiKey: (key: string): string => {
    if (key.length <= 8) return key;
    
    const start = key.substring(0, 8);
    const end = key.substring(key.length - 4);
    const middle = '*'.repeat(Math.max(0, key.length - 12));
    
    return `${start}${middle}${end}`;
  },

  // Валидация формата API ключа
  isValidApiKeyFormat: (key: string): boolean => {
    // Проверяем формат sk-xxx или sk-test-xxx
    const standardKeyRegex = /^sk-[a-zA-Z0-9]{48}$/;
    const testKeyRegex = /^sk-(test|prod|demo)-[a-zA-Z0-9-]+$/;
    
    return standardKeyRegex.test(key) || testKeyRegex.test(key);
  },

  // Определение типа ключа
  getKeyType: (key: string): 'standard' | 'test' | 'production' | 'demo' | 'unknown' => {
    if (key.startsWith('sk-test-')) return 'test';
    if (key.startsWith('sk-prod-')) return 'production';
    if (key.startsWith('sk-demo-')) return 'demo';
    if (key.startsWith('sk-') && key.length === 51) return 'standard';
    return 'unknown';
  },

  // Копирование ключа в буфер обмена
  copyToClipboard: async (text: string): Promise<boolean> => {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (error) {
      // Fallback для старых браузеров
      try {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        return true;
      } catch (fallbackError) {
        console.error('Не удалось скопировать в буфер обмена:', fallbackError);
        return false;
      }
    }
  },
};

// Утилиты для форматирования
export const formatUtils = {
  // Форматирование числа токенов
  formatTokens: (tokens: number): string => {
    if (tokens >= 1000000) {
      return `${(tokens / 1000000).toFixed(1)}M`;
    }
    if (tokens >= 1000) {
      return `${(tokens / 1000).toFixed(1)}K`;
    }
    return tokens.toString();
  },

  // Форматирование даты
  formatDate: (date: string | Date): string => {
    const d = new Date(date);
    return d.toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  },

  // Форматирование относительного времени
  formatRelativeTime: (date: string | Date): string => {
    const now = new Date();
    const target = new Date(date);
    const diffMs = now.getTime() - target.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMinutes < 1) return 'только что';
    if (diffMinutes < 60) return `${diffMinutes} мин. назад`;
    if (diffHours < 24) return `${diffHours} ч. назад`;
    if (diffDays < 7) return `${diffDays} дн. назад`;
    
    return formatUtils.formatDate(date);
  },

  // Форматирование размера файла
  formatFileSize: (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },
};