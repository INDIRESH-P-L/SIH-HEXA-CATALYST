/**
 * Authentication context.
 *
 * Holds the current session in memory and mirrors the token to localStorage so
 * a refresh does not sign the officer out. Roles are displayed from the token
 * response, but every authorisation decision is made server-side — the backend
 * reads roles from the database on each request and never trusts the client.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { api, API, getToken, setToken } from './api'
import type { Me, Profile, TokenResponse } from './types'

interface AuthState {
  user: Me | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<Me>
  signOut: () => void
  /** Fold a saved profile back into the session so the shell renders it. */
  applyProfile: (profile: Profile) => void
  hasRole: (role: string) => boolean
  isTrainer: boolean
  isAdmin: boolean
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Me | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function restore() {
      if (!getToken()) {
        setLoading(false)
        return
      }
      try {
        const { data } = await api.get<Me>(API.v1('/auth/me'))
        if (!cancelled) setUser(data)
      } catch {
        setToken(null)
        if (!cancelled) setUser(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void restore()

    const handleUnauthorized = () => {
      if (!cancelled) {
        setUser(null)
        setToken(null)
      }
    }
    window.addEventListener('auth:unauthorized', handleUnauthorized)

    return () => {
      cancelled = true
      window.removeEventListener('auth:unauthorized', handleUnauthorized)
    }
  }, [])


  const signIn = useCallback(async (email: string, password: string) => {
    const { data } = await api.post<TokenResponse>(API.v1('/auth/login'), {
      email,
      password,
    })
    setToken(data.access_token)
    setUser(data.user)
    return data.user
  }, [])

  const signOut = useCallback(() => {
    setToken(null)
    setUser(null)
  }, [])

  const applyProfile = useCallback((profile: Profile) => {
    setUser((current) => (current ? { ...current, profile } : current))
  }, [])

  const value = useMemo<AuthState>(
    () => ({
      user,
      loading,
      signIn,
      signOut,
      applyProfile,
      hasRole: (role: string) => Boolean(user?.roles.includes(role)),
      isTrainer: Boolean(user?.roles.includes('trainer') || user?.roles.includes('admin')),
      isAdmin: Boolean(user?.roles.includes('admin')),
    }),
    [user, loading, signIn, signOut, applyProfile],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
