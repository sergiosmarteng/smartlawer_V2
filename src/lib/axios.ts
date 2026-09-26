import axios from 'axios';

const baseURL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1').replace(/\/+$/, '');
const ACCESS_TOKEN_KEY = 'access_token';
const ACCESS_TOKEN_COOKIE = 'smartlawer_access_token';

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }

    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        document.cookie = `${ACCESS_TOKEN_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax`;
        window.location.href = '/sign-in';
      }
    }

    return Promise.reject(error);
  }
);

export function getApiErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }

    if (detail && typeof detail === 'object' && 'message' in detail) {
      const message = detail.message;
      if (typeof message === 'string' && message.trim()) {
        return message;
      }
    }

    if (Array.isArray(detail) && detail.length > 0) {
      const combinedMessage = detail
        .map((item) => {
          if (typeof item === 'string') {
            return item;
          }

          if (item && typeof item === 'object' && 'msg' in item) {
            return String(item.msg);
          }

          return null;
        })
        .filter(Boolean)
        .join(', ');

      if (combinedMessage) {
        return combinedMessage;
      }
    }

    const message = error.response?.data?.message;
    if (typeof message === 'string' && message.trim()) {
      return message;
    }

    if (error.message) {
      return error.message;
    }
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }

  return fallback;
}

export function normalizeApiPath(path: string) {
  if (!path) {
    return path;
  }

  const trimmedPath = path.trim();
  if (trimmedPath.startsWith(baseURL)) {
    return trimmedPath.slice(baseURL.length) || '/';
  }

  if (trimmedPath.startsWith('/api/v1/')) {
    return trimmedPath.slice('/api/v1'.length);
  }

  return trimmedPath;
}

/** Cliente da API V2 do dossiê (`/api/v2/...`). Mesmo auth do `api`. */
const baseURLv2 = baseURL.replace(/\/api\/v1\/?$/, '/api/v2');

export const apiV2 = axios.create({
  baseURL: baseURLv2,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiV2.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }

    return config;
  },
  (error) => Promise.reject(error)
);

export default api;
