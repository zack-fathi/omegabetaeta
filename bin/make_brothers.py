
import uuid
import hashlib

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
"Jad Elharake - Hareth",
],
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


brothers = []
for key in bros.keys():
    ln = 0
    for bro in bros[key]:
        a = 0
        if key == 5 or key == 6:
            a = 1
        ln += 1
        names = bro.replace('-', ' ').split()
        if len(names) == 3:
            brothers.append({
                "u": "",
                "f": names[0] + " " + names[1],
                "l": key,
                "ln": ln,
                "lion": names[2],
                "a": a
            })


# Define the path to the SQL file
sql_file_path = 'sql/insert_brothers.sql'

new_password = "password"
algorithm = 'sha512'

# Open the SQL file for writing
with open(sql_file_path, 'w') as file:
    for b in brothers:
        new_salt = uuid.uuid4().hex
        new_hash_obj = hashlib.new(algorithm)
        new_hash_obj.update((new_salt + new_password).encode('utf-8'))
        new_password_hash = new_hash_obj.hexdigest()
        new_password_db_string = "$".join([algorithm, new_salt, new_password_hash])

        username = b["f"].lower().replace(" ", "")

        desc = f"Hello, my name is {b['f']} and I am a brother of OBH.\n\n I crossed {line_to_cross_time(b['l'])} and am part of the {line_int_to_line[str(b['l'])]} as line number {b['ln']}.\n You can contact me at {b['u']}@umich.edu for further questions."

        # Create the SQL insert statement
        sql = (
            "INSERT INTO brothers(username, password, uniqname, fullname, line, line_num, cross_time, lion_name, active, desc) "
            f'VALUES("{username}", "{new_password_db_string}", "{b["u"]}", "{b["f"]}", {b["l"]}, {b["ln"]}, "{line_to_cross_time(b["l"])}", "{b["lion"]}", {b["a"]}, "{desc}");\n'

        )

        # Write the SQL statement to the file
        file.write(sql)

print(f"SQL insert statements have been written to {sql_file_path}")
