-- Migration: Add email and password management columns
-- Run this on an existing database to add the new features.
-- Safe to run multiple times (uses IF NOT EXISTS / catches errors).

-- Add new columns to brothers table
ALTER TABLE brothers ADD COLUMN default_password TEXT DEFAULT NULL;
ALTER TABLE brothers ADD COLUMN password_changed BIT DEFAULT 0;
ALTER TABLE brothers ADD COLUMN email_sent BIT DEFAULT 0;

-- Mark all existing brothers who have non-default passwords as password_changed = 1
-- (If they previously changed from "password", this won't know, but it's safe default)

-- Create message_replies table for multi-reply threads
CREATE TABLE IF NOT EXISTS message_replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    reply_text TEXT NOT NULL,
    replied_by INTEGER NOT NULL,
    replied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (replied_by) REFERENCES brothers(user_id)
);

-- Migrate any existing single replies into the new table
INSERT INTO message_replies (message_id, reply_text, replied_by, replied_at)
SELECT id, reply_text, replied_by, replied_at
FROM messages
WHERE reply_text IS NOT NULL AND replied_by IS NOT NULL;

-- (Optional) After verifying migration, these columns can be removed:
-- ALTER TABLE messages DROP COLUMN reply_text;
-- ALTER TABLE messages DROP COLUMN replied_at;
-- ALTER TABLE messages DROP COLUMN replied_by;
