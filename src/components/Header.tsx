import Link from 'next/link';
import { useRouter } from 'next/router';
import { useState } from 'react';
import { useAuth } from './auth/AuthProvider';
import Icon from './landing/Icon';

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
    <header className="sticky top-0 z-30 border-b border-tinta-profunda/10 bg-papel-alta/95 backdrop-blur">
      <nav className="mx-auto flex h-[88px] max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <button
            type="button"
            className="inline-flex items-center justify-center rounded-[5px] border border-linha p-2 text-tinta-profunda transition-colors hover:border-latiim lg:hidden"
            onClick={onToggleSidebar}
            aria-label="Abrir menu"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          <Link href={user ? '/dashboard' : '/'} className="flex items-center gap-3" aria-label="SmartLawer — início">
            <span className="inline-flex h-[45px] w-10 items-center justify-center rounded-[20px_20px_5px_5px] border border-tinta-suave/40 text-latiim-texto">
              <Icon name="scale" size={25} />
            </span>
            <div>
              <p className="font-display text-[27px] leading-none tracking-[-1.2px] text-tinta-profunda">SmartLawer</p>
              <p className="mt-[9px] font-sans text-[7px] font-normal uppercase tracking-[2.65px] text-tinta-suave">Inteligência jurídica</p>
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
            <>
              <Link
                href="/sign-up"
                className="inline-flex items-center gap-4 rounded-[5px] bg-tinta-profunda px-[19px] py-[14px] text-[11px] font-medium text-white transition-colors hover:bg-tinta"
              >
                Criar minha conta
              </Link>
              <Link
                href="/sign-in"
                className="text-[11px] font-medium text-tinta-suave transition-colors hover:text-latiim-texto"
              >
                Entrar
              </Link>
            </>
          ) : (
            <>
              <div className="hidden items-center gap-3 rounded-[5px] border border-linha bg-papel-alta px-4 py-2 sm:flex">
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-tinta-profunda/10 text-xs font-semibold uppercase tracking-[0.2em] text-tinta-profunda">
                  {userInitials}
                </span>
                <div className="text-right">
                  <p className="font-mono text-[0.65rem] uppercase tracking-[0.24em] text-tinta-muda">Logado</p>
                  <p className="max-w-[12rem] truncate text-sm text-tinta">{userLabel}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => logout()}
                className="hidden rounded-[5px] border border-linha px-4 py-2 text-sm font-medium text-tinta-suave transition-colors hover:border-latiim hover:text-tinta sm:inline-flex"
              >
                Sair
              </button>
            </>
          )}

          {user && (
          <button
            type="button"
            className="inline-flex h-11 w-11 items-center justify-center rounded-[5px] border border-linha text-tinta-profunda transition-colors hover:border-latiim md:hidden"
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
        <div className="border-t border-linha bg-papel-alta px-4 py-4 md:hidden">
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
            className="mt-4 inline-flex w-full items-center justify-center rounded-[5px] border border-linha bg-papel-alta px-4 py-3 text-sm font-medium text-tinta transition-colors hover:border-latiim"
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
      className={`rounded-[5px] px-4 py-2 text-[11px] font-medium transition-colors ${
        active
          ? 'bg-tinta-profunda/10 text-tinta-profunda shadow-[inset_0_0_0_1px_rgba(20,54,45,0.25)]'
          : 'text-tinta-suave hover:text-latiim-texto'
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
      className={`block rounded-[5px] px-4 py-3 text-base font-medium transition-colors ${
        active ? 'bg-papel-areia text-tinta' : 'text-tinta-suave hover:bg-papel-areia hover:text-tinta'
      }`}
    >
      {children}
    </Link>
  );
}
