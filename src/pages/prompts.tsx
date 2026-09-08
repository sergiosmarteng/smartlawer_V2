import Head from 'next/head';
import { useCallback, useEffect, useState } from 'react';
import AuthGuard from '../components/auth/AuthGuard';
import Layout from '../components/layout';
import api, { getApiErrorMessage } from '../lib/axios';
import type { PromptProfile } from '../types/workflow';

/**
 * Minimal prompt-profile manager (C3/BL-020): list, create, set default,
 * delete. The default profile's guidance is prepended to the analyzer
 * prompt for subsequently processed documents.
 */
export default function PromptsPage() {
  const [profiles, setProfiles] = useState<PromptProfile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [name, setName] = useState('');
  const [strategy, setStrategy] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');

  const fetchProfiles = useCallback(async () => {
    try {
      const response = await api.get<PromptProfile[]>('/prompts');
      setProfiles(Array.isArray(response.data) ? response.data : []);
    } catch (fetchError) {
      setError(getApiErrorMessage(fetchError, 'Failed to load prompt profiles.'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProfiles();
  }, [fetchProfiles]);

  const handleCreate = async () => {
    if (!name.trim() || isSaving) {
      return;
    }

    setIsSaving(true);
    setNotice('');
    setError('');

    try {
      await api.post('/prompts', { name: name.trim(), strategy_prompt: strategy });
      setName('');
      setStrategy('');
      setNotice('Profile created.');
      fetchProfiles();
    } catch (createError) {
      setError(getApiErrorMessage(createError, 'Failed to create the profile.'));
    } finally {
      setIsSaving(false);
    }
  };

  const handleSetDefault = async (id: string) => {
    setNotice('');
    setError('');

    try {
      await api.patch(`/prompts/${id}/default`);
      setNotice('Default profile updated. New documents will use its guidance.');
      fetchProfiles();
    } catch (defaultError) {
      setError(getApiErrorMessage(defaultError, 'Failed to set the default profile.'));
    }
  };

  const handleDelete = async (id: string) => {
    setNotice('');
    setError('');

    try {
      await api.delete(`/prompts/${id}`);
      setNotice('Profile deleted.');
      fetchProfiles();
    } catch (deleteError) {
      setError(getApiErrorMessage(deleteError, 'Failed to delete the profile.'));
    }
  };

  return (
    <AuthGuard>
      <Layout>
        <Head>
          <title>Prompt Profiles - SmartLawer</title>
        </Head>

        <div className="min-h-[calc(100vh-4rem)] bg-zinc-950 px-4 py-10 text-slate-300 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-5xl space-y-8">
            <section className="overflow-hidden rounded-[2rem] border border-zinc-800 bg-zinc-900 px-8 py-10 shadow-2xl shadow-black/20 sm:px-10">
              <p className="text-xs uppercase tracking-[0.32em] text-sky-300">AI run settings</p>
              <h1 className="mt-4 text-3xl font-light tracking-tight text-slate-100 sm:text-4xl">
                Prompt profiles
              </h1>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-zinc-400">
                Extra guidance prepended to the analyzer prompt. The default profile applies to
                documents processed after it is set; the built-in prompt stays untouched when no
                profile is default.
              </p>

              {error && (
                <p className="mt-4 rounded-2xl border border-rose-900/80 bg-rose-950/50 px-5 py-3 text-sm text-rose-200">
                  {error}
                </p>
              )}
              {notice && (
                <p className="mt-4 rounded-2xl border border-emerald-900/80 bg-emerald-950/40 px-5 py-3 text-sm text-emerald-200">
                  {notice}
                </p>
              )}

              <div className="mt-6 grid gap-4 rounded-[1.75rem] border border-zinc-800 bg-zinc-950/60 p-6">
                <input
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Profile name (e.g. Concise theses)"
                  maxLength={255}
                  className="rounded-2xl border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-slate-100 outline-none placeholder:text-zinc-600 focus:border-sky-500"
                />
                <textarea
                  value={strategy}
                  onChange={(event) => setStrategy(event.target.value)}
                  placeholder="Additional guidance for the analyzer (max 2000 chars)"
                  maxLength={2000}
                  rows={3}
                  className="rounded-2xl border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm leading-6 text-slate-100 outline-none placeholder:text-zinc-600 focus:border-sky-500"
                />
                <div>
                  <button
                    type="button"
                    onClick={handleCreate}
                    disabled={!name.trim() || isSaving}
                    className="inline-flex items-center justify-center rounded-full bg-slate-100 px-6 py-3 text-sm font-medium uppercase tracking-[0.24em] text-zinc-950 transition-all hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:bg-zinc-800 disabled:text-zinc-500"
                  >
                    {isSaving ? 'Saving...' : 'Create profile'}
                  </button>
                </div>
              </div>
            </section>

            <section className="overflow-hidden rounded-[2rem] border border-zinc-800 bg-zinc-900 px-8 py-8 shadow-2xl shadow-black/20 sm:px-10">
              <h2 className="text-sm font-medium uppercase tracking-[0.28em] text-zinc-300">
                Your profiles ({isLoading ? '…' : profiles.length})
              </h2>
              {isLoading ? (
                <p className="mt-4 text-sm text-zinc-500">Loading…</p>
              ) : profiles.length === 0 ? (
                <p className="mt-4 text-sm leading-7 text-zinc-500">
                  No profiles yet. Create one above to customize AI runs.
                </p>
              ) : (
                <ul className="mt-4 space-y-4">
                  {profiles.map((profile) => (
                    <li
                      key={profile.id}
                      className="rounded-[1.5rem] border border-zinc-800 bg-zinc-950/70 p-5"
                    >
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                          <p className="text-base font-medium text-slate-100">
                            {profile.name}
                            {profile.is_default && (
                              <span className="ml-3 rounded-full border border-emerald-800 bg-emerald-900/30 px-3 py-1 text-xs uppercase tracking-[0.2em] text-emerald-300">
                                Default
                              </span>
                            )}
                          </p>
                          {profile.strategy_prompt && (
                            <p className="mt-2 text-sm leading-6 text-zinc-400">{profile.strategy_prompt}</p>
                          )}
                        </div>
                        <div className="flex shrink-0 gap-2">
                          {!profile.is_default && (
                            <button
                              type="button"
                              onClick={() => handleSetDefault(profile.id)}
                              className="rounded-full border border-zinc-700 px-4 py-2 text-sm text-zinc-200 transition-colors hover:border-zinc-500 hover:bg-zinc-900"
                            >
                              Set default
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => handleDelete(profile.id)}
                            className="rounded-full border border-rose-900/80 px-4 py-2 text-sm text-rose-200 transition-colors hover:bg-rose-950/50"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </div>
      </Layout>
    </AuthGuard>
  );
}
