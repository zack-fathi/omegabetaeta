
import obhapp
import uuid
import hashlib

def line_to_cross_time(i):
    return "SP' 20" + str(18 + i)

brothers = [
    {
        "u": "jawadals",
        "f": "Jawad Alsahlani",
        "l": 5,
        "ln": 2,
        "lion": "Muthafar",
        "a": 1
    },
]

bros = {
1:[
"Yasser Abusabha - Aklaaf",
"Mohamad Awada - Haidar",
"Hassan Bazzi - Abbas",
"Marwan Bazzi - Furhud",
"Ali Darwiche - Hamza",
"Rachad Elghoul - Sarem",
"Islam Gellani - Usayd",
"Mohammed Hammoud - Feras",
"Labib Joumaa - Asrul",
"Mahdi Mazeh - Layth",
"Houd Mashrah - Baqer",
"Mohamed Mazeh - Shibel",
"Ahmad Saad - Bassel",
"Kassim Salami - Muthafar",
"Mohamad Saleh - Rebaal",
"Ryan Shami - Dhergham",
],
2:[
"X",
"Navid Fotovat - Akklaf",
"Nader Nehme - Furhud",
"Haider Koussan - Bassel",
"Ziad Fehmi - Sarem",
"Nader Wehbi - Rebaal",
],
3:[
"Adam Chalak - Sarem",
"Hadi Allouch - Baqer",
"X",
"Sami Issa - Furhud",
"Akram Irshaid - Shibel",
"Sharif Salman - Asrul",
"Abdou Atoui - Abbas",
],
4:[
"Reda Mazeh - Furhud",
"Hussein Mustafa - Hamza",
"Hadi Fayad - Akklaf",
"Joseph Haddad - Dergham",
"Bashar Zeidan - Asrul",
"Adam Allouch - Muthafar",
"Ammar Saloum - Layth",
"Abbas Ajami - Feras",
"Ziad Harb - Rebaal",
"Abood Alsubee - Abbas",
],
5:[ 
"X",
"Jawad Alsahlani - Muthafar",
"Zackery Fathi - Aklaaf",
"Mohsen Najar - Farhud",
"Mohamman Alhameed - Asrul",
"Ali Haidar - Usayd",
"Ahmad Sukhon - Baqer",
"Omar Said - Shibel",
"Wadih Alradi - Haider",
"Zaid Omari - Sarem",
"Jaafar Abdallah - Feras",
],
6:[
"Ali Elhawli- Sarem",
"Ahmad Elkhatib- Usayd",
"Adam Abduljabbar- Hamza",
"Saif Alesawy- Dhergham",
"Ali Hammoud- Muthafar",
"Ali Atoui- Feras",
"Mohamed Najm- Laith",
"Ibrahim Qamhieh-Asrul",
"Ali Ghoul-Rebal",
"Sajed Nehme- Baqer",
"Ghassan Shohatee- Farhud",
"Hisham Irshaid- Haidar",
"Youssef Cherri- Bassel",
],
}

for key in bros.keys():
    ln = 0
    for bro in bros[key]:
        a = 0
        if key == 5 or key == 6:
            a = 1
        ln += 1
        names = bro.replace('-', '').split()
        brothers.append({
            "u": "",
            "f": names[0] + " " + names[1],
            "l": key,
            "ln": ln,
            "lion": names[2],
            "a": a
        })


con = obhapp.model.get_db()

new_password = "password"
algorithm = 'sha512'
for b in brothers:
    new_salt = uuid.uuid4().hex
    new_hash_obj = hashlib.new(algorithm)
    new_hash_obj.update((new_salt + new_password).encode('utf-8'))
    new_password_hash = new_hash_obj.hexdigest()
    new_password_db_string = "$".join([algorithm, new_salt, new_password_hash])

    username = b["fullname"].lower().replace(" ", "")

    con.execute(
        "INSERT INTO brothers(username, password, uniqname, fullname, line, line_num, cross_time, lion_name, active) "
        "VALUES(?, ?, ?, ?, ?, ?, ?) ",
        (username, new_password_db_string, b["u"], b["f"], b["l"], b["ln"], line_to_cross_time(b['l']), b["lion"], b["a"])
    )
    con.commit()
