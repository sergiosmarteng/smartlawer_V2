import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const ACCESS_TOKEN_COOKIE = 'smartlawer_access_token';
const PROTECTED_PATH_PREFIXES = ['/dashboard', '/upload', '/analysis', '/chat', '/user-profile'];

function isProtectedPath(pathname: string) {
  return PROTECTED_PATH_PREFIXES.some((prefix) => {
    return pathname === prefix || pathname.startsWith(`${prefix}/`);
  });
}

export default function middleware(request: NextRequest) {
  if (!isProtectedPath(request.nextUrl.pathname)) {
    return NextResponse.next();
  }

  const accessToken = request.cookies.get(ACCESS_TOKEN_COOKIE)?.value;

  if (accessToken) {
    return NextResponse.next();
  }

  const signInUrl = request.nextUrl.clone();
  signInUrl.pathname = '/sign-in';
  signInUrl.searchParams.set(
    'next',
    `${request.nextUrl.pathname}${request.nextUrl.search}`
  );

  return NextResponse.redirect(signInUrl);
}

export const config = {
  matcher: [
    '/dashboard/:path*',
    '/upload/:path*',
    '/analysis/:path*',
    '/chat/:path*',
    '/user-profile/:path*',
  ],
};
