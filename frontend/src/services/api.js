import axios from "axios";
import { getLocalTenantSlug } from "../lib/tenant";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";
const ACCESS_KEY = "be-wise-access-token";
const REFRESH_KEY = "be-wise-refresh-token";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

// Client séparé pour éviter qu'une requête de refresh déclenche elle-même
// l'interceptor de refresh et crée une boucle infinie.
const refreshClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

let refreshPromise = null;

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY);
}

export function storeAuth(data) {
  if (data?.access) localStorage.setItem(ACCESS_KEY, data.access);
  if (data?.refresh) localStorage.setItem(REFRESH_KEY, data.refresh);
}

export function clearAuth() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

function addTenantHeader(config) {
  // Uniquement utile avec Vite en local. En production le backend lit le Host.
  const tenantSlug = getLocalTenantSlug();
  if (tenantSlug) config.headers["X-Tenant-Slug"] = tenantSlug;
  return config;
}

api.interceptors.request.use((config) => {
  config.headers = config.headers || {};
  addTenantHeader(config);

  const url = config.url || "";
  const publicRequest =
    config.skipAuth ||
    url.startsWith("/public/") ||
    url === "/auth/login/";

  if (publicRequest) {
    config.skipAuth = true;
    config.skipAuthRefresh = true;
  }

  const token = getAccessToken();
  if (token && !config.skipAuth) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

async function refreshAccessToken() {
  const refresh = getRefreshToken();
  if (!refresh) throw new Error("No refresh token available");

  // Si 5 requêtes expirent au même moment, une seule requête de refresh part.
  if (!refreshPromise) {
    refreshPromise = refreshClient
      .post("/auth/refresh/", { refresh })
      .then(({ data }) => {
        storeAuth(data);
        return data.access;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

function expireSession() {
  clearAuth();
  window.dispatchEvent(new CustomEvent("be-wise-auth-expired"));
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const status = error?.response?.status;

    if (
      status !== 401 ||
      !original ||
      original._retry ||
      original.skipAuthRefresh ||
      !getRefreshToken()
    ) {
      return Promise.reject(error);
    }

    original._retry = true;

    try {
      const access = await refreshAccessToken();
      original.headers = original.headers || {};
      original.headers.Authorization = `Bearer ${access}`;
      addTenantHeader(original);
      return api(original);
    } catch (refreshError) {
      expireSession();
      return Promise.reject(refreshError);
    }
  }
);

export default api;
