import Layout from '../components/layout';
import { useAuth } from '../components/auth/AuthProvider';
import Link from 'next/link';
import Head from 'next/head';

const PROOFS = [
  {
    value: '106',
    label: 'testes automatizados verdes',
    detail: 'Cada entrega passa pela suíte completa antes de ir ao ar.',
  },
  {
    value: '10/10',
    label: 'no smoke de ponta a ponta',
    detail: 'Do envio do PDF à peça DOCX pronta para protocolar.',
  },
  {
    value: '32',
    label: 'itens no gate de qualidade do RAG',
    detail: 'Fidelidade média 0,969 com citação obrigatória por afirmação.',
  },
];

const CAPABILITIES = [
  {
    title: 'Análise com tese pronta',
    detail: 'Resumo dos fatos, pedidos, leis e teses preliminares e de mérito — estruturado para a sua revisão.',
  },
  {
    title: 'Chat com fonte citada',
    detail: 'Toda afirmação jurídica vem com a fonte clicável. Sem fundamento, a IA diz que não encontrou.',
  },
  {
    title: 'Peça em DOCX no seu modelo',
    detail: 'Suba o template do escritório, valide os campos e baixe a defesa formatada.',
  },
  {
    title: 'Trilha auditável',
    detail: 'Histórico de versões, retenção e auditoria consultável de cada evento da conta.',
  },
];

export default function Home() {
  const { user, isLoading } = useAuth();
  const userLabel = user?.username || user?.email || 'Doutor(a)';

  return (
    <Layout>
      <Head>
        <title>SmartLawer — Inteligência jurídica que entrega resultado sólido</title>
      </Head>
      <div className="bg-tribunal-texture px-4 py-10 text-slate-200 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl">
          <section className="grid items-center gap-10 py-10 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
            <div className="animate-fade-in-up">
              <p className="font-mono text-xs uppercase tracking-[0.32em] text-ouro-400">
                Advocacia brasileira · IA com fundamento
              </p>
              <h1 className="mt-5 font-display text-5xl font-black leading-[1.05] tracking-tight text-slate-50 md:text-7xl">
                O sistema <span className="text-ouro-300">fodão</span> da sua banca.
              </h1>
              <p className="mt-6 max-w-xl text-lg font-light leading-9 text-zinc-400">
                Petição entra, <strong className="font-semibold text-slate-100">resultado sólido</strong> sai:
                análise com tese, peça em DOCX no modelo do escritório e cada afirmação com a fonte citada.
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                {!isLoading && !user && (
                  <>
                    <Link
                      href="/sign-up"
                      className="inline-flex items-center justify-center rounded-full bg-ouro-500 px-8 py-3.5 text-sm font-bold uppercase tracking-[0.2em] text-tribunal-950 shadow-[0_0_32px_rgba(201,162,39,0.25)] transition-all hover:-translate-y-0.5 hover:bg-ouro-400"
                    >
                      Começar agora
                    </Link>
                    <Link
                      href="/sign-in"
                      className="inline-flex items-center justify-center rounded-full border border-zinc-700 px-8 py-3.5 text-sm font-medium uppercase tracking-[0.2em] text-slate-200 transition-colors hover:border-ouro-600/60 hover:text-ouro-200"
                    >
                      Entrar
                    </Link>
                  </>
                )}
                {!isLoading && user && (
                  <>
                    <p className="font-display text-2xl text-slate-100">
                      Bem-vindo(a) de volta, {userLabel}.
                    </p>
                    <Link
                      href="/dashboard"
                      className="inline-flex items-center justify-center rounded-full bg-ouro-500 px-8 py-3.5 text-sm font-bold uppercase tracking-[0.2em] text-tribunal-950 shadow-[0_0_32px_rgba(201,162,39,0.25)] transition-all hover:-translate-y-0.5 hover:bg-ouro-400"
                    >
                      Abrir meu painel
                    </Link>
                  </>
                )}
              </div>
            </div>

            <div className="grid gap-4">
              {PROOFS.map((proof, index) => (
                <div
                  key={proof.label}
                  style={{ animationDelay: `${index * 120}ms` }}
                  className="border-selo-ouro animate-fade-in-up rounded-r-[1.75rem] rounded-l-lg border border-zinc-800 border-l-0 bg-tribunal-900/80 p-6 shadow-2xl shadow-black/30"
                >
                  <p className="font-display text-5xl font-black tabular-nums text-ouro-300">
                    {proof.value}
                  </p>
                  <p className="mt-2 text-sm font-semibold uppercase tracking-[0.18em] text-slate-100">
                    {proof.label}
                  </p>
                  <p className="mt-1 text-sm leading-6 text-zinc-400">{proof.detail}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="mt-6 border-t border-zinc-800/80 py-12">
            <p className="font-mono text-xs uppercase tracking-[0.32em] text-ouro-500">
              O que o sistema entrega
            </p>
            <h2 className="mt-3 font-display text-3xl font-bold text-slate-50 sm:text-4xl">
              Tudo que a sua petição precisa, num só fluxo
            </h2>
            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              {CAPABILITIES.map((item) => (
                <div
                  key={item.title}
                  className="rounded-[1.75rem] border border-zinc-800 bg-tribunal-900/60 p-6 transition-colors hover:border-ouro-700/50"
                >
                  <h3 className="font-display text-xl font-bold text-ouro-200">{item.title}</h3>
                  <p className="mt-2 text-sm leading-7 text-zinc-400">{item.detail}</p>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </Layout>
  );
}
