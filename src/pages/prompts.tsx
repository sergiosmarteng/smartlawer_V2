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
      setError(getApiErrorMessage(fetchError, 'Não foi possível carregar os perfis.'));
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
      setNotice('Perfil criado.');
      fetchProfiles();
    } catch (createError) {
      setError(getApiErrorMessage(createError, 'Não foi possível criar o perfil.'));
    } finally {
      setIsSaving(false);
    }
  };

  const handleSetDefault = async (id: string) => {
    setNotice('');
    setError('');

    try {
      await api.patch(`/prompts/${id}/default`);
      setNotice('Perfil padrão atualizado. Novos documentos usam essa orientação.');
      fetchProfiles();
    } catch (defaultError) {
      setError(getApiErrorMessage(defaultError, 'Não foi possível definir o padrão.'));
    }
  };

  const handleDelete = async (id: string) => {
    setNotice('');
    setError('');

    try {
      await api.delete(`/prompts/${id}`);
      setNotice('Perfil excluído.');
      fetchProfiles();
    } catch (deleteError) {
      setError(getApiErrorMessage(deleteError, 'Não foi possível excluir o perfil.'));
    }
  };

  return (
    <AuthGuard>
      <Layout>
        <Head>
          <title>Perfis de prompt - SmartLawer</title>
        </Head>

        <div className="min-h-[calc(100vh-4rem)] bg-papel px-4 py-10 text-tinta sm:px-6 lg:px-8">
          <div className="mx-auto max-w-5xl space-y-8">
            <section className="overflow-hidden rounded-[5px] border border-linha bg-white px-8 py-10 shadow-[0_4px_10px_rgba(41,69,50,0.05)] sm:px-10">
              <p className="font-mono text-[9px] uppercase tracking-[2.25px] text-latiim-texto">Ajustes da IA</p>
              <h1 className="mt-4 font-display text-3xl font-normal tracking-tight text-tinta sm:text-4xl">
                Perfis de prompt
              </h1>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-tinta-suave">
                Orientação extra que entra no comando do analisador. O perfil padrão vale para os
                documentos processados depois de definido; sem padrão, vale o comando original.
              </p>

              {error && (
                <p className="mt-4 rounded-[5px] border border-red-200 bg-red-50 px-5 py-3 text-sm text-red-700">
                  {error}
                </p>
              )}
              {notice && (
                <p className="mt-4 rounded-[5px] border border-green-800/25 bg-green-50 px-5 py-3 text-sm text-green-800">
                  {notice}
                </p>
              )}

              <div className="mt-6 grid gap-4 rounded-[5px] border border-linha bg-papel-alta p-6">
                <input
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Nome do perfil (ex.: Teses objetivas)"
                  maxLength={255}
                  className="rounded-[5px] border border-linha bg-white px-4 py-3 text-sm text-tinta outline-none placeholder:text-tinta-muda/60 focus:border-latiim"
                />
                <textarea
                  value={strategy}
                  onChange={(event) => setStrategy(event.target.value)}
                  placeholder="Orientação extra para o analisador (máx. 2000 caracteres)"
                  maxLength={2000}
                  rows={3}
                  className="rounded-[5px] border border-linha bg-white px-4 py-3 text-sm leading-6 text-tinta outline-none placeholder:text-tinta-muda/60 focus:border-latiim"
                />
                <div>
                  <button
                    type="button"
                    onClick={handleCreate}
                    disabled={!name.trim() || isSaving}
                    className="inline-flex items-center justify-center rounded-[5px] bg-tinta-profunda px-6 py-3 text-sm font-medium uppercase tracking-[0.2em] text-white transition-colors hover:bg-tinta disabled:cursor-not-allowed disabled:bg-papel-areia disabled:text-tinta-muda"
                  >
                    {isSaving ? 'Salvando...' : 'Criar perfil'}
                  </button>
                </div>
              </div>
            </section>

            <section className="overflow-hidden rounded-[5px] border border-linha bg-white px-8 py-8 shadow-[0_4px_10px_rgba(41,69,50,0.05)] sm:px-10">
              <h2 className="font-mono text-[9px] font-medium uppercase tracking-[2.25px] text-tinta-muda">
                Seus perfis ({isLoading ? '…' : profiles.length})
              </h2>
              {isLoading ? (
                <p className="mt-4 text-sm text-tinta-muda">Carregando…</p>
              ) : profiles.length === 0 ? (
                <p className="mt-4 text-sm leading-7 text-tinta-muda">
                  Nenhum perfil ainda. Crie acima para personalizar a IA.
                </p>
              ) : (
                <ul className="mt-4 space-y-4">
                  {profiles.map((profile) => (
                    <li
                      key={profile.id}
                      className="rounded-[5px] border border-linha bg-papel-alta p-5"
                    >
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                          <p className="text-base font-medium text-tinta">
                            {profile.name}
                            {profile.is_default && (
                              <span className="ml-3 rounded-[5px] border border-tinta-profunda/25 bg-tinta-profunda/10 px-3 py-1 text-xs uppercase tracking-[0.2em] text-tinta-profunda">
                                Padrão
                              </span>
                            )}
                          </p>
                          {profile.strategy_prompt && (
                            <p className="mt-2 text-sm leading-6 text-tinta-suave">{profile.strategy_prompt}</p>
                          )}
                        </div>
                        <div className="flex shrink-0 gap-2">
                          {!profile.is_default && (
                            <button
                              type="button"
                              onClick={() => handleSetDefault(profile.id)}
                              className="rounded-[5px] border border-linha bg-white px-4 py-2 text-sm text-tinta-suave transition-colors hover:border-latiim hover:text-tinta"
                            >
                              Tornar padrão
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => handleDelete(profile.id)}
                            className="rounded-[5px] border border-red-200 bg-white px-4 py-2 text-sm text-red-700 transition-colors hover:bg-red-50"
                          >
                            Excluir
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
