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
        <div className="min-h-[calc(100vh-4rem)] bg-papel px-4 py-10 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl rounded-[5px] border border-linha bg-white p-8 text-tinta shadow-[0_4px_10px_rgba(41,69,50,0.05)]">
            <p className="font-mono text-[9px] uppercase tracking-[2.25px] text-latiim-texto">Conta</p>
            <h1 className="mb-6 mt-2 font-display text-2xl font-normal tracking-tight text-tinta">Seu perfil</h1>
            <div className="space-y-3">
              <div className="rounded-[5px] border border-linha bg-papel-alta p-4">
                <p className="font-mono text-[9px] uppercase tracking-[2.25px] text-tinta-muda">E-mail</p>
                <p className="mt-1 text-sm text-tinta">{user?.email}</p>
              </div>
              <div className="rounded-[5px] border border-linha bg-papel-alta p-4">
                <p className="font-mono text-[9px] uppercase tracking-[2.25px] text-tinta-muda">Usuário</p>
                <p className="mt-1 text-sm text-tinta">{user?.username}</p>
              </div>
              <div className="rounded-[5px] border border-linha bg-papel-alta p-4">
                <p className="font-mono text-[9px] uppercase tracking-[2.25px] text-tinta-muda">Papel</p>
                <p className="mt-1 text-sm capitalize text-tinta">{user?.role === 'admin' ? 'administrador' : 'advogado'}</p>
              </div>
              <p className="pt-4 text-xs text-tinta-muda">A edição do perfil chega no próximo marco.</p>
              <button
                type="button"
                onClick={() => logout()}
                className="rounded-[5px] border border-linha bg-white px-4 py-2 text-sm font-medium text-tinta-suave transition-colors hover:border-latiim hover:text-tinta"
              >
                Sair da conta
              </button>
            </div>
          </div>
        </div>
      </Layout>
    </AuthGuard>
  );
}
