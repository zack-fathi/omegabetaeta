
import uuid
import hashlib
import sqlite3
import secrets

DB_PATH = 'var/obhapp.sqlite3'

def line_to_cross_time(i):
    return "SP' 20" + str(18 + i)

line_int_to_line = {
    '0': 'Fraternal Father',
    '1': 'Founding Line',
    '2': 'Beta Line',
    '3': 'Gamma Line',
    '4': 'Delta Line',
    '5': 'Epsilon Line',
    '6': 'Zeta Line',
    '7': 'Eta Line',
    '8': 'Theta Line',
    '9': 'Iota Line',
    '10': 'Kappa Line',
    '11': 'Lambda Line',
    '12': 'Mu Line',
    '13': 'Nu Line',
    '14': 'Xi Line',
    '15': 'Omicron Line',
    '16': 'Pi Line',
    '17': 'Rho Line',
    '18': 'Sigma Line',
    '19': 'Tau Line',
    '20': 'Upsilon Line',
    '21': 'Phi Line',
    '22': 'Chi Line',
    '23': 'Psi Line',
    '24': 'Omega Line',    
}

bros = {
# ──────────────────────────────────────────────────────
# Replace the placeholder data below with real member info.
# Format: "Full Name, LionName" or "Full Name, LionName, uniqname"
# Use "X" for dropped/placeholder positions.
# ──────────────────────────────────────────────────────
0:[
"Example Father, Hareth",
],
1:[
"Brother One, Aklaaf",
"Brother Two, Haidar",
"Brother Three, Abbas",
],
2:[
"X",
"Brother Four, Aklaaf",
"Brother Five, Furhud",
],
}

# Build brother records
brothers = []
for key in bros.keys():
    ln = 0
    for bro in bros[key]:
        a = 0
        if key == 6 or key == 7 or key == 8:
            a = 1
        ln += 1
        if bro == "X":
            continue
        parts = bro.split(',')
        if len(parts) >= 2:
            full_name = parts[0].strip()
            lion = parts[1].strip()
            uniq = parts[2].strip() if len(parts) >= 3 else ""
            brothers.append({
                "u": uniq,
                "f": full_name,
                "l": key,
                "ln": ln,
                "lion": lion,
                "a": a
            })

# Connect to the database and look up lion_name_id mapping
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.execute("SELECT lion_name_id, name FROM lion_names")
lion_name_map = {row["name"]: row["lion_name_id"] for row in cur.fetchall()}

algorithm = 'sha512'

for b in brothers:
    # Generate random 8-digit default password
    default_pw = ''.join([str(secrets.randbelow(10)) for _ in range(8)])
    new_salt = uuid.uuid4().hex
    new_hash_obj = hashlib.new(algorithm)
    new_hash_obj.update((new_salt + default_pw).encode('utf-8'))
    new_password_hash = new_hash_obj.hexdigest()
    password_db = "$".join([algorithm, new_salt, new_password_hash])

    base_username = b["f"].lower().replace(" ", "")
    username = base_username
    counter = 0
    while True:
        existing = conn.execute(
            "SELECT username FROM brothers WHERE username = ?",
            (username,)
        ).fetchone()
        if not existing:
            break
        counter += 1
        username = base_username + str(counter)

    lion_name_id = lion_name_map.get(b["lion"])
    if lion_name_id is None:
        print(f"WARNING: Lion name '{b['lion']}' not found in lion_names table, skipping {b['f']}")
        continue

    line_name = line_int_to_line[str(b['l'])]
    cross = line_to_cross_time(b['l'])
    contact = f" Reach me at {b['u']}@umich.edu." if b['u'] else ""
    if b['l'] == 0:
        desc = f"{b['f']} — Fraternal Father of Omega Beta Eta.{contact}"
    else:
        desc = f"{b['f']}, {line_name} #{b['ln']}. Crossed {cross}.{contact}"

    conn.execute(
        "INSERT INTO brothers(username, password, default_password, password_changed, email_sent, "
        "uniqname, fullname, line, line_num, "
        "cross_time, lion_name_id, active, desc) "
        "VALUES(?, ?, ?, 0, 0, ?, ?, ?, ?, ?, ?, ?, ?)",
        (username, password_db, default_pw, b["u"], b["f"], b["l"], b["ln"],
         line_to_cross_time(b["l"]), lion_name_id, b["a"], desc)
    )

conn.commit()
conn.close()
print(f"Inserted {len(brothers)} brothers directly into {DB_PATH}")
