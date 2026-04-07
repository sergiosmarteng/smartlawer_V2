import Head from 'next/head';
import { useEffect, useState } from 'react';
import { useAuth } from '../components/auth/AuthProvider';
import Layout from '../components/layout';
import AuthGuard from '../components/auth/AuthGuard';
import Link from 'next/link';
import api from '../lib/axios';

interface Process {
  id: string | number;
  title: string;
  status: string;
  date?: string;
  created_at?: string;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [processes, setProcesses] = useState<Process[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchProcesses = async () => {
      try {
        const response = await api.get('/processes');
        if (Array.isArray(response.data)) {
          setProcesses(response.data);
        } else if (response.data?.items) {
          setProcesses(response.data.items);
        } else {
          setProcesses([]);
        }
      } catch (err: any) {
        console.error('Error fetching processes:', err);
        setError('Failed to load processes. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchProcesses();
  },[]);

  return (
    <AuthGuard>
      <Layout>
        <Head>
          <title>Dashboard - SmartLawer</title>
        </Head>
        <div className="bg-zinc-950 min-h-screen text-slate-300 py-10 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            {/* Header Section */}
            <div className="flex justify-between items-end border-b border-zinc-800 pb-6 mb-8 mt-12 animate-fade-in-up">
              <div>
                <h1 className="text-4xl font-light text-slate-100 tracking-tight">
                  Welcome, <span className="font-medium text-white">{user?.firstName || 'Back'}</span>
                </h1>
                <p className="mt-2 text-sm text-slate-400 font-light tracking-wide">
                  Your intelligent legal workspace is active.
                </p>
              </div>
              <div>
                <Link
                  href="/upload"
                  className="px-6 py-2.5 bg-slate-100 text-zinc-900 font-medium text-sm tracking-widest uppercase rounded shadow-[0_0_15px_rgba(255,255,255,0.1)] hover:shadow-[0_0_25px_rgba(255,255,255,0.3)] transition-all duration-300 flex items-center justify-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4"/></svg>
                  New Analysis
                </Link>
              </div>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-3 mb-12 animate-fade-in-up delay-100">
              <StatCard title="Active Analisys" value="12" />
              <StatCard title="Documents Processed" value="1,248" />
              <StatCard title="AI Accuracy Rate" value="98.5%" />
            </div>

            {/* Processes List */}
            <div className="animate-fade-in-up delay-200">
              <h2 className="text-xl font-medium text-slate-100 mb-6 tracking-wide">Recent Processes</h2>
              <div className="bg-zinc-900 shadow-2xl rounded-xl border border-zinc-800 overflow-hidden">
                {isLoading ? (
                  <div className="p-8 text-center text-slate-400 font-light tracking-wide animate-pulse">Loading recent processes...</div>
                ) : error ? (
                  <div className="p-8 text-center text-rose-400 font-light">{error}</div>
                ) : processes.length === 0 ? (
                  <div className="p-8 text-center text-slate-400 font-light">No processes found. Upload a legal document to begin analysis.</div>
                ) : (
                  <ul className="divide-y divide-zinc-800">
                    {processes.map((process, idx) => (
                      <li key={process.id} className="hover:bg-zinc-800/50 transition-colors duration-200">
                        <Link href={`/analysis/${process.id}`} className="block px-6 py-5">
                          <div className="flex items-center justify-between">
                            <p className="text-sm font-medium text-slate-200 truncate">{process.title}</p>
                            <div className="ml-2 flex-shrink-0 flex">
                              <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full tracking-wide ${
                                (process.status === 'Done' || process.status === 'SUCCESS' || process.status === 'COMPLETED') ? 'bg-emerald-900/40 text-emerald-300 border border-emerald-800' :
                                (process.status === 'Processing' || process.status === 'PENDING') ? 'bg-blue-900/40 text-blue-300 border border-blue-800' :
                                'bg-rose-900/40 text-rose-300 border border-rose-800'
                              }`}>
                                {process.status}
                              </span>
                            </div>
                          </div>
                          <div className="mt-2 sm:flex sm:justify-between">
                            <div className="sm:flex">
                              <p className="flex items-center text-sm text-zinc-500">
                                ID: {process.id}
                              </p>
                            </div>
                            <div className="mt-2 flex items-center text-sm text-zinc-500 sm:mt-0">
                              <p>Opened on <time dateTime={process.date || process.created_at}>{process.date || process.created_at}</time></p>
                            </div>
                          </div>
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        </div>
      </Layout>
    </AuthGuard>
  );
}

function StatCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="bg-zinc-900 overflow-hidden shadow-2xl rounded-xl border border-zinc-800 relative group cursor-pointer">
      <div className="absolute inset-0 bg-gradient-to-r from-zinc-800/0 via-zinc-800/10 to-zinc-800/0 transform -translate-x-full group-hover:animate-shimmer" />
      <div className="px-6 py-6 relative">
        <dt className="text-xs font-semibold text-zinc-500 uppercase tracking-widest truncate">{title}</dt>
        <dd className="mt-2 text-3xl font-light text-slate-200">{value}</dd>
      </div>
    </div>
  );
}
