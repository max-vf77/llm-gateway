import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import { 
  ApiResponse, 
  AuthResponse, 
  LoginRequest, 
  RegisterRequest,
  User,
  ApiKey,
  UsageStats,
  RequestHistory,
  LLMRequest,
  LLMResponse,
  Tariff,
  PaginatedResponse
} from '../types';

// Конфигурация API
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:12000';

// Создание экземпляра axios
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Для HttpOnly cookies
});

// Интерсептор для добавления токена авторизации
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Интерсептор для обработки ответов
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    // Если получили 401 и это не повторный запрос
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Попытка обновить токен
        const refreshResponse = await api.post('/auth/refresh');
        const { token } = refreshResponse.data;
        
        localStorage.setItem('auth_token', token);
        
        // Повторяем оригинальный запрос с новым токеном
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Если обновление токена не удалось, перенаправляем на логин
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Обработчик ошибок API
const handleApiError = (error: AxiosError): string => {
  if (error.response?.data) {
    const data = error.response.data as any;
    return data.message || data.error || 'Произошла ошибка';
  }
  
  if (error.code === 'NETWORK_ERROR') {
    return 'Ошибка сети. Проверьте подключение к интернету.';
  }
  
  if (error.code === 'ECONNABORTED') {
    return 'Превышено время ожидания запроса.';
  }
  
  return error.message || 'Неизвестная ошибка';
};

// API методы для аутентификации
export const authApi = {
  // Вход в систему
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    try {
      const response = await api.post<ApiResponse<AuthResponse>>('/auth/login', credentials);
      return response.data.data!;
    } catch (error) {
      throw new Error(handleApiError(error as AxiosError));
    }
  },

  // Регистрация
  register: async (userData: RegisterRequest): Promise<AuthResponse> => {
    try {
      const response = await api.post<ApiResponse<AuthResponse>>('/auth/register', userData);
      return response.data.data!;
    } catch (error) {
      throw new Error(handleApiError(error as AxiosError));
    }
  },

  // Выход из системы
  logout: async (): Promise<void> => {
    try {
      await api.post('/auth/logout');
      localStorage.removeItem('auth_token');
    } catch (error) {
      // Игнорируем ошибки при выходе
      localStorage.removeItem('auth_token');
    }
  },

  // Получение профиля пользователя
  getProfile: async (): Promise<User> => {
    try {
      const response = await api.get<ApiResponse<User>>('/auth/profile');
      return response.data.data!;
    } catch (error) {
      throw new Error(handleApiError(error as AxiosError));
    }
  },

  // Обновление профиля
  updateProfile: async (userData: Partial<User>): Promise<User> => {
    try {
      const response = await api.put<ApiResponse<User>>('/auth/profile', userData);
      return response.data.data!;
    } catch (error) {
      throw new Error(handleApiError(error as AxiosError));
    }
  },

  // Сброс пароля
  forgotPassword: async (email: string): Promise<void> => {
    try {
      await api.post('/auth/forgot-password', { email });
    } catch (error) {
      throw new Error(handleApiError(error as AxiosError));
    }
  },

  // Смена пароля
  resetPassword: async (token: string, password: string): Promise<void> => {
    try {
      await api.post('/auth/reset-password', { token, password });
    } catch (error) {
      throw new Error(handleApiError(error as AxiosError));
    }
  },
};

// API методы для работы с API ключами
export const apiKeysApi = {
  // Получение списка ключей
  getKeys: async (): Promise<ApiKey[]> => {
    try {
      const response = await api.get<ApiResponse<ApiKey[]>>('/api-keys');
      return response.data.data!;
    } catch (error) {
      throw new Error(handleApiError(error as AxiosError));
    }
  },

  // Создание нового ключа
  createKey: async (keyData: { name: string; description?: string; maxTokens: number }): Promise<ApiKey> => {
    try {
      const response = await api.post<ApiResponse<ApiKey>>('/api-keys', keyData);
      return response.data.data!;
    } catch (error) {
      throw new Error(handleApiError(error as AxiosError));
    }
  },

  // Обновление ключа
  updateKey: async (keyId: string, keyData: Partial<ApiKey>): Promise<ApiKey> => {
    try {
      const response = await api.put<ApiResponse<ApiKey>>(`/api-keys/${keyId}`, keyData);
      return response.data.data!;
    } catch (error) {
      throw new Error(handleApiError(error as AxiosError));
    }
  },

  // Удаление ключа
  deleteKey: async (keyId: string): Promise<void> => {
    try {
      await api.delete(`/api-keys/${keyId}`);
    } catch (error) {
      throw new Error(handleApiError(error as AxiosError));
    }
  },

  // Регенерация ключа
  regenerateKey: async (keyId: string): Promise<ApiKey> => {
    try {
      const response = await api.post<ApiResponse<ApiKey>>(`/api-keys/${keyId}/regenerate`);
      return response.data.data!;
    } catch (error) {
      throw new Error(handleApiError(error as AxiosError));
    }
  },
};

// API методы для статистики использования
export const usageApi = {
  // Получение статистики
  getStats: async (): Promise<UsageStats> => {
    try {
      const response = await api.get<ApiResponse<UsageStats>>('/usage/stats');
      return response.data.data!;
    } catch (error) {
      throw new Error(handleApiError(error as AxiosError));
    }
  },

  // Получение истории запросов
  getHistory: async (page = 1, limit = 20): Promise<PaginatedResponse<RequestHistory>> => {
    try {
      const response = await api.get<ApiResponse<PaginatedResponse<RequestHistory>>>(
        `/usage/history?page=${page}&limit=${limit}`
      );
      return response.data.data!;
    } catch (error) {
      throw new Error(handleApiError(error as AxiosError));
    }
  },
};

// API методы для работы с LLM
export const llmApi = {
  // Отправка запроса к LLM
  completion: async (request: LLMRequest): Promise<LLMResponse> => {
    try {
      const response = await api.post<LLMResponse>('/v1/completions', request);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error as AxiosError));
    }
  },

  // Получение списка доступных моделей
  getModels: async (): Promise<string[]> => {
    try {
      const response = await api.get<ApiResponse<string[]>>('/v1/models');
      return response.data.data!;
    } catch (error) {
      throw new Error(handleApiError(error as AxiosError));
    }
  },
};

// API методы для тарифов и биллинга
export const billingApi = {
  // Получение доступных тарифов
  getTariffs: async (): Promise<Tariff[]> => {
    try {
      const response = await api.get<ApiResponse<Tariff[]>>('/billing/tariffs');
      return response.data.data!;
    } catch (error) {
      throw new Error(handleApiError(error as AxiosError));
    }
  },

  // Получение информации о биллинге
  getBillingInfo: async (): Promise<any> => {
    try {
      const response = await api.get<ApiResponse<any>>('/billing/info');
      return response.data.data!;
    } catch (error) {
      throw new Error(handleApiError(error as AxiosError));
    }
  },
};

// Общие API методы
export const commonApi = {
  // Проверка здоровья сервиса
  healthCheck: async (): Promise<{ status: string; timestamp: string }> => {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error as AxiosError));
    }
  },

  // Получение информации о сервисе
  getServiceInfo: async (): Promise<any> => {
    try {
      const response = await api.get('/');
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error as AxiosError));
    }
  },
};

// Экспорт основного экземпляра API
export default api;