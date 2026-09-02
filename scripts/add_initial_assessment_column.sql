-- Migration: add initial_assessment_completed column to profiles
-- Run this once against the local or Supabase database.

ALTER TABLE profiles
    ADD COLUMN IF NOT EXISTS initial_assessment_completed BOOLEAN NOT NULL DEFAULT FALSE;

-- Existing demo users (already seeded) are treated as assessment-completed
-- so they can access the dashboard immediately without being gated.
UPDATE profiles SET initial_assessment_completed = TRUE
WHERE id IN (
    SELECT p.id FROM profiles p
    JOIN competency_evidence ce ON ce.user_id = p.id
    WHERE ce.source_type = 'assessment'
);
