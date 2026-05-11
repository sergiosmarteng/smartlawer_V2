import { ReactNode } from 'react';

export const authConfig = {
  signInPath: '/sign-in',
  signUpPath: '/sign-up',
  userProfilePath: '/user-profile',
};

export default function SuperTokensProvider({ children }: { children: ReactNode }) {
  // Compatibility wrapper kept while older imports are phased out of the app.
  return <>{children}</>;
}
