import Head from 'next/head';
import { useUser } from '@clerk/nextjs';
import Layout from '../components/layout';
import AuthGuard from '../components/auth/AuthGuard';

export default function DashboardPage() {
  const { user } = useUser();

  return (
    <AuthGuard>
      <Layout>
        <Head>
          <title>Dashboard - SmartLawer</title>
        </Head>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back{user?.firstName ? `, ${user.firstName}` : ''}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Here is an overview of your legal workspace.
          </p>

          <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            <StatCard title="Active Cases" value="--" />
            <StatCard title="Documents" value="--" />
            <StatCard title="Upcoming Deadlines" value="--" />
          </div>
        </div>
      </Layout>
    </AuthGuard>
  );
}

function StatCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-200">
      <div className="px-4 py-5 sm:p-6">
        <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
        <dd className="mt-1 text-3xl font-semibold text-gray-900">{value}</dd>
      </div>
    </div>
  );
}
