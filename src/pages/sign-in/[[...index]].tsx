import { SignIn } from '@clerk/nextjs';
import Head from 'next/head';

export default function SignInPage() {
  return (
    <>
      <Head>
        <title>Sign In - SmartLawer</title>
      </Head>
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-gray-900">SmartLawer</h1>
            <p className="mt-2 text-sm text-gray-600">
              Sign in to access your legal workspace
            </p>
          </div>
          <SignIn
            path="/sign-in"
            routing="path"
            signUpUrl="/sign-up"
            afterSignInUrl="/dashboard"
            appearance={{
              elements: {
                rootBox: 'mx-auto',
                card: 'shadow-md rounded-xl',
              },
            }}
          />
        </div>
      </div>
    </>
  );
}
