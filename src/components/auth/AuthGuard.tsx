import { useAuth } from './AuthProvider';
import { useRouter } from 'next/router';
import { useEffect } from 'react';

interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export default function AuthGuard({ children, fallback }: AuthGuardProps) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!router.isReady || isLoading || user) {
      return;
    }

    const nextPath = router.asPath.startsWith('/') ? router.asPath : '/dashboard';

    void router.replace({
      pathname: '/sign-in',
      query: { next: nextPath },
    });
  }, [isLoading, router, user]);

  if (isLoading) {
    return (
      fallback ?? (
        <div className="flex min-h-screen items-center justify-center bg-tribunal-950">
          <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-ouro-400" />
        </div>
      )
    );
  }

  if (!user) {
    return (
      fallback ?? (
        <div className="flex min-h-screen items-center justify-center bg-tribunal-950">
          <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-ouro-400" />
        </div>
      )
    );
  }

  return <>{children}</>;
}
