// Пользователь
export interface User {
  id: string;
  email: string;
  name: string;
  telegramId?: string;
  createdAt: string;
  updatedAt: string;
  isActive: boolean;
  role: 'user' | 'admin';
}

// API ключ
export interface ApiKey {
  id: string;
  key: string;
  name: string;
  description?: string;
  maxTokens: number;
  usedTokens: number;
  isActive: boolean;
  createdAt: string;
  lastUsedAt?: string;
  expiresAt?: string;
}

// Статистика использования
export interface UsageStats {
  totalRequests: number;
  totalTokens: number;
  requestsToday: number;
  tokensToday: number;
  requestsThisMonth: number;
  tokensThisMonth: number;
  averageResponseTime: number;
  successRate: number;
}

// История запросов
export interface RequestHistory {
  id: string;
  timestamp: string;
  method: string;
  endpoint: string;
  tokensUsed: number;
  responseTime: number;
  status: number;
  model?: string;
  prompt?: string;
  response?: string;
  error?: string;
}

// Тариф
export interface Tariff {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  maxTokensPerMonth: number;
  maxRequestsPerMinute: number;
  features: string[];
  isPopular?: boolean;
  isActive: boolean;
}

// Аутентификация
export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  token?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  telegramId?: string;
}

export interface AuthResponse {
  user: User;
  token: string;
  refreshToken: string;
}

// LLM запрос
export interface LLMRequest {
  prompt: string;
  model?: string;
  maxTokens?: number;
  temperature?: number;
  topP?: number;
  stream?: boolean;
}

export interface LLMResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    text: string;
    finishReason: string;
  }>;
  usage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

// Уведомления
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  timestamp: string;
}

// API ответы
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

// Формы
export interface ContactForm {
  name: string;
  email: string;
  subject: string;
  message: string;
}

export interface PasswordResetForm {
  email: string;
}

export interface ChangePasswordForm {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

export interface ProfileUpdateForm {
  name: string;
  email: string;
  telegramId?: string;
}

// Настройки
export interface UserSettings {
  theme: 'light' | 'dark' | 'system';
  language: 'ru' | 'en';
  notifications: {
    email: boolean;
    telegram: boolean;
    browser: boolean;
  };
  apiDefaults: {
    model: string;
    maxTokens: number;
    temperature: number;
  };
}

// Биллинг
export interface BillingInfo {
  currentTariff: Tariff;
  nextBillingDate?: string;
  paymentMethod?: {
    type: 'card' | 'paypal' | 'crypto';
    last4?: string;
    expiryMonth?: number;
    expiryYear?: number;
  };
  invoices: Invoice[];
}

export interface Invoice {
  id: string;
  amount: number;
  currency: string;
  status: 'paid' | 'pending' | 'failed';
  createdAt: string;
  paidAt?: string;
  downloadUrl?: string;
}

// Ошибки
export interface AppError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
}

// Навигация
export interface NavItem {
  label: string;
  href: string;
  icon?: string;
  badge?: string;
  children?: NavItem[];
  requireAuth?: boolean;
  adminOnly?: boolean;
}

// Компоненты
export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
}

export interface InputProps {
  label?: string;
  error?: string;
  placeholder?: string;
  type?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
}

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  closeOnOverlayClick?: boolean;
}

// Утилиты
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

// Константы
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    PROFILE: '/auth/profile',
    FORGOT_PASSWORD: '/auth/forgot-password',
    RESET_PASSWORD: '/auth/reset-password',
  },
  API_KEYS: {
    LIST: '/api-keys',
    CREATE: '/api-keys',
    UPDATE: '/api-keys',
    DELETE: '/api-keys',
  },
  LLM: {
    COMPLETIONS: '/v1/completions',
    MODELS: '/v1/models',
  },
  USAGE: {
    STATS: '/usage/stats',
    HISTORY: '/usage/history',
  },
  BILLING: {
    INFO: '/billing/info',
    TARIFFS: '/billing/tariffs',
    INVOICES: '/billing/invoices',
  },
} as const;