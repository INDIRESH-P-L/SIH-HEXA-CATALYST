import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

import { Button, Card, ErrorNote, Field, inputClass } from '../components/common'
import { errorMessage } from '../lib/api'
import { useAuth } from '../lib/auth'

/** Seeded local accounts, listed so the demonstration does not need a crib sheet. */
const DEMO_ACCOUNTS = [
  { email: 'priya.sharma@mospi.gov.in', role: 'Statistical Officer — the demo officer' },
  { email: 'anand.desai@nssta.gov.in', role: 'Assistant Director (Training) — trainer' },
  { email: 'admin@mospi.gov.in', role: 'System Administrator — admin' },
]
const DEMO_PASSWORD = 'Demo@2026'

export default function Login() {
  const { signIn } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await signIn(email.trim(), password)
      navigate('/', { replace: true })
    } catch (caught) {
      setError(errorMessage(caught, 'Sign-in failed.'))
    } finally {
      setBusy(false)
    }
  }

  function useAccount(value: string) {
    setEmail(value)
    setPassword(DEMO_PASSWORD)
    setError(null)
  }

  return (
    <div className="flex min-h-full items-center justify-center bg-paper px-4 py-10">
      <div className="w-full max-w-md">
        <header className="mb-6">
          <h1 className="text-24 font-semibold text-ink">Skill Intelligence Platform</h1>
          <p className="mt-1 text-14 text-ink-2">
            Ministry of Statistics and Programme Implementation
          </p>
        </header>

        <Card>
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <Field id="email" label="Official email">
              <input
                id="email"
                type="email"
                autoComplete="username"
                required
                className={inputClass}
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </Field>

            <Field id="password" label="Password">
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                className={inputClass}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </Field>

            {error && <ErrorNote>{error}</ErrorNote>}

            <Button type="submit" variant="primary" loading={busy} className="w-full">
              Sign in
            </Button>
          </form>
        </Card>

        <Card className="mt-4" label="Seeded demo accounts">
          <ul className="space-y-2">
            {DEMO_ACCOUNTS.map((account) => (
              <li key={account.email}>
                <button
                  type="button"
                  onClick={() => useAccount(account.email)}
                  className="w-full rounded border border-rule px-3 py-2 text-left transition-colors hover:bg-surface-2"
                >
                  <span className="block font-mono text-12 text-ink">{account.email}</span>
                  <span className="block text-12 text-ink-2">{account.role}</span>
                </button>
              </li>
            ))}
          </ul>
          <p className="mt-3 font-mono text-11 text-ink-3">
            password: {DEMO_PASSWORD} · local auth mode
          </p>
        </Card>

        <p className="mt-4 max-w-prose text-12 leading-relaxed text-ink-3">
          Authentication runs through a single token-verification function, so replacing it with a
          government identity provider changes the issuer and claims mapping only. No government
          single sign-on is integrated in this prototype.
        </p>
      </div>
    </div>
  )
}
