import Link from 'next/link';
import { SignedIn, SignedOut, SignInButton, UserButton } from '@clerk/nextjs';
import { useState } from 'react';

interface HeaderProps {
  onToggleSidebar?: () => void;
}

export default function Header({ onToggleSidebar }: HeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-30">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Left side: hamburger + logo */}
          <div className="flex items-center">
            <button
              type="button"
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 lg:hidden"
              onClick={onToggleSidebar}
              aria-label="Toggle sidebar"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <Link href="/" className="ml-2 lg:ml-0 text-xl font-bold text-primary-700 tracking-tight">
              SmartLawer
            </Link>
          </div>

          {/* Center: desktop nav links */}
          <div className="hidden sm:flex sm:items-center sm:space-x-6">
            <SignedIn>
              <NavLink href="/dashboard">Dashboard</NavLink>
              <NavLink href="/documents">Documents</NavLink>
              <NavLink href="/cases">Cases</NavLink>
            </SignedIn>
          </div>

          {/* Right side: auth */}
          <div className="flex items-center space-x-3">
            <SignedOut>
              <SignInButton mode="modal">
                <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors">
                  Sign In
                </button>
              </SignInButton>
            </SignedOut>
            <SignedIn>
              <UserButton
                afterSignOutUrl="/"
                appearance={{
                  elements: {
                    avatarBox: 'h-9 w-9',
                  },
                }}
              />
            </SignedIn>

            {/* Mobile menu button */}
            <button
              type="button"
              className="sm:hidden inline-flex items-center justify-center p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile nav menu */}
        {mobileMenuOpen && (
          <div className="sm:hidden pb-3 pt-2 space-y-1">
            <SignedIn>
              <MobileNavLink href="/dashboard" onClick={() => setMobileMenuOpen(false)}>Dashboard</MobileNavLink>
              <MobileNavLink href="/documents" onClick={() => setMobileMenuOpen(false)}>Documents</MobileNavLink>
              <MobileNavLink href="/cases" onClick={() => setMobileMenuOpen(false)}>Cases</MobileNavLink>
            </SignedIn>
          </div>
        )}
      </nav>
    </header>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="text-sm font-medium text-gray-600 hover:text-primary-700 transition-colors px-1 py-2 border-b-2 border-transparent hover:border-primary-500"
    >
      {children}
    </Link>
  );
}

function MobileNavLink({ href, children, onClick }: { href: string; children: React.ReactNode; onClick: () => void }) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className="block px-3 py-2 text-base font-medium text-gray-600 hover:text-primary-700 hover:bg-gray-50 rounded-md"
    >
      {children}
    </Link>
  );
}
