-- Migration: Move contacts from VARCHAR field to brother_contacts table
-- Run: sqlite3 var/obhapp.sqlite3 < sql/migrate_contacts.sql

CREATE TABLE IF NOT EXISTS brother_contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    contact_type TEXT NOT NULL DEFAULT 'other',
    contact_value TEXT NOT NULL,
    is_primary BIT DEFAULT 0,
    is_public BIT DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES brothers(user_id) ON DELETE CASCADE
);

-- Migrate existing contacts data (non-empty, non-N/A values) as 'other' type
INSERT INTO brother_contacts (user_id, contact_type, contact_value, is_primary, is_public, sort_order)
SELECT user_id, 'other', contacts, 1, 1, 0
FROM brothers
WHERE contacts IS NOT NULL AND contacts != 'N/A' AND contacts != '';
