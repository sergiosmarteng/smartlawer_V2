import Link from 'next/link';
import { useRouter } from 'next/router';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const sidebarLinks = [
  { href: '/dashboard', label: 'Painel', icon: DashboardIcon, description: 'Acompanhe o andamento dos documentos' },
  { href: '/upload', label: 'Nova análise', icon: DocumentIcon, description: 'Envie um PDF para análise' },
  { href: '/chat', label: 'Chat jurídico', icon: ChatIcon, description: 'Perguntas com fontes citadas' },
  { href: '/prompts', label: 'Prompts', icon: DocumentIcon, description: 'Perfis de IA do escritório' },
  { href: '/audit', label: 'Auditoria', icon: ClientIcon, description: 'Trilha de eventos da conta' },
  { href: '/user-profile', label: 'Perfil', icon: ClientIcon, description: 'Dados da sua conta' },
];

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const router = useRouter();

  return (
    <>
      {isOpen && <div className="fixed inset-0 z-40 bg-tinta-profunda/40 backdrop-blur-sm lg:hidden" onClick={onClose} />}

      <aside
        className={`fixed left-0 top-[88px] z-40 h-[calc(100vh-88px)] w-72 border-r border-linha bg-papel-alta px-4 py-6 transition-transform duration-200 ease-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:static lg:z-0 lg:translate-x-0`}
      >
        <div className="border-selo-ouro rounded-r-[5px] border border-linha border-l-0 bg-white p-5 shadow-[0_4px_10px_rgba(41,69,50,0.05)]">
          <p className="font-mono text-[0.65rem] uppercase tracking-[0.3em] text-latiim-texto">Fluxo de trabalho</p>
          <h2 className="mt-2 font-display text-lg font-normal tracking-[-0.7px] text-tinta">Operação do escritório</h2>
          <p className="mt-2 text-[11px] leading-[1.9] text-tinta-muda">
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
                className={`group flex items-start gap-3 rounded-[5px] border px-4 py-3 transition-all ${
                  isActive
                    ? 'border-tinta-profunda/25 bg-tinta-profunda/[0.07] text-tinta'
                    : 'border-transparent bg-transparent text-tinta-suave hover:border-linha hover:bg-white hover:text-tinta'
                }`}
              >
                <link.icon className={`mt-0.5 h-5 w-5 flex-shrink-0 ${isActive ? 'text-tinta-profunda' : 'text-tinta-muda group-hover:text-tinta'}`} />
                <div className="min-w-0">
                  <p className="text-sm font-medium">{link.label}</p>
                  <p className="mt-1 text-xs leading-5 text-tinta-muda">{link.description}</p>
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
