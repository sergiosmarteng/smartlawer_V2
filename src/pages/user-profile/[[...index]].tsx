import { UserProfile } from '@clerk/nextjs';
import Head from 'next/head';
import Layout from '../../components/layout';
import AuthGuard from '../../components/auth/AuthGuard';

export default function UserProfilePage() {
  return (
    <AuthGuard>
      <Layout>
        <Head>
          <title>Profile - SmartLawer</title>
        </Head>
        <div className="max-w-4xl mx-auto py-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">Your Profile</h1>
          <UserProfile
            path="/user-profile"
            routing="path"
            appearance={{
              elements: {
                rootBox: 'w-full',
                card: 'shadow-sm rounded-xl w-full',
              },
            }}
          />
        </div>
      </Layout>
    </AuthGuard>
  );
}
