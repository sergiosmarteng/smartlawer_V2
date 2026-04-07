import { ClerkProvider } from '@clerk/nextjs';
import type { AppProps } from 'next/app';
import Head from 'next/head';
import '../styles/globals.css';

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <ClerkProvider
      {...pageProps}
      appearance={{
        variables: {
          colorPrimary: '#2563eb',
          borderRadius: '0.5rem',
        },
      }}
    >
      <Head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>SmartLawer</title>
      </Head>
      <Component {...pageProps} />
    </ClerkProvider>
  );
}
