import Layout from '../components/layout';
import { useAuth } from '../components/auth/AuthProvider';
import Link from 'next/link';

export default function Home() {
  const { user, isLoading } = useAuth();

  return (
    <Layout>
      <div className="flex flex-col items-center justify-center min-h-[80vh] px-4 py-6 sm:px-0 bg-zinc-950 text-slate-200">
        <div className="text-center space-y-6 max-w-2xl">
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-slate-200 to-slate-400 mb-4 animate-fade-in-up">
            SmartLawer
          </h1>
          <p className="text-lg md:text-xl text-slate-400 font-light tracking-wide mb-8">
            An elegant, AI-driven legal intelligence platform.
          </p>

          {!isLoading && !user && (
            <div className="p-8 rounded-2xl bg-zinc-900 border border-zinc-800 shadow-2xl backdrop-blur-md">
              <h2 className="text-2xl font-semibold mb-6 text-slate-100 tracking-wide">
                Secure Access
              </h2>
              <Link
                href="/sign-in"
                className="inline-block w-full sm:w-auto px-8 py-3 text-sm font-medium tracking-widest uppercase transition-all duration-300 bg-slate-100 text-zinc-950 rounded hover:bg-white hover:shadow-[0_0_20px_rgba(255,255,255,0.3)] focus:outline-none focus:ring flex justify-center items-center"
              >
                Authenticate
              </Link>
            </div>
          )}

          {!isLoading && user && (
            <div className="p-8 rounded-2xl bg-zinc-900 border border-zinc-800 shadow-2xl backdrop-blur-md">
              <h2 className="text-2xl font-semibold mb-4 text-slate-100 tracking-wide">
                Welcome, {user.firstName || 'Esquire'}
              </h2>
              <p className="text-slate-400 mb-6">
                Your legal workspace is ready.
              </p>
              <Link
                href="/dashboard"
                className="inline-block w-full sm:w-auto px-8 py-3 text-sm font-medium tracking-widest uppercase transition-all duration-300 bg-transparent border border-slate-500 text-slate-300 rounded hover:text-white hover:border-white focus:outline-none focus:ring flex justify-center items-center"
              >
                Enter Dashboard
              </Link>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
