import { SignUp } from '@clerk/nextjs';
import Head from 'next/head';

export default function SignUpPage() {
  return (
    <>
      <Head>
        <title>Sign Up - SmartLawer</title>
      </Head>
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-gray-900">SmartLawer</h1>
            <p className="mt-2 text-sm text-gray-600">
              Create your account to get started
            </p>
          </div>
          <SignUp
            path="/sign-up"
            routing="path"
            signInUrl="/sign-in"
            afterSignUpUrl="/dashboard"
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
