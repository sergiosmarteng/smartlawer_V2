import { auth, currentUser } from '@clerk/nextjs/server';

/**
 * Get the current authenticated user's ID or null if not authenticated.
 * Use in Server Components and API routes.
 */
export async function getAuthUserId(): Promise<string | null> {
  const { userId } = await auth();
  return userId;
}

/**
 * Require authentication - throws redirect if not authenticated.
 * Use in Server Components that require auth.
 */
export async function requireAuth(): Promise<string> {
  const { userId, redirectToSignIn } = await auth();
  if (!userId) {
    redirectToSignIn();
    // redirectToSignIn never returns, but TypeScript needs this
    throw new Error('Not authenticated');
  }
  return userId;
}

/**
 * Get the full Clerk user object for the current session.
 * Returns null if not authenticated.
 */
export async function getCurrentUser() {
  const user = await currentUser();
  if (!user) return null;

  return {
    id: user.id,
    email: user.emailAddresses[0]?.emailAddress ?? null,
    firstName: user.firstName,
    lastName: user.lastName,
    imageUrl: user.imageUrl,
    createdAt: user.createdAt,
  };
}

/**
 * Check if the current user has a specific role via Clerk metadata.
 */
export async function hasRole(role: string): Promise<boolean> {
  const { sessionClaims } = await auth();
  const roles = (sessionClaims?.metadata as { roles?: string[] })?.roles;
  return roles?.includes(role) ?? false;
}
