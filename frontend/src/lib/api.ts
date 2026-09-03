/**
 * The single axios instance.
 *
 * The base URL comes from configuration, never a hard-coded origin, and the
 * bearer token is attached by an interceptor so no call site handles auth.
 * The browser only ever holds the user's own JWT: no service-role key and no
 * Groq key exists on this side of the wire.
 */
import axios, { AxiosError } from 'axios'

const TOKEN_KEY = 'sip.access_token'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
  headers: { 'Content-Type': 'application/json' },
  timeout: 120_000, // question generation legitimately takes a while
})

export function getToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) window.localStorage.setItem(TOKEN_KEY, token)
    else window.localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* private browsing: the session simply does not persist */
  }
}

api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      setToken(null)
      window.dispatchEvent(new CustomEvent('auth:unauthorized'))
    }
    return Promise.reject(error)
  },
)

/** The error shape the backend returns for every deliberate failure. */
export interface ApiErrorBody {
  code?: string
  message?: string
  detail?: unknown
}

export function errorMessage(error: unknown, fallback = 'Something went wrong.'): string {
  const axiosError = error as AxiosError<ApiErrorBody>
  const body = axiosError?.response?.data
  if (body && typeof body === 'object') {
    if (typeof body.message === 'string') return body.message
    if (typeof body.detail === 'string') return body.detail
  }
  if (axiosError?.message) return axiosError.message
  return fallback
}

export function isUnauthorised(error: unknown): boolean {
  return (error as AxiosError)?.response?.status === 401
}

export const API = {
  v1: (path: string) => `/api/v1${path}`,
}
