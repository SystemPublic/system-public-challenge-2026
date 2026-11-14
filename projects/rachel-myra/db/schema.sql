-- The Missing Label: local SQLite schema for LIVE demo state (spec §4.8).
--
-- Static data (patients, medications, questionnaire, trusted contacts) is NOT
-- copied here: it stays in data/processed/synthetic/ and is loaded by lib/patient.
-- This database only holds what changes during the demo: alerts sent, check-ins
-- tapped on the phone, the simulated push/SMS log, new sign-ups, and the
-- fast-forward clock. patient_id = the synthetic id (e.g. 'S01').
--
-- Applied automatically by web/src/lib/db.ts on first connection (idempotent).
-- Reset the demo: delete db/heat.sqlite* and reload.

PRAGMA foreign_keys = ON;

-- Clinician → patient alerts. One row per send (single or lasso batch).
CREATE TABLE IF NOT EXISTS alerts (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  health_system_id  TEXT NOT NULL DEFAULT 'sbh',
  patient_id        TEXT NOT NULL,
  kind              TEXT NOT NULL DEFAULT 'heat_safety', -- heat_safety | cooling_place | follow_up
  message           TEXT NOT NULL,
  language          TEXT NOT NULL DEFAULT 'en',
  channel           TEXT NOT NULL DEFAULT 'push+sms',    -- simulated in the demo
  status            TEXT NOT NULL DEFAULT 'sent',
    -- sent | acknowledged | escalated_contact | escalated_clinic | resolved
  wait_minutes      REAL,                                -- T_wait from lib/patient escalationPlan
  contact_id        TEXT,                                -- contact escalated to (contacts_routed.contact_id)
  scenario          TEXT NOT NULL DEFAULT 'replay',      -- which panel_scores_<scenario>.json the steps came from
  steps_done        INTEGER NOT NULL DEFAULT 0,          -- how many escalation.steps have fired
  sent_at           TEXT NOT NULL,                       -- demo time (ISO), see demo_clock
  ack_at            TEXT,
  escalated_at      TEXT,
  resolved_at       TEXT
);

-- Patient taps on the phone: "I'm OK" / "I feel unwell" / "No AC".
CREATE TABLE IF NOT EXISTS checkins (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_id  TEXT NOT NULL,
  alert_id    INTEGER REFERENCES alerts(id) ON DELETE SET NULL,
  status      TEXT NOT NULL,                             -- ok | unwell | no_ac
  note        TEXT,
  created_at  TEXT NOT NULL                              -- demo time (ISO)
);

-- Every simulated push / SMS / contact message (board + nerd stats show this log).
CREATE TABLE IF NOT EXISTS messages (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_id  TEXT,
  alert_id    INTEGER REFERENCES alerts(id) ON DELETE SET NULL,
  recipient   TEXT NOT NULL,                             -- patient | contact:<contact_id> | clinic
  channel     TEXT NOT NULL,                             -- push | sms | call_list
  body        TEXT NOT NULL,
  note        TEXT,                                      -- the escalation step action that produced it
  simulated   INTEGER NOT NULL DEFAULT 1,
  read_at     TEXT,                                      -- phone marks the banner as seen
  created_at  TEXT NOT NULL                              -- demo time (ISO)
);

-- Questionnaire answers submitted live from the phone (overrides the synthetic row).
CREATE TABLE IF NOT EXISTS questionnaire_responses (
  patient_id    TEXT PRIMARY KEY,
  answers_json  TEXT NOT NULL,                           -- same keys as synthetic/questionnaire.csv
  updated_at    TEXT NOT NULL
);

-- Demo clock: fast-forward offset so a 45-minute wait plays in seconds.
CREATE TABLE IF NOT EXISTS demo_clock (
  id              INTEGER PRIMARY KEY CHECK (id = 1),
  offset_minutes  REAL NOT NULL DEFAULT 0
);
INSERT OR IGNORE INTO demo_clock (id, offset_minutes) VALUES (1, 0);

CREATE INDEX IF NOT EXISTS idx_alerts_patient   ON alerts(patient_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status    ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_checkins_patient ON checkins(patient_id);
CREATE INDEX IF NOT EXISTS idx_messages_patient ON messages(patient_id);
