import { AuthProvider } from '../components/auth/AuthProvider';
import type { AppProps } from 'next/app';
import Head from 'next/head';
import '../styles/globals.css';

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <Head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>SmartLawer</title>
      </Head>
      <Component {...pageProps} />
    </AuthProvider>
  );
}

