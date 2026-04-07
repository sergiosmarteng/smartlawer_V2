import Head from 'next/head';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import Layout from '../../components/layout';
import AuthGuard from '../../components/auth/AuthGuard';
import api from '../../lib/axios';

export default function AnalysisPage() {
  const router = useRouter();
  const { id } = router.query;

  const [analysis, setAnalysis] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;

    const fetchAnalysis = async () => {
      setIsLoading(true);
      setError('');
      try {
        const response = await api.get(`/analysis/${id}`);
        setAnalysis(response.data);
      } catch (err: any) {
        console.error('Error fetching analysis:', err);
        setError('Failed to load analysis data.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalysis();
  }, [id]);

  const handleDownloadTemplate = async () => {
    try {
      const response = await api.get(`/templates/${id}/generate`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Defense_Strategy_${id}.docx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Download error:', err);
      alert('Failed to generate template. Please try again.');
    }
  };

  return (
    <AuthGuard>
      <Layout>
        <Head>
          <title>AI Analysis - SmartLawer</title>
        </Head>
        
        <div className="bg-zinc-950 min-h-screen text-slate-300 py-10 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto space-y-8 animate-fade-in-up">
            
            {/* Header Content */}
            {isLoading ? (
              <div className="py-20 flex justify-center items-center">
                <div className="animate-pulse text-slate-400 tracking-widest uppercase font-light text-sm">Translating Legalese...</div>
              </div>
            ) : error ? (
              <div className="py-20 text-center text-rose-400 font-light">{error}</div>
            ) : !analysis ? (
              <div className="py-20 text-center text-slate-500 font-light tracking-wide">Analysis record not found.</div>
            ) : (
              <>
                <div className="flex flex-col md:flex-row justify-between md:items-end border-b border-zinc-800 pb-6">
                  <div>
                    <p className="text-sm font-medium text-blue-400 uppercase tracking-widest mb-2">LangChain Intelligence Panel</p>
                    <h1 className="text-3xl font-light text-slate-100 tracking-tight">
                      Analysis Report #{id}
                    </h1>
                    <p className="mt-2 text-sm text-zinc-500 font-light truncate max-w-xl">
                      Source: {analysis.documentName || analysis.title || 'Extracted Document'}
                    </p>
                  </div>
                  <div className="mt-6 md:mt-0">
                    {/* O botão reluzente final! */}
                    <button
                      onClick={handleDownloadTemplate}
                      className="relative group overflow-hidden px-8 py-3 rounded-lg flex items-center justify-center font-medium tracking-widest uppercase transition-all duration-300 transform hover:-translate-y-1"
                    >
                      <span className="absolute inset-0 bg-gradient-to-r from-blue-600 via-emerald-500 to-blue-600 opacity-80 group-hover:opacity-100 transition-opacity duration-300 animate-gradient-x shadow-[0_0_30px_rgba(59,130,246,0.5)] group-hover:shadow-[0_0_50px_rgba(16,185,129,0.8)]"></span>
                      <span className="absolute inset-0 bg-zinc-900 opacity-20 rounded-lg"></span>
                      <div className="relative flex items-center text-white drop-shadow-md">
                        <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                        Generate .DOCX Defense
                      </div>
                    </button>
                  </div>
                </div>

                {/* Split View */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  
                  {/* Left Column: Context */}
                  <div className="space-y-8">
                    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 shadow-xl">
                      <h2 className="text-lg font-medium text-slate-100 uppercase tracking-widest border-b border-zinc-800 pb-4 mb-6">Execution Summary</h2>
                      <p className="text-slate-400 font-light leading-relaxed">
                        {analysis.summary || 'Summary is still being compiled or was not provided.'}
                      </p>
                    </div>

                    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 shadow-xl">
                      <h2 className="text-lg font-medium text-slate-100 uppercase tracking-widest border-b border-zinc-800 pb-4 mb-6">Key Extracted Arguments</h2>
                      <ul className="space-y-4">
                        {(analysis.keyArguments || []).map((arg: string, idx: number) => (
                          <li key={idx} className="flex items-start">
                            <span className="flex-shrink-0 h-6 w-6 rounded-full bg-blue-900/40 border border-blue-800 flex items-center justify-center text-blue-400 text-xs mr-4 mt-0.5">{idx + 1}</span>
                            <p className="text-slate-400 font-light">{arg}</p>
                          </li>
                        ))}
                        {(!analysis.keyArguments || analysis.keyArguments.length === 0) && (
                          <p className="text-zinc-600 font-light italic">No arguments extracted.</p>
                        )}
                      </ul>
                    </div>
                  </div>

                  {/* Right Column: AI Output */}
                  <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 shadow-xl relative overflow-hidden group">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none group-hover:bg-blue-500/10 transition-colors duration-500"></div>
                    <h2 className="text-lg font-medium text-blue-400 uppercase tracking-widest flex items-center pb-4 mb-6 border-b border-zinc-800">
                      <svg className="w-5 h-5 mr-3 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                      AI Generated Defense Strategy
                    </h2>
                    <div className="prose prose-invert max-w-none">
                      <p className="text-slate-300 font-light leading-loose text-lg border-l-4 border-blue-600/50 pl-6 space-y-4 whitespace-pre-wrap">
                        {analysis.generatedDefenseStrategy || 'The AI Model has not formulated a defense strategy yet.'}
                      </p>
                    </div>

                    <div className="mt-12 p-6 bg-zinc-950/50 rounded-xl border border-zinc-800 border-dashed">
                      <p className="text-sm text-zinc-500 font-mono flex items-center">
                        <span className="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-ping"></span>
                        Model: OpenRouter / GPT-4 Turbo
                      </p>
                      <p className="text-sm text-zinc-600 font-mono mt-1 ml-4">
                        Status: Active | Trace ID: {analysis.id || id}
                      </p>
                    </div>
                  </div>

                </div>
              </>
            )}
          </div>
        </div>
      </Layout>
    </AuthGuard>
  );
}
