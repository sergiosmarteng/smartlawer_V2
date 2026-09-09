import { AuthProvider } from '../components/auth/AuthProvider';
import type { AppProps } from 'next/app';
import Head from 'next/head';
import '../styles/globals.css';
import { fontDisplay, fontMono, fontSans } from '../lib/fonts';

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <Head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>SmartLawer — Resultado sólido na advocacia</title>
      </Head>
      <div className={`${fontDisplay.variable} ${fontSans.variable} ${fontMono.variable}`}>
        <Component {...pageProps} />
      </div>
    </AuthProvider>
  );
}

