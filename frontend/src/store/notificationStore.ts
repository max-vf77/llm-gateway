import { create } from 'zustand';
import { Notification } from '../types';

interface NotificationStore {
  notifications: Notification[];
  
  // Действия
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
  
  // Удобные методы для разных типов уведомлений
  success: (title: string, message: string, duration?: number) => void;
  error: (title: string, message: string, duration?: number) => void;
  warning: (title: string, message: string, duration?: number) => void;
  info: (title: string, message: string, duration?: number) => void;
}

export const useNotificationStore = create<NotificationStore>((set, get) => ({
  notifications: [],

  // Добавление уведомления
  addNotification: (notification) => {
    const id = Math.random().toString(36).substr(2, 9);
    const timestamp = new Date().toISOString();
    const duration = notification.duration || 5000;

    const newNotification: Notification = {
      ...notification,
      id,
      timestamp,
      duration,
    };

    set((state) => ({
      notifications: [...state.notifications, newNotification],
    }));

    // Автоматическое удаление через указанное время
    if (duration > 0) {
      setTimeout(() => {
        get().removeNotification(id);
      }, duration);
    }
  },

  // Удаление уведомления
  removeNotification: (id) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }));
  },

  // Очистка всех уведомлений
  clearNotifications: () => {
    set({ notifications: [] });
  },

  // Успешное уведомление
  success: (title, message, duration = 5000) => {
    get().addNotification({
      type: 'success',
      title,
      message,
      duration,
    });
  },

  // Уведомление об ошибке
  error: (title, message, duration = 7000) => {
    get().addNotification({
      type: 'error',
      title,
      message,
      duration,
    });
  },

  // Предупреждение
  warning: (title, message, duration = 6000) => {
    get().addNotification({
      type: 'warning',
      title,
      message,
      duration,
    });
  },

  // Информационное уведомление
  info: (title, message, duration = 5000) => {
    get().addNotification({
      type: 'info',
      title,
      message,
      duration,
    });
  },
}));

// Хук для удобного использования уведомлений
export const useNotifications = () => {
  const { success, error, warning, info } = useNotificationStore();
  
  return {
    success,
    error,
    warning,
    info,
    
    // Уведомления для API операций
    apiSuccess: (operation: string) => {
      success('Успешно', `${operation} выполнено успешно`);
    },
    
    apiError: (operation: string, errorMessage?: string) => {
      error(
        'Ошибка',
        errorMessage || `Не удалось выполнить ${operation.toLowerCase()}`
      );
    },
    
    // Уведомления для форм
    formSuccess: (action: string) => {
      success('Сохранено', `${action} успешно сохранено`);
    },
    
    formError: (field: string, errorMessage: string) => {
      error('Ошибка валидации', `${field}: ${errorMessage}`);
    },
    
    // Уведомления для аутентификации
    authSuccess: (action: string) => {
      success('Добро пожаловать', action);
    },
    
    authError: (errorMessage: string) => {
      error('Ошибка аутентификации', errorMessage);
    },
    
    // Уведомления для копирования
    copySuccess: (item: string) => {
      success('Скопировано', `${item} скопировано в буфер обмена`);
    },
    
    copyError: () => {
      error('Ошибка', 'Не удалось скопировать в буфер обмена');
    },
  };
};