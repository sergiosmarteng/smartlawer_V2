import Layout from '../components/layout';
import { SignInButton, SignedIn, SignedOut } from '@clerk/nextjs';

export default function Home() {
  return (
    <Layout>
      <div className="px-4 py-6 sm:px-0">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Welcome to SmartLawer_V2
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            A modern legal platform built with Next.js and Clerk authentication
          </p>

          <SignedOut>
            <div className="bg-blue-50 p-6 rounded-lg">
              <h2 className="text-xl font-semibold mb-4">
                Please sign in to access the platform
              </h2>
              <SignInButton />
            </div>
          </SignedOut>

          <SignedIn>
            <div className="bg-green-50 p-6 rounded-lg">
              <h2 className="text-xl font-semibold mb-4">
                Welcome back! You're signed in.
              </h2>
              <p className="text-gray-600">
                Navigate to other features or manage your account settings.
              </p>
            </div>
          </SignedIn>
        </div>
      </div>
    </Layout>
  );
}
