import Head from 'next/head';
import LandingPage from '../components/landing/LandingPage';

export default function Home() {
  return (
    <>
      <Head>
        <title>SmartLawer — Mais estratégia. Menos trabalho repetitivo.</title>
        <meta name="description" content="Transforme petições em análises estruturadas, converse com seus documentos e prepare minutas em Word. Inteligência artificial a serviço da advocacia, com você no comando." key="description" />
        <link rel="canonical" href="https://smartlawer.com.br/" />
        <meta property="og:locale" content="pt_BR" />
        <meta property="og:type" content="website" />
        <meta property="og:site_name" content="SmartLawer" />
        <meta property="og:title" content="Seu talento é a estratégia. O trabalho pesado é nosso." />
        <meta property="og:description" content="Da petição à minuta: análise jurídica, chat com documentos e geração de DOCX em um só fluxo." />
        <meta property="og:url" content="https://smartlawer.com.br/" />
        <meta property="og:image" content="https://smartlawer.com.br/images/landing/justice-architecture.png" />
        <meta property="og:image:width" content="1536" />
        <meta property="og:image:height" content="1024" />
        <meta property="og:image:alt" content="Balança de latão entre mármore verde e travertino" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="theme-color" content="#112c25" />
      </Head>
      <LandingPage />
    </>
  );
}
