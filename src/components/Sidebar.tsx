import Link from 'next/link';
import { useRouter } from 'next/router';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const sidebarLinks = [
  { href: '/dashboard', label: 'Painel', icon: DashboardIcon, description: 'Acompanhe o andamento dos documentos' },
  { href: '/upload', label: 'Nova análise', icon: DocumentIcon, description: 'Envie um PDF para a esteira' },
  { href: '/chat', label: 'Chat jurídico', icon: ChatIcon, description: 'Perguntas com fontes citadas' },
  { href: '/prompts', label: 'Prompts', icon: DocumentIcon, description: 'Perfis de IA da banca' },
  { href: '/audit', label: 'Auditoria', icon: ClientIcon, description: 'Trilha de eventos da conta' },
  { href: '/user-profile', label: 'Perfil', icon: ClientIcon, description: 'Dados da sua conta' },
];

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const router = useRouter();

  return (
    <>
      {isOpen && <div className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm lg:hidden" onClick={onClose} />}

      <aside
        className={`fixed left-0 top-16 z-40 h-[calc(100vh-4rem)] w-72 border-r border-ouro-700/20 bg-tribunal-950/95 px-4 py-6 transition-transform duration-200 ease-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:static lg:z-0 lg:translate-x-0`}
      >
        <div className="border-selo-ouro rounded-r-3xl border border-zinc-800 border-l-0 bg-tribunal-900/70 p-5 shadow-2xl shadow-black/20">
          <p className="font-mono text-[0.65rem] uppercase tracking-[0.3em] text-ouro-500">Fluxo de trabalho</p>
          <h2 className="mt-2 font-display text-lg font-bold text-slate-100">Operação da banca</h2>
          <p className="mt-2 text-sm leading-6 text-zinc-400">
            Envie, acompanhe e receba a análise com tese, fundamento e peça pronta para protocolar.
          </p>
        </div>

        <nav className="mt-6 space-y-2">
          {sidebarLinks.map((link) => {
            const isActive = router.pathname === link.href || router.asPath.startsWith(`${link.href}/`);
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={onClose}
                className={`group flex items-start gap-3 rounded-2xl border px-4 py-3 transition-all ${
                  isActive
                    ? 'border-ouro-500/40 bg-ouro-500/10 text-ouro-100'
                    : 'border-transparent bg-transparent text-zinc-400 hover:border-zinc-800 hover:bg-tribunal-900/80 hover:text-slate-100'
                }`}
              >
                <link.icon className={`mt-0.5 h-5 w-5 flex-shrink-0 ${isActive ? 'text-ouro-300' : 'text-zinc-500 group-hover:text-slate-200'}`} />
                <div className="min-w-0">
                  <p className="text-sm font-medium">{link.label}</p>
                  <p className="mt-1 text-xs leading-5 text-zinc-500 group-hover:text-zinc-400">{link.description}</p>
                </div>
              </Link>
            );
          })}
        </nav>
      </aside>
    </>
  );
}

function DashboardIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
    </svg>
  );
}

function DocumentIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  );
}

function ClientIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  );
}

function ChatIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M21 12a9 9 0 01-13.2 7.9L3 21l1.2-4.6A9 9 0 1121 12z" />
    </svg>
  );
}
