import Link from 'next/link';
import { useRouter } from 'next/router';

export default function SuperSignInButton() {
  const router = useRouter();
  const href =
    router.asPath && router.asPath !== '/sign-in'
      ? { pathname: '/sign-in', query: { next: router.asPath } }
      : '/sign-in';

  return (
    <Link
      href={href}
      className="rounded-lg bg-blue-500 px-4 py-2 font-medium text-white shadow-md transition hover:bg-blue-600"
    >
      Sign In
    </Link>
  );
}
