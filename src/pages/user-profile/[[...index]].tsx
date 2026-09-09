import Head from 'next/head';
import { useAuth } from '../../components/auth/AuthProvider';
import Layout from '../../components/layout';
import AuthGuard from '../../components/auth/AuthGuard';

export default function UserProfilePage() {
  const { user, logout } = useAuth();

  return (
    <AuthGuard>
      <Layout>
        <Head>
          <title>Perfil - SmartLawer</title>
        </Head>
        <div className="mx-auto max-w-2xl rounded-[2rem] border border-zinc-800 bg-tribunal-900/70 p-8 text-slate-200 shadow-xl">
          <p className="font-mono text-xs uppercase tracking-[0.32em] text-ouro-400">Conta</p>
          <h1 className="mb-6 mt-2 font-display text-2xl font-black">Seu perfil</h1>
          <div className="space-y-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">E-mail</p>
              <p className="text-sm text-slate-200">{user?.email}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Usuário</p>
              <p className="text-sm text-slate-200">{user?.username}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Papel</p>
              <p className="text-sm capitalize text-slate-200">{user?.role === 'admin' ? 'administrador' : 'advogado'}</p>
            </div>
            <p className="pt-4 text-xs text-slate-500">A edição do perfil chega no próximo marco.</p>
            <button
              type="button"
              onClick={() => logout()}
              className="rounded-full border border-zinc-700 px-4 py-2 text-sm font-medium text-slate-200 transition hover:border-zinc-500 hover:bg-tribunal-900"
            >
              Sair da conta
            </button>
          </div>
        </div>
      </Layout>
    </AuthGuard>
  );
}
