"""Inject a test user for local development. Only runs when FLASK_ENV != production."""

import os
import sys
import uuid
import hashlib
import sqlite3

if os.environ.get('FLASK_ENV') == 'production':
    print("ERROR: This script must not be run in production.")
    sys.exit(1)

DB_PATH = 'var/obhapp.sqlite3'

USERNAME = 'jawadalsahlani'
PASSWORD = 'j12345'
FULLNAME = 'Jawad Alsahlani'
UNIQNAME = 'jawadals'

algorithm = 'sha512'
salt = uuid.uuid4().hex
hash_obj = hashlib.new(algorithm)
hash_obj.update((salt + PASSWORD).encode('utf-8'))
password_db = "$".join([algorithm, salt, hash_obj.hexdigest()])

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Check if user already exists
existing = conn.execute(
    "SELECT user_id FROM brothers WHERE username = ?", (USERNAME,)
).fetchone()

if existing:
    print(f"Test user '{USERNAME}' already exists (user_id={existing['user_id']}). Skipping.")
    conn.close()
    sys.exit(0)

# Use the first lion_name as a placeholder
lion = conn.execute("SELECT lion_name_id FROM lion_names LIMIT 1").fetchone()
lion_name_id = lion["lion_name_id"] if lion else None

conn.execute(
    "INSERT INTO brothers(username, password, password_changed, email_sent, "
    "uniqname, fullname, line, line_num, lion_name_id, active, desc) "
    "VALUES(?, ?, 1, 0, ?, ?, 1, 1, ?, 1, ?)",
    (USERNAME, password_db, UNIQNAME, FULLNAME, lion_name_id,
     f"{FULLNAME} — test account for local development.")
)

user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

# Give Admin role so all features are accessible during testing
conn.execute(
    "UPDATE roles SET user_id = ? WHERE role_name = 'Admin' AND user_id IS NULL",
    (user_id,)
)

conn.commit()
conn.close()
print(f"Inserted test user '{USERNAME}' (user_id={user_id}) into {DB_PATH}")
