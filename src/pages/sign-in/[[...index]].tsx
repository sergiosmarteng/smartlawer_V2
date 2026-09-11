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

export default function SignInPage() {
  const router = useRouter();
  const { login, user, isLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const nextPath = useMemo(() => resolveNextPath(router.query.next), [router.query.next]);
  const signUpHref = useMemo(
    () =>
      nextPath === '/dashboard'
        ? '/sign-up'
        : {
            pathname: '/sign-up',
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
      const payload = new URLSearchParams();
      payload.append('username', email.trim());
      payload.append('password', password);
      const response = await api.post('/login/access-token', payload, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      await login(response.data.access_token, nextPath);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'E-mail ou senha inválidos');
      setLoading(false);
    }
  };

  if (isLoading || user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-tribunal-950">
        <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-ouro-400" />
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>Entrar - SmartLawer</title>
      </Head>
      <div className="bg-tribunal-texture flex min-h-screen items-center justify-center px-4">
        <div className="w-full max-w-md rounded-[2rem] border border-zinc-800 bg-tribunal-900/90 p-8 shadow-2xl shadow-black/40">
          <div className="mb-8 text-center">
            <p className="font-mono text-xs uppercase tracking-[0.32em] text-ouro-500">SmartLawer</p>
            <h1 className="mt-3 font-display text-3xl font-black text-slate-50">Entrar na banca</h1>
            <p className="mt-2 text-sm text-zinc-400">Acesse seu escritório jurídico digital</p>
          </div>

          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label htmlFor="signin-email" className="mb-1 block text-sm text-slate-300">E-mail</label>
              <input
                id="signin-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
                className="w-full rounded-xl border border-zinc-700 bg-tribunal-950 px-3 py-2.5 text-slate-200 outline-none focus:border-ouro-500"
              />
            </div>
            <div>
              <label htmlFor="signin-password" className="mb-1 block text-sm text-slate-300">Senha</label>
              <input
                id="signin-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
                className="w-full rounded-xl border border-zinc-700 bg-tribunal-950 px-3 py-2.5 text-slate-200 outline-none focus:border-ouro-500"
              />
            </div>

            {error && <p className="text-sm text-rose-400">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-full bg-ouro-500 px-4 py-3 text-sm font-bold uppercase tracking-[0.2em] text-tribunal-950 transition hover:bg-ouro-400 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {loading ? 'Entrando...' : 'Entrar'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-zinc-400">
            Ainda não tem conta?{' '}
            <Link href={signUpHref} className="font-medium text-ouro-300 underline underline-offset-4 hover:text-ouro-200">
              Criar conta
            </Link>
          </p>
        </div>
      </div>
    </>
  );
}
