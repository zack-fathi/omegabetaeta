-- Migration: Add email and password management columns
-- Run this on an existing database to add the new features.
-- Safe to run multiple times (uses IF NOT EXISTS / catches errors).

-- Add new columns to brothers table
ALTER TABLE brothers ADD COLUMN default_password TEXT DEFAULT NULL;
ALTER TABLE brothers ADD COLUMN password_changed BIT DEFAULT 0;
ALTER TABLE brothers ADD COLUMN email_sent BIT DEFAULT 0;

-- Mark all existing brothers who have non-default passwords as password_changed = 1
-- (If they previously changed from "password", this won't know, but it's safe default)

-- Add reply columns to messages table
ALTER TABLE messages ADD COLUMN reply_text TEXT DEFAULT NULL;
ALTER TABLE messages ADD COLUMN replied_at DATETIME DEFAULT NULL;
ALTER TABLE messages ADD COLUMN replied_by INTEGER DEFAULT NULL;
