import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';

// Pages
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
// import DashboardPage from './pages/DashboardPage';
// import ApiKeysPage from './pages/ApiKeysPage';
// import UsagePage from './pages/UsagePage';
// import PlaygroundPage from './pages/PlaygroundPage';
// import DocsPage from './pages/DocsPage';
// import PricingPage from './pages/PricingPage';

// Components
import { FullScreenSpinner } from './components/ui/Spinner';

// Protected Route Component
interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore();
  
  if (isLoading) {
    return <FullScreenSpinner text="Проверка аутентификации..." />;
  }
  
  if (!isAuthenticated || !checkAuth()) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

// Public Route Component (redirect to dashboard if authenticated)
interface PublicRouteProps {
  children: React.ReactNode;
}

const PublicRoute: React.FC<PublicRouteProps> = ({ children }) => {
  const { isAuthenticated, checkAuth } = useAuthStore();
  
  if (isAuthenticated && checkAuth()) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return <>{children}</>;
};

function App() {
  const { initialize, isLoading } = useAuthStore();
  
  // Инициализация аутентификации при загрузке приложения
  useEffect(() => {
    initialize();
  }, [initialize]);
  
  if (isLoading) {
    return <FullScreenSpinner text="Загрузка приложения..." />;
  }
  
  return (
    <Router>
      <Routes>
        {/* Публичные маршруты */}
        <Route path="/" element={<HomePage />} />
        
        <Route 
          path="/login" 
          element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          } 
        />
        
        <Route 
          path="/register" 
          element={
            <PublicRoute>
              <RegisterPage />
            </PublicRoute>
          } 
        />
        
        {/* Защищенные маршруты */}
        {/* <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/api-keys" 
          element={
            <ProtectedRoute>
              <ApiKeysPage />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/usage" 
          element={
            <ProtectedRoute>
              <UsagePage />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/playground" 
          element={
            <ProtectedRoute>
              <PlaygroundPage />
            </ProtectedRoute>
          } 
        /> */}
        
        {/* Публичные информационные страницы */}
        {/* <Route path="/docs" element={<DocsPage />} />
        <Route path="/pricing" element={<PricingPage />} /> */}
        
        {/* Временные заглушки */}
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                  <h1 className="text-2xl font-bold text-gray-900 mb-4">Dashboard</h1>
                  <p className="text-gray-600">Страница в разработке</p>
                </div>
              </div>
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/docs" 
          element={
            <div className="min-h-screen flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-2xl font-bold text-gray-900 mb-4">Документация</h1>
                <p className="text-gray-600">Страница в разработке</p>
              </div>
            </div>
          } 
        />
        
        <Route 
          path="/pricing" 
          element={
            <div className="min-h-screen flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-2xl font-bold text-gray-900 mb-4">Тарифы</h1>
                <p className="text-gray-600">Страница в разработке</p>
              </div>
            </div>
          } 
        />
        
        <Route 
          path="/playground" 
          element={
            <ProtectedRoute>
              <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                  <h1 className="text-2xl font-bold text-gray-900 mb-4">Playground</h1>
                  <p className="text-gray-600">Страница в разработке</p>
                </div>
              </div>
            </ProtectedRoute>
          } 
        />
        
        {/* 404 страница */}
        <Route 
          path="*" 
          element={
            <div className="min-h-screen flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-4xl font-bold text-gray-900 mb-4">404</h1>
                <p className="text-gray-600 mb-8">Страница не найдена</p>
                <a 
                  href="/" 
                  className="text-primary-600 hover:text-primary-500 font-medium"
                >
                  Вернуться на главную
                </a>
              </div>
            </div>
          } 
        />
      </Routes>
    </Router>
  );
}

export default App;
