#!/usr/bin/env python3
"""Migrate the live database to use a lion_names table with foreign keys.

This script:
1. Creates the lion_names table
2. Populates it from existing distinct lion_name values in brothers
3. Adds lion_name_id column to brothers and recruits
4. Populates the FK columns from the text values
5. Removes the old lion_name text columns

Run from the project root:
    python3 bin/migrate_lion_names.py
"""
import sqlite3
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'var', 'obhapp.sqlite3')

def migrate():
    db_path = os.path.abspath(DB_PATH)
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        sys.exit(1)

    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = OFF")
    cur = con.cursor()

    # Check if migration already done
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lion_names'")
    if cur.fetchone():
        print("lion_names table already exists. Migration may have already been run.")
        # Check if brothers still has old lion_name column
        cur.execute("PRAGMA table_info(brothers)")
        cols = [row[1] for row in cur.fetchall()]
        if 'lion_name' not in cols and 'lion_name_id' in cols:
            print("Migration already complete.")
            con.close()
            return
        print("Continuing migration...")
    else:
        # Step 1: Create lion_names table
        cur.execute("""
            CREATE TABLE lion_names(
                lion_name_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                meaning TEXT DEFAULT ''
            )
        """)
        print("Created lion_names table.")

    # Step 2: Populate from existing brothers
    cur.execute("SELECT DISTINCT lion_name FROM brothers WHERE lion_name IS NOT NULL AND lion_name != '' ORDER BY lion_name")
    names = [row[0] for row in cur.fetchall()]
    
    # Also get from recruits
    cur.execute("SELECT DISTINCT lion_name FROM recruits WHERE lion_name IS NOT NULL AND lion_name != '' ORDER BY lion_name")
    recruit_names = [row[0] for row in cur.fetchall()]
    all_names = sorted(set(names + recruit_names))
    
    for name in all_names:
        try:
            cur.execute("INSERT OR IGNORE INTO lion_names(name) VALUES(?)", (name,))
        except sqlite3.IntegrityError:
            pass
    con.commit()
    print(f"Inserted {len(all_names)} lion names: {all_names}")

    # Step 3 & 4: Rebuild brothers table with lion_name_id
    cur.execute("PRAGMA table_info(brothers)")
    cols = [row[1] for row in cur.fetchall()]
    
    if 'lion_name' in cols and 'lion_name_id' not in cols:
        # Rebuild brothers
        cur.execute("""
            CREATE TABLE brothers_new(
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(20) NOT NULL UNIQUE,
                uniqname VARCHAR(20) DEFAULT "N/A",
                fullname VARCHAR(40) NOT NULL,
                profile_picture VARCHAR(64) DEFAULT "default.jpg",
                password VARCHAR(128) DEFAULT "password",
                major VARCHAR(40) DEFAULT "N/A",
                job VARCHAR(40) DEFAULT "N/A",
                desc VARCHAR(256) DEFAULT "N/A",
                campus VARCHAR(40) DEFAULT "N/A",
                contacts VARCHAR(64) DEFAULT "N/A",
                cross_time VARCHAR(40) DEFAULT "N/A",
                grad_time DATE DEFAULT NULL,
                line INTEGER NOT NULL,
                line_num INTEGER NOT NULL,
                lion_name_id INTEGER,
                active BIT DEFAULT 0,
                FOREIGN KEY (lion_name_id) REFERENCES lion_names(lion_name_id)
            )
        """)
        cur.execute("""
            INSERT INTO brothers_new(user_id, username, uniqname, fullname, profile_picture,
                password, major, job, desc, campus, contacts, cross_time, grad_time,
                line, line_num, lion_name_id, active)
            SELECT b.user_id, b.username, b.uniqname, b.fullname, b.profile_picture,
                b.password, b.major, b.job, b.desc, b.campus, b.contacts, b.cross_time,
                b.grad_time, b.line, b.line_num, ln.lion_name_id, b.active
            FROM brothers b
            LEFT JOIN lion_names ln ON b.lion_name = ln.name
        """)
        cur.execute("DROP TABLE brothers")
        cur.execute("ALTER TABLE brothers_new RENAME TO brothers")
        print("Migrated brothers table.")
    else:
        print("Brothers table already migrated.")

    # Step 5: Rebuild recruits table with lion_name_id
    cur.execute("PRAGMA table_info(recruits)")
    rcols = [row[1] for row in cur.fetchall()]
    
    if 'lion_name' in rcols and 'lion_name_id' not in rcols:
        cur.execute("""
            CREATE TABLE recruits_new(
                uniqname VARCHAR(20) NOT NULL,
                fullname VARCHAR(40) NOT NULL,
                email VARCHAR(20) NOT NULL,
                campus VARCHAR(40) NOT NULL,
                line_num INTEGER,
                lion_name_id INTEGER,
                accept BIT DEFAULT 0,
                deleted BIT DEFAULT 0,
                PRIMARY KEY(uniqname),
                FOREIGN KEY (lion_name_id) REFERENCES lion_names(lion_name_id)
            )
        """)
        cur.execute("""
            INSERT INTO recruits_new(uniqname, fullname, email, campus, line_num,
                lion_name_id, accept, deleted)
            SELECT r.uniqname, r.fullname, r.email, r.campus, r.line_num,
                ln.lion_name_id, r.accept, r.deleted
            FROM recruits r
            LEFT JOIN lion_names ln ON r.lion_name = ln.name
        """)
        cur.execute("DROP TABLE recruits")
        cur.execute("ALTER TABLE recruits_new RENAME TO recruits")
        print("Migrated recruits table.")
    else:
        print("Recruits table already migrated.")

    con.commit()
    con.execute("PRAGMA foreign_keys = ON")
    
    # Verify
    cur.execute("SELECT * FROM lion_names ORDER BY lion_name_id")
    print("\nLion names in database:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} (meaning: {row[2] or 'not set'})")
    
    cur.execute("SELECT COUNT(*) FROM brothers WHERE lion_name_id IS NOT NULL")
    print(f"\nBrothers with lion_name_id set: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM brothers WHERE lion_name_id IS NULL")
    print(f"Brothers with lion_name_id NULL: {cur.fetchone()[0]}")

    con.close()
    print("\nMigration complete!")

if __name__ == '__main__':
    migrate()
