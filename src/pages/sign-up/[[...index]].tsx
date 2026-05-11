import Head from 'next/head';
import Link from 'next/link';
import { FormEvent, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import api from '../../lib/axios';
import { useAuth } from '../../components/auth/AuthProvider';

function resolveNextPath(nextParam: string | string[] | undefined) {
  if (typeof nextParam !== 'string' || !nextParam.startsWith('/')) {
    return '/dashboard';
  }

  return nextParam;
}

export default function SignUpPage() {
  const router = useRouter();
  const { login, user, isLoading } = useAuth();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const nextPath = useMemo(() => resolveNextPath(router.query.next), [router.query.next]);
  const signInHref = useMemo(
    () =>
      nextPath === '/dashboard'
        ? '/sign-in'
        : {
            pathname: '/sign-in',
            query: { next: nextPath },
          },
    [nextPath]
  );

  useEffect(() => {
    if (!router.isReady || isLoading || !user) {
      return;
    }

    void router.replace(nextPath);
  }, [isLoading, nextPath, router, user]);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      await api.post('/users/register', {
        username: username.trim(),
        email: email.trim(),
        password,
      });

      const payload = new URLSearchParams();
      payload.append('username', email.trim());
      payload.append('password', password);
      const auth = await api.post('/login/access-token', payload, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      await login(auth.data.access_token, nextPath);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to create account');
      setLoading(false);
    }
  };

  if (isLoading || user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-950">
        <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-slate-200" />
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>Sign Up - SmartLawer</title>
      </Head>
      <div className="min-h-screen flex items-center justify-center bg-zinc-950 px-4">
        <div className="w-full max-w-md rounded-xl border border-zinc-800 bg-zinc-900 p-8 shadow-2xl">
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-bold text-slate-100">SmartLawer</h1>
            <p className="mt-2 text-sm text-slate-400">Create your account to get started</p>
          </div>

          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm text-slate-300">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
                className="w-full rounded border border-zinc-700 bg-zinc-950 px-3 py-2 text-slate-200 outline-none focus:border-slate-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-300">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
                className="w-full rounded border border-zinc-700 bg-zinc-950 px-3 py-2 text-slate-200 outline-none focus:border-slate-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-300">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                required
                className="w-full rounded border border-zinc-700 bg-zinc-950 px-3 py-2 text-slate-200 outline-none focus:border-slate-500"
              />
            </div>

            {error && <p className="text-sm text-rose-400">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded bg-slate-200 px-4 py-2 font-semibold text-zinc-900 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-70"
            >
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-400">
            Already have an account?{' '}
            <Link href={signInHref} className="text-slate-200 underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </>
  );
}
