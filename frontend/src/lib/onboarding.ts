/**
 * Onboarding gate.
 *
 * Whether an officer has completed the wizard is read from the server, not
 * from browser storage: `Me.onboarded` is true when any competency evidence
 * exists for that user. The wizard's entire purpose is to write the first rows
 * into that ledger, so the ledger itself is the completion record.
 *
 * This matters because re-running the wizard is destructive. It appends a
 * fresh self-declaration for every competency at the cluster default, and the
 * `user_competency` view reads the latest row per (user, competency) — so a
 * second pass would supersede seeded baselines and real assessment results
 * with flat guesses at confidence 0.25. A per-browser flag would fire again on
 * a new device or a cleared cache; a server-side signal cannot.
 *
 * Trainers and administrators never see it. It is an officer's competency
 * self-assessment, and forcing an academy trainer through it would write 33
 * self-declared rows against an account that has no job-role expectations to
 * measure them against.
 */
import type { Me } from './types'

export function needsOnboarding(user: Me | null): boolean {
  if (!user) return false
  if (user.roles.includes('trainer') || user.roles.includes('admin')) return false
  return !user.onboarded
}
