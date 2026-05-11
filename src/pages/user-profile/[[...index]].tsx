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
          <title>Profile - SmartLawer</title>
        </Head>
        <div className="mx-auto max-w-2xl rounded-xl border border-zinc-800 bg-zinc-900 p-8 text-slate-200 shadow-xl">
          <h1 className="mb-6 text-2xl font-semibold">Your Profile</h1>
          <div className="space-y-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Email</p>
              <p className="text-sm text-slate-200">{user?.email}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Username</p>
              <p className="text-sm text-slate-200">{user?.username}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Role</p>
              <p className="text-sm capitalize text-slate-200">{user?.role || 'user'}</p>
            </div>
            <p className="pt-4 text-xs text-slate-500">Profile editing will be added in the next milestone.</p>
            <button
              type="button"
              onClick={() => logout()}
              className="rounded-lg border border-zinc-700 px-4 py-2 text-sm font-medium text-slate-200 transition hover:border-zinc-500 hover:bg-zinc-800"
            >
              Sign out
            </button>
          </div>
        </div>
      </Layout>
    </AuthGuard>
  );
}
