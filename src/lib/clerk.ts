// Clerk environment variable keys used by @clerk/nextjs:
//   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY - required, set in .env.local
//   CLERK_SECRET_KEY                  - required, set in .env.local
//
// Route configuration for Clerk auth pages:
export const clerkRoutes = {
  signIn: '/sign-in',
  signUp: '/sign-up',
  afterSignIn: '/dashboard',
  afterSignUp: '/dashboard',
  userProfile: '/user-profile',
} as const;