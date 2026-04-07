import { useState } from 'react';
import { useAuth } from '@clerk/nextjs';
import Header from './Header';
import Sidebar from './Sidebar';
import Footer from './Footer';

interface LayoutProps {
  children: React.ReactNode;
  hideSidebar?: boolean;
}

export default function Layout({ children, hideSidebar = false }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { isSignedIn } = useAuth();
  const showSidebar = isSignedIn && !hideSidebar;

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />

      <div className="flex flex-1">
        {showSidebar && (
          <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        )}

        <main className="flex-1 min-w-0">
          <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>

      <Footer />
    </div>
  );
}
