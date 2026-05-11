import Link from 'next/link';
import { useRouter } from 'next/router';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const sidebarLinks = [
  { href: '/dashboard', label: 'Dashboard', icon: DashboardIcon, description: 'Track document processing' },
  { href: '/upload', label: 'New analysis', icon: DocumentIcon, description: 'Send a new PDF to the pipeline' },
  { href: '/user-profile', label: 'Profile', icon: ClientIcon, description: 'Review account details' },
];

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const router = useRouter();

  return (
    <>
      {isOpen && <div className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm lg:hidden" onClick={onClose} />}

      <aside
        className={`fixed left-0 top-16 z-40 h-[calc(100vh-4rem)] w-72 border-r border-zinc-800 bg-zinc-950/98 px-4 py-6 transition-transform duration-200 ease-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:static lg:z-0 lg:translate-x-0`}
      >
        <div className="rounded-3xl border border-zinc-800 bg-zinc-900/70 p-5 shadow-2xl shadow-black/20">
          <p className="text-xs uppercase tracking-[0.3em] text-zinc-500">Workflow</p>
          <h2 className="mt-2 text-lg font-medium text-slate-100">Main operations</h2>
          <p className="mt-2 text-sm leading-6 text-zinc-400">
            Keep the upload, processing, and analysis loop visible while the backend finishes each document.
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
                    ? 'border-sky-500/30 bg-sky-500/10 text-sky-100'
                    : 'border-transparent bg-transparent text-zinc-400 hover:border-zinc-800 hover:bg-zinc-900/80 hover:text-slate-100'
                }`}
              >
                <link.icon className={`mt-0.5 h-5 w-5 flex-shrink-0 ${isActive ? 'text-sky-300' : 'text-zinc-500 group-hover:text-slate-200'}`} />
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
