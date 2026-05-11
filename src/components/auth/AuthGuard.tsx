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
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
        </div>
      )
    );
  }

  if (!user) {
    return (
      fallback ?? (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
        </div>
      )
    );
  }

  return <>{children}</>;
}
