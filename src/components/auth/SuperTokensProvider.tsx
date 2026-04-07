import { SuperTokensConfig } from 'supertokens-auth-react/lib/build/recipe/session';

export const authConfig: SuperTokensConfig = {
  appInfo: {
    appName: 'SmartLawer_V2',
    apiDomain: process.env.NEXT_PUBLIC_SUPERTOKENS_API_DOMAIN || 'http://localhost:3000',
    websiteDomain: process.env.NEXT_PUBLIC_SUPERTOKENS_WEBSITE_DOMAIN || 'http://localhost:3000',
    apiBasePath: '/api/auth',
    websiteBasePath: '/auth',
  },
  recipeList: [],
};

export default function SuperTokensProvider({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}