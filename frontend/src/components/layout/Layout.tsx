import React from 'react';
import Header from './Header';
import Footer from './Footer';
import ToastContainer from '../ui/Toast';

interface LayoutProps {
  children: React.ReactNode;
  showFooter?: boolean;
  className?: string;
}

const Layout: React.FC<LayoutProps> = ({ 
  children, 
  showFooter = true,
  className = ''
}) => {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />
      
      <main className={`flex-1 ${className}`}>
        {children}
      </main>
      
      {showFooter && <Footer />}
      
      {/* Toast уведомления */}
      <ToastContainer />
    </div>
  );
};

export default Layout;