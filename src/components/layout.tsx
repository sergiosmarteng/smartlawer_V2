import { useState } from 'react';
import { useAuth } from './auth/AuthProvider';
import Header from './Header';
import Sidebar from './Sidebar';
import Footer from './Footer';

interface LayoutProps {
  children: React.ReactNode;
  hideSidebar?: boolean;
}

export default function Layout({ children, hideSidebar = false }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user } = useAuth();
  const showSidebar = Boolean(user) && !hideSidebar;

  return (
    <div className="min-h-screen bg-papel font-sans text-tinta">
      <Header onToggleSidebar={() => setSidebarOpen((current) => !current)} />

      <div className="flex min-h-[calc(100vh-88px)]">
        {showSidebar && <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />}

        <main className="min-w-0 flex-1">
          {children}
        </main>
      </div>

      <Footer />
    </div>
  );
}
