
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
0:[
"Jad Elharake, Hareth",
],
1:[
"Yasser Abusabha, Aklaaf",
"Mohamad Awada, Haidar",
"Hassan Bazzi, Abbas",
"Marwan Bazzi, Furhud",
"Ali Darwiche, Hamza",
"Rachad Elghoul, Sarem",
"Islam Gellani, Usayd",
"Mohammed Hammoud, Feras",
"Labib Joumaa, Asrul",
"Mahdi Mazeh, Layth",
"Houd Mashrah, Baqer",
"Mohamed Mazeh, Shibel",
"Ahmad Saad, Bassel",
"Kassim Salami, Muthafar",
"Mohamad Saleh, Rebaal",
"Ryan Shami, Dhergham",
],
2:[
"X",
"Navid Fotovat, Aklaaf",
"Nader Nehme, Furhud",
"Haider Koussan, Bassel",
"Ziad Fehmi, Sarem",
"Nader Wehbi, Rebaal",
],
3:[
"Adam Chalak, Sarem",
"Hadi Allouch, Baqer",
"X",
"Sami Issa, Furhud",
"Akram Irshaid, Shibel",
"Sharif Salman, Asrul",
"Abdou Atoui, Abbas",
],
4:[
"Reda Mazeh, Furhud",
"Hussein Mustafa, Hamza",
"Hadi Fayad, Aklaaf",
"Joseph Haddad, Dhergham",
"Bashar Zeidan, Asrul",
"Adam Allouch, Muthafar",
"Ammar Saloum, Layth",
"Abbas Ajami, Feras",
"Ziad Harb, Rebaal",
"Abood Alsubee, Abbas",
],
5:[ 
"X",
"Jawad Alsahlani, Muthafar, jawadals",
"Zackery Fathi, Aklaaf, zfathi",
"Mohsen Najar, Furhud, mohsenn",
"Mohamman Alhameed, Asrul, mohamman",
"Ali Haidar, Usayd, alihaidr",
"Ahmad Sukhon, Baqer, asukhon",
"Omar Said, Shibel, saido",
"Wadih Elaridi, Haidar, welaridi",
"Zaid Omari, Sarem, zomari",
"Jaafar Abdallah, Feras, jhaafar",
],
6:[
"Ali Elhawli, Sarem, elhawli",
"Ahmed Elkhatib, Usayd, aelkhati",
"Adam Abduljabbar, Hamza, adamjbar",
"Saif Alesawy, Dhergham, salesawy",
"Ali Hammoud, Muthafar, alinabil",
"Ali Atoui, Feras, atouiali",
"Mohamed Najm, Layth, moenajm",
"Ibrahim Qamhieh, Asrul, qamhieh",
"Ali Ghoul, Rebaal, alighoul",
"Sajed Nehme, Baqer, shnehme",
"Ghassan Shohatee, Furhud, gsho",
"Hisham Irshaid, Haidar, hirshaid",
"Youssef Cherri, Bassel, ycherri",
],
7:[
"Haroon Sofyan, Sarem, hrsofyan",
"Amer Al-Ebidi, Furhud, amerale",
"Malek Husain, Usayd, malekh",
"Mohammed Alsaidi, Muthafar, mashaif",
"Bader Atoui, Feras, batoui",
"Adam Kasham, Bassel, adkasham",
"Mohamad-Ali Chahrour, Haidar, mchahrou",
"Zain Mohamad, Layth, zmohamad",
"Hamza Alnaib, Shibel, halnaib",
"Parth Gautam, Abbas, parthg",
],
8:[
"Nadir Alam, Usayd, nadira",
"Noah Qasim, Aklaaf, nzqasim",
"Kareem Serhane, Sarem, kserhane",
"Hadi Boussi, Asrul, hadibous",
"Yousif Ogaily, Feras, yoogaily",
"Abdullah Ouza, Haidar, abdullao",
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
