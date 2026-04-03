-- Migration: Replace "N/A" default values with empty strings
-- Run: sqlite3 var/obhapp.sqlite3 < sql/migrate_na_to_empty.sql

UPDATE brothers SET uniqname = '' WHERE uniqname = 'N/A';
UPDATE brothers SET major = '' WHERE major = 'N/A';
UPDATE brothers SET job = '' WHERE job = 'N/A';
UPDATE brothers SET desc = '' WHERE desc = 'N/A';
UPDATE brothers SET campus = '' WHERE campus = 'N/A';
UPDATE brothers SET contacts = '' WHERE contacts = 'N/A';
UPDATE brothers SET cross_time = '' WHERE cross_time = 'N/A';
