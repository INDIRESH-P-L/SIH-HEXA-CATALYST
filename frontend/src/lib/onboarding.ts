/**
 * Onboarding gate — client-side only.
 *
 * Whether a user has completed the initial wizard is stored in localStorage
 * keyed by user.id. The backend is the real source of truth (evidence ledger,
 * profile, recommendations). This flag is a pure UI guard: it prevents
 * re-showing the wizard to officers who have already been through it.
 *
 * Demo accounts (seeded at startup) are always considered onboarded.
 */

const ONBOARDED_KEY_PREFIX = 'sip_onboarded_'

/** Emails of pre-seeded demo accounts that should skip the wizard. */
const DEMO_EMAILS = new Set([
  'priya.sharma@mospi.gov.in',
  'anand.desai@nssta.gov.in',
  'admin@mospi.gov.in',
])

export function isOnboarded(userId: string, email?: string | null): boolean {
  if (email && DEMO_EMAILS.has(email)) return true
  try {
    return localStorage.getItem(ONBOARDED_KEY_PREFIX + userId) === '1'
  } catch {
    return true // If storage is unavailable, don't block access
  }
}

export function markOnboarded(userId: string): void {
  try {
    localStorage.setItem(ONBOARDED_KEY_PREFIX + userId, '1')
  } catch {
    // Silently ignore — the user still gets to the dashboard
  }
}
