import { Fraunces, JetBrains_Mono, Sora } from 'next/font/google';

/**
 * Tipografia da identidade institucional SmartLawer.
 *
 * - Fraunces: serifada de autoridade p/ títulos e números de resultado.
 * - Sora: texto corrido com caráter, sem cair no Inter genérico.
 * - JetBrains Mono: etiquetas, prazos e IDs de processo.
 */
export const fontDisplay = Fraunces({
  subsets: ['latin'],
  variable: '--font-fraunces',
  weight: ['400', '500', '600', '700', '900'],
  display: 'swap',
});

export const fontSans = Sora({
  subsets: ['latin'],
  variable: '--font-sora',
  weight: ['300', '400', '500', '600', '700'],
  display: 'swap',
});

export const fontMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
  weight: ['400', '500', '600'],
  display: 'swap',
});
