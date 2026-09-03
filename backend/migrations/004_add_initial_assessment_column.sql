ALTER TABLE profiles
    ADD COLUMN IF NOT EXISTS initial_assessment_completed BOOLEAN NOT NULL DEFAULT FALSE;

UPDATE profiles SET initial_assessment_completed = TRUE
WHERE id IN (
    SELECT p.id FROM profiles p
    JOIN competency_evidence ce ON ce.user_id = p.id
    WHERE ce.source_type = 'assessment'
);
