import { SignIn } from 'supertokens-auth-react';

export default function SuperSignInButton() {
  return (
    <SignIn
      appearance={{
        theme: 'supertokens',
        primaryColor: '#2563eb',
      }}
      className="bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded-lg shadow-md"
    >
      Sign In
    </SignIn>
  );
}