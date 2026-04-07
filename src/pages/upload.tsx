import Head from 'next/head';
import { useState } from 'react';
import Layout from '../components/layout';
import AuthGuard from '../components/auth/AuthGuard';
import { useRouter } from 'next/router';
import api from '../lib/axios';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [statusMessage, setStatusMessage] = useState('Initializing upload...');
  const router = useRouter();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsProcessing(true);
    setProgress(10);
    setError('');
    setStatusMessage('Uploading document...');

    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const uploadRes = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      const taskId = uploadRes.data.task_id || uploadRes.data.id;
      if (!taskId) {
        throw new Error('No task ID received from server.');
      }
      
      setProgress(30);
      setStatusMessage('Document uploaded. Extracting and analyzing via AI...');
      
      const pollTask = async () => {
        try {
          const taskRes = await api.get(`/tasks/${taskId}`);
          const { status, progress: taskProgress, analysis_id } = taskRes.data;
          
          if (status === 'SUCCESS' || status === 'COMPLETED' || status === 'DONE') {
            setProgress(100);
            setStatusMessage('Analysis complete! Redirecting...');
            setTimeout(() => {
               router.push(`/analysis/${analysis_id || taskId}`);
            }, 1000);
          } else if (status === 'FAILURE' || status === 'FAILED' || status === 'ERROR') {
            setError('Task failed during AI analysis. Please try a different document.');
            setIsProcessing(false);
          } else {
             setProgress(prev => Math.min(prev + 5, 90)); 
             if (taskProgress) setProgress(taskProgress);
             
             setTimeout(pollTask, 2000);
          }
        } catch (pollErr) {
          console.error('Polling error:', pollErr);
          setError('Lost connection to analysis worker.');
          setIsProcessing(false);
        }
      };
      
      setTimeout(pollTask, 2000);
      
    } catch (err: any) {
      console.error('Upload error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to upload document.');
      setIsProcessing(false);
    }
  };

  return (
    <AuthGuard>
      <Layout>
        <Head>
          <title>Upload Legal Document - SmartLawer</title>
        </Head>
        
        <div className="bg-zinc-950 min-h-screen text-slate-300 py-10 px-4 flex items-center justify-center">
          <div className="max-w-3xl w-full bg-zinc-900 border border-zinc-800 rounded-3xl p-10 shadow-2xl animate-fade-in-up">
            
            <div className="mb-10 text-center">
              <h1 className="text-3xl font-light text-slate-100 tracking-tight mb-2">Initialize Analysis</h1>
              <p className="text-slate-400 font-light tracking-wide text-sm">
                Upload your legal document (PDF, DOCX) to initiate AI extraction & structuring.
              </p>
            </div>

            {!isProcessing ? (
              <div className="space-y-8">
                {error && <div className="text-rose-400 text-sm text-center bg-rose-950/50 p-3 rounded-lg border border-rose-900">{error}</div>}
                <div className="relative border-2 border-dashed border-zinc-700 hover:border-zinc-500 rounded-2xl p-16 text-center transition-all duration-300 group cursor-pointer bg-zinc-950">
                  <input
                    type="file"
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    onChange={handleFileChange}
                    accept=".pdf,.docx"
                  />
                  <div className="flex flex-col items-center justify-center space-y-4">
                    <svg className="w-12 h-12 text-zinc-600 group-hover:text-slate-300 transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
                    <div className="text-sm">
                      {file ? (
                        <p className="text-emerald-400 font-medium tracking-wide">{file.name}</p>
                      ) : (
                        <p className="font-medium text-slate-300">Click to upload or drag and drop</p>
                      )}
                      {!file && (
                        <p className="text-zinc-500 mt-1">PDF or DOCX up to 10MB</p>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={handleUpload}
                    disabled={!file}
                    className={`px-8 py-3 rounded text-sm font-medium tracking-widest uppercase transition-all duration-300 flex items-center
                      ${file 
                        ? 'bg-slate-100 text-zinc-900 shadow-[0_0_15px_rgba(255,255,255,0.1)] hover:shadow-[0_0_25px_rgba(255,255,255,0.3)]' 
                        : 'bg-zinc-800 text-zinc-600 cursor-not-allowed'
                      }`}
                  >
                    Start Processing
                    <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
                  </button>
                </div>
              </div>
            ) : (
              // Processing State mimicking Celery background task
              <div className="py-16 flex flex-col items-center justify-center space-y-8 animate-fade-in-up">
                <div className="relative w-32 h-32 flex items-center justify-center">
                  <div className="absolute inset-0 border-4 border-zinc-800 rounded-full"></div>
                  <div className="absolute inset-0 border-4 border-slate-200 rounded-full animate-spin border-t-transparent"></div>
                  <span className="text-xl font-light text-slate-200">{progress}%</span>
                </div>
                
                <div className="text-center space-y-2">
                  <p className="text-lg font-medium text-slate-100 uppercase tracking-widest animate-pulse">Running Celery Worker...</p>
                  <p className="text-sm text-slate-400">
                    {statusMessage}
                  </p>
                </div>
              </div>
            )}
            
          </div>
        </div>
      </Layout>
    </AuthGuard>
  );
}
