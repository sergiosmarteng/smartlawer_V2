import { useAuth } from '@clerk/nextjs';
import { useRouter } from 'next/router';
import { useEffect } from 'react';

interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export default function AuthGuard({ children, fallback }: AuthGuardProps) {
  const { isLoaded, isSignedIn } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoaded && !isSignedIn) {
      router.push('/sign-in');
    }
  }, [isLoaded, isSignedIn, router]);

  if (!isLoaded) {
    return (
      fallback ?? (
        <div className="flex items-center justify-center min-h-screen-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      )
    );
  }

  if (!isSignedIn) {
    return null;
  }

  return <>{children}</>;
}
