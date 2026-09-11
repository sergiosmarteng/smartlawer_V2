import Link from 'next/link';
import { useRouter } from 'next/router';
import { useState } from 'react';
import { useAuth } from './auth/AuthProvider';

interface HeaderProps {
  onToggleSidebar?: () => void;
}

const primaryLinks = [
  { href: '/dashboard', label: 'Painel' },
  { href: '/upload', label: 'Nova análise' },
  { href: '/chat', label: 'Chat jurídico' },
  { href: '/prompts', label: 'Prompts' },
  { href: '/audit', label: 'Auditoria' },
  { href: '/user-profile', label: 'Perfil' },
];

export default function Header({ onToggleSidebar }: HeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, logout } = useAuth();
  const router = useRouter();
  const userLabel = user?.username || user?.email || 'Advogado';
  const userInitials = userLabel.slice(0, 2).toUpperCase();

  return (
    <header className="sticky top-0 z-30 border-b border-ouro-700/30 bg-tribunal-950/95 backdrop-blur">
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <button
            type="button"
            className="inline-flex items-center justify-center rounded-xl border border-zinc-800 p-2 text-slate-300 transition-colors hover:border-ouro-600/50 hover:bg-tribunal-900 lg:hidden"
            onClick={onToggleSidebar}
            aria-label="Abrir menu"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          <Link href={user ? '/dashboard' : '/'} className="flex items-center gap-3">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-ouro-500/40 bg-gradient-to-br from-ouro-500/25 to-ouro-700/10 font-display text-sm font-black tracking-[0.2em] text-ouro-300">
              SL
            </span>
            <div>
              <p className="font-display text-base font-bold tracking-wide text-slate-100">SmartLawer</p>
              <p className="font-mono text-[0.65rem] uppercase tracking-[0.3em] text-ouro-500/90">Advocacia de excelência</p>
            </div>
          </Link>
        </div>

        <div className="hidden items-center gap-2 md:flex">
          {user &&
            primaryLinks.map((link) => {
              const isActive = router.pathname === link.href || router.asPath.startsWith(`${link.href}/`);
              return (
                <NavLink key={link.href} href={link.href} active={isActive}>
                  {link.label}
                </NavLink>
              );
            })}
        </div>

        <div className="flex items-center gap-3">
          {!user ? (
            <Link
              href="/sign-in"
              className="inline-flex items-center rounded-full border border-ouro-500/40 bg-ouro-500/10 px-4 py-2 text-sm font-medium text-ouro-200 transition-colors hover:border-ouro-400/60 hover:bg-ouro-500/20"
            >
              Entrar
            </Link>
          ) : (
            <>
              <div className="hidden items-center gap-3 rounded-full border border-zinc-800 bg-tribunal-900/80 px-4 py-2 sm:flex">
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-ouro-500/15 text-xs font-semibold uppercase tracking-[0.2em] text-ouro-300">
                  {userInitials}
                </span>
                <div className="text-right">
                  <p className="font-mono text-[0.65rem] uppercase tracking-[0.24em] text-zinc-500">Logado</p>
                  <p className="max-w-[12rem] truncate text-sm text-slate-200">{userLabel}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => logout()}
                className="hidden rounded-full border border-zinc-800 px-4 py-2 text-sm font-medium text-slate-300 transition-colors hover:border-zinc-700 hover:bg-tribunal-900 sm:inline-flex"
              >
                Sair
              </button>
            </>
          )}

          {user && (
          <button
            type="button"
            className="inline-flex items-center justify-center rounded-xl border border-zinc-800 p-2 text-slate-300 transition-colors hover:border-ouro-600/50 hover:bg-tribunal-900 md:hidden"
            onClick={() => setMobileMenuOpen((current) => !current)}
            aria-label="Abrir menu"
          >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          )}
        </div>
      </nav>

      {mobileMenuOpen && user && (
        <div className="border-t border-zinc-800 bg-zinc-950 px-4 py-4 md:hidden">
          <div className="space-y-2">
            {primaryLinks.map((link) => {
              const isActive = router.pathname === link.href || router.asPath.startsWith(`${link.href}/`);
              return (
                <MobileNavLink
                  key={link.href}
                  href={link.href}
                  active={isActive}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {link.label}
                </MobileNavLink>
              );
            })}
          </div>

          <button
            type="button"
            onClick={() => logout()}
            className="mt-4 inline-flex w-full items-center justify-center rounded-xl border border-zinc-800 px-4 py-3 text-sm font-medium text-slate-300 transition-colors hover:border-zinc-700 hover:bg-tribunal-900"
          >
            Sair
          </button>
        </div>
      )}
    </header>
  );
}

function NavLink({ href, children, active }: { href: string; children: React.ReactNode; active: boolean }) {
  return (
    <Link
      href={href}
      className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
        active
          ? 'bg-ouro-500/15 text-ouro-200 shadow-[inset_0_0_0_1px_rgba(201,162,39,0.45)]'
          : 'text-zinc-400 hover:bg-tribunal-900/80 hover:text-slate-100'
      }`}
    >
      {children}
    </Link>
  );
}

function MobileNavLink({
  href,
  children,
  onClick,
  active,
}: {
  href: string;
  children: React.ReactNode;
  onClick: () => void;
  active: boolean;
}) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className={`block rounded-xl px-4 py-3 text-base font-medium transition-colors ${
        active ? 'bg-zinc-900 text-slate-100' : 'text-zinc-300 hover:bg-zinc-900 hover:text-slate-100'
      }`}
    >
      {children}
    </Link>
  );
}
