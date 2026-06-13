-- ============================================================
-- Medical CRM — Supabase Full Schema
-- Jalankan SQL ini di: Supabase Dashboard → SQL Editor → New Query
-- ============================================================

-- ──────────────────────────────────────────────────────────
-- TABEL: users
-- Menyimpan akun pengguna dengan role (admin/staff/viewer)
-- Password di-hash dengan bcrypt cost factor 12
-- ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              BIGSERIAL       PRIMARY KEY,
    username        TEXT            NOT NULL UNIQUE,
    password_bcrypt TEXT            NOT NULL,
    role            TEXT            NOT NULL CHECK (role IN ('admin', 'staff', 'viewer')),
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_full_access_users" ON users
    FOR ALL TO service_role USING (true) WITH CHECK (true);


-- ──────────────────────────────────────────────────────────
-- TABEL: patients
-- ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patients (
    id              BIGSERIAL       PRIMARY KEY,
    name            TEXT            NOT NULL,
    age             INTEGER         NOT NULL CHECK (age >= 0 AND age <= 150),
    chief_complaint TEXT            NOT NULL,
    pain_level      INTEGER         NOT NULL CHECK (pain_level >= 1 AND pain_level <= 10),
    triage_status   TEXT            NOT NULL CHECK (triage_status IN ('Kritis', 'Sedang', 'Ringan')),
    registered_at   TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    hospital_id     INTEGER         NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_patients_triage_status ON patients (triage_status);
CREATE INDEX IF NOT EXISTS idx_patients_registered_at ON patients (registered_at DESC);
CREATE INDEX IF NOT EXISTS idx_patients_hospital_id   ON patients (hospital_id);

ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_full_access_patients" ON patients
    FOR ALL TO service_role USING (true) WITH CHECK (true);


-- ──────────────────────────────────────────────────────────
-- SEED DATA: users
--
-- Password di bawah adalah bcrypt hash dari:
--   admin   → "BlueteamEAS2025!"
--   staff   → "StaffMedis2025!"
--   viewer  → "ViewerCRM2025!"
--
-- Untuk generate hash baru, jalankan di terminal:
--   python -c "import bcrypt; print(bcrypt.hashpw(b'PASSWORD', bcrypt.gensalt(12)).decode())"
-- ──────────────────────────────────────────────────────────
INSERT INTO users (username, password_bcrypt, role) VALUES
    (
        'admin',
        '$2b$12$Gr9hIUuKeir6krxqoaLkOeZYk0zQvKjejFAhb5VGCcmTcbxLcM.Tm',
        'admin'
    ),
    (
        'staff',
        '$2b$12$pmY.G81jG9hjVlqH4RlwjeoIzFjU4C0fTi31ozV/MKMSfLaFvQbki',
        'staff'
    ),
    (
        'viewer',
        '$2b$12$da1nfj6wvjWrdUAgknTIC.AsYhcgM11zFvNNZ/Ikyqn5GcvDR3mxC',
        'viewer'
    )
ON CONFLICT (username) DO NOTHING;

