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
      setError(err?.response?.data?.detail || 'Não foi possível criar a conta');
      setLoading(false);
    }
  };

  if (isLoading || user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-papel">
        <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-tinta-profunda" />
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>Criar conta - SmartLawer</title>
      </Head>
      <div className="flex min-h-screen items-center justify-center bg-papel px-4">
        <div className="w-full max-w-md rounded-[5px] border border-linha bg-white p-8 shadow-[0_4px_10px_rgba(41,69,50,0.05)]">
          <div className="mb-8 text-center">
            <p className="font-mono text-[9px] uppercase tracking-[2.25px] text-latiim-texto">SmartLawer</p>
            <h1 className="mt-3 font-display text-3xl font-normal tracking-tight text-tinta">Criar sua conta</h1>
            <p className="mt-2 text-sm text-tinta-suave">Leva menos de um minuto para começar</p>
          </div>

          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label htmlFor="signup-username" className="mb-1 block text-sm text-tinta">Nome de usuário</label>
              <input
                id="signup-username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
                className="w-full rounded-[5px] border border-linha bg-white px-3 py-2.5 text-tinta outline-none placeholder:text-tinta-muda/60 focus:border-latiim"
              />
            </div>
            <div>
              <label htmlFor="signup-email" className="mb-1 block text-sm text-tinta">E-mail</label>
              <input
                id="signup-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
                className="w-full rounded-[5px] border border-linha bg-white px-3 py-2.5 text-tinta outline-none placeholder:text-tinta-muda/60 focus:border-latiim"
              />
            </div>
            <div>
              <label htmlFor="signup-password" className="mb-1 block text-sm text-tinta">Senha</label>
              <input
                id="signup-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                required
                className="w-full rounded-[5px] border border-linha bg-white px-3 py-2.5 text-tinta outline-none placeholder:text-tinta-muda/60 focus:border-latiim"
              />
            </div>

            {error && <p className="rounded-[5px] border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-[5px] bg-tinta-profunda px-4 py-3 text-sm font-medium uppercase tracking-[0.2em] text-white transition-colors hover:bg-tinta disabled:cursor-not-allowed disabled:opacity-70"
            >
              {loading ? 'Criando conta...' : 'Criar conta'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-tinta-suave">
            Já tem conta?{' '}
            <Link href={signInHref} className="font-medium text-latiim-texto underline underline-offset-4 hover:text-tinta-profunda">
              Entrar
            </Link>
          </p>
        </div>
      </div>
    </>
  );
}
