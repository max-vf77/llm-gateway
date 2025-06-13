import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, AuthState, LoginRequest, RegisterRequest } from '../types';
import { authApi } from '../lib/api';
import { sessionUtils, userUtils, tokenUtils } from '../lib/auth';

interface AuthStore extends AuthState {
  // Действия
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
  updateUser: (updates: Partial<User>) => void;
  clearError: () => void;
  
  // Состояние ошибок
  error: string | null;
  setError: (error: string | null) => void;
  
  // Состояние загрузки
  setLoading: (loading: boolean) => void;
  
  // Проверка аутентификации
  checkAuth: () => boolean;
  
  // Инициализация при загрузке приложения
  initialize: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Начальное состояние
      user: null,
      isAuthenticated: false,
      isLoading: false,
      token: undefined,
      error: null,

      // Установка ошибки
      setError: (error: string | null) => {
        set({ error });
      },

      // Очистка ошибки
      clearError: () => {
        set({ error: null });
      },

      // Установка состояния загрузки
      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      // Вход в систему
      login: async (credentials: LoginRequest) => {
        try {
          set({ isLoading: true, error: null });
          
          const response = await authApi.login(credentials);
          const { user, token } = response;
          
          // Сохраняем данные в localStorage
          sessionUtils.initializeSession(token, user);
          
          set({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Ошибка входа';
          set({
            error: errorMessage,
            isLoading: false,
            isAuthenticated: false,
            user: null,
            token: undefined,
          });
          throw error;
        }
      },

      // Регистрация
      register: async (userData: RegisterRequest) => {
        try {
          set({ isLoading: true, error: null });
          
          const response = await authApi.register(userData);
          const { user, token } = response;
          
          // Сохраняем данные в localStorage
          sessionUtils.initializeSession(token, user);
          
          set({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Ошибка регистрации';
          set({
            error: errorMessage,
            isLoading: false,
            isAuthenticated: false,
            user: null,
            token: undefined,
          });
          throw error;
        }
      },

      // Выход из системы
      logout: async () => {
        try {
          set({ isLoading: true });
          
          // Отправляем запрос на сервер
          await authApi.logout();
        } catch (error) {
          console.error('Ошибка при выходе:', error);
        } finally {
          // Очищаем локальные данные в любом случае
          sessionUtils.clearSession();
          
          set({
            user: null,
            token: undefined,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      },

      // Загрузка данных пользователя
      loadUser: async () => {
        try {
          set({ isLoading: true, error: null });
          
          const user = await authApi.getProfile();
          
          // Обновляем данные пользователя в localStorage
          userUtils.setUser(user);
          
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Ошибка загрузки профиля';
          
          // Если ошибка 401, очищаем сессию
          if (errorMessage.includes('401') || errorMessage.includes('Unauthorized')) {
            sessionUtils.clearSession();
            set({
              user: null,
              token: undefined,
              isAuthenticated: false,
              isLoading: false,
              error: null,
            });
          } else {
            set({
              error: errorMessage,
              isLoading: false,
            });
          }
          
          throw error;
        }
      },

      // Обновление данных пользователя
      updateUser: (updates: Partial<User>) => {
        const currentUser = get().user;
        if (!currentUser) return;

        const updatedUser = { ...currentUser, ...updates };
        
        // Обновляем в localStorage
        userUtils.setUser(updatedUser);
        
        set({ user: updatedUser });
      },

      // Проверка аутентификации
      checkAuth: (): boolean => {
        const { user, token } = get();
        
        // Проверяем наличие пользователя и токена
        if (!user || !token) return false;
        
        // Проверяем валидность сессии
        return sessionUtils.isValidSession();
      },

      // Инициализация при загрузке приложения
      initialize: () => {
        const token = tokenUtils.getToken();
        const user = userUtils.getUser();
        
        if (token && user && sessionUtils.isValidSession()) {
          set({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } else {
          // Очищаем невалидные данные
          sessionUtils.clearSession();
          set({
            user: null,
            token: undefined,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      },
    }),
    {
      name: 'auth-store',
      // Сохраняем только необходимые поля
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
      // Восстанавливаем состояние при загрузке
      onRehydrateStorage: () => (state) => {
        if (state) {
          // Проверяем валидность восстановленной сессии
          if (!state.checkAuth()) {
            state.initialize();
          }
        }
      },
    }
  )
);

// Хук для проверки ролей
export const useAuth = () => {
  const { user, isAuthenticated, isLoading } = useAuthStore();
  
  return {
    user,
    isAuthenticated,
    isLoading,
    isAdmin: user?.role === 'admin',
    isActive: user?.isActive === true,
    hasRole: (role: string) => user?.role === role,
  };
};

// Хук для защищенных маршрутов
export const useRequireAuth = () => {
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore();
  
  return {
    isAuthenticated: isAuthenticated && checkAuth(),
    isLoading,
    requireAuth: () => {
      if (!isAuthenticated || !checkAuth()) {
        throw new Error('Требуется аутентификация');
      }
    },
  };
};