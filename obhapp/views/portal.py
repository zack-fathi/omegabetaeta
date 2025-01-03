import uuid
import hashlib
import pathlib
import flask
import obhapp
from datetime import datetime
import obhapp.model
from obhapp.utils import line_int_to_line



@obhapp.app.route('/login/')
def show_login():
    if "user" in flask.session:
        return flask.redirect(flask.url_for("show_portal"))
    return flask.render_template("login.html")

@obhapp.app.route('/login/', methods=["POST"])
def login():
    username = flask.request.form["username"].lower()
    password = flask.request.form["password"]
    if not username or not password:
        flask.flash('Please provide both username and password', 'error')
        return flask.redirect(flask.url_for('show_login'))
    connection = obhapp.model.get_db()
    cur = connection.execute(
        "SELECT user_id, password, profile_picture, fullname FROM brothers "
        "WHERE username = ? ",
        (username,)
    )
    user = cur.fetchone()
    if user is None:
        flask.flash('User does not exist', 'error')
        return flask.redirect(flask.url_for('show_login'))

    alg, salt, stored_hash = user["password"].split('$')
    hash_obj = hashlib.new(alg)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    if password_hash == stored_hash:
        flask.session["user_id"] = user["user_id"]
        flask.session["pfp"] = user["profile_picture"]
        flask.session["name"] = user["fullname"]
    else:
        flask.flash('Incorrect password', 'error')
        return flask.redirect(flask.url_for('show_login'))
    return flask.redirect(flask.request.args.get('target'))

@obhapp.app.route('/portal/')
def show_portal():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    
    return flask.render_template("portal_index.html")


@obhapp.app.route('/portal/account/', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in flask.session:
        return flask.redirect(flask.url_for('login'))

    user_id = flask.session['user_id']
    con = obhapp.model.get_db()

    if flask.request.method == 'POST':
        # Get the form data
        new_username = flask.request.form['username']
        fullname = flask.request.form['fullname']
        major = flask.request.form['major']
        job = flask.request.form['job']
        desc = flask.request.form['desc']
        contacts = flask.request.form['contacts']
        grad_time = flask.request.form['grad_time']
        active = flask.request.form.get('active', 0)

        file = flask.request.files.get("profile_picture")
        print(flask.request.files)
        print(file)
        print(flask.request.form['existing_profile_picture'])
        if file:
            filename = file.filename
            print("img: ",filename)
            stem = uuid.uuid4().hex
            suffix = pathlib.Path(filename).suffix.lower()
            uuid_basename = f"{stem}{suffix}"
            path = obhapp.app.config["UPLOAD_FOLDER"] / uuid_basename
            file.save(path)
        else:
            uuid_basename = flask.request.form['existing_profile_picture']

        # Update the user's information in the database
        con.execute('''
            UPDATE brothers SET username = ?, fullname = ?, profile_picture = ?, major = ?, job = ?, desc = ?, 
             contacts = ?, grad_time = ?, active = ? 
            WHERE user_id = ?
        ''', (new_username, fullname, uuid_basename, major, job, desc, contacts, grad_time, active, user_id))

        # TODO: Need to see if this is the correct way to update the change log
        con.execute(
            "INSERT INTO change_log(user_id, desc) "
            "VALUES(?, ?); ",
            (user_id, f"Changed account details (new username: {new_username})")
        )
        con.commit()

        # Update the session variables
        flask.session["pfp"] = uuid_basename
        flask.session["name"] = fullname

        return flask.redirect(flask.url_for('edit_profile'))

    # Fetch the user's current information
    cur = con.execute('SELECT * FROM brothers WHERE user_id = ?', (user_id,))
    brother = cur.fetchone()
    context = {"brother": brother}

    return flask.render_template('portal_account.html', **context)


@obhapp.app.route('/portal/change_password/', methods=['POST'])
def change_password():
    if 'user_id' not in flask.session:
        return flask.redirect(flask.url_for('login'))

    user_id = flask.session['user_id']
    current_password = flask.request.form['current_password']
    new_password = flask.request.form['new_password']
    confirm_new_password = flask.request.form['confirm_new_password']

    if new_password != confirm_new_password:
        return flask.jsonify({"error": "New passwords do not match."}), 400

    conn = obhapp.model.get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM brothers WHERE user_id = ?', (user_id,))
    brother = cursor.fetchone()

    algorithm, salt, stored_password_hash = brother['password'].split('$')
    hash_obj = hashlib.new(algorithm)
    hash_obj.update((salt + current_password).encode('utf-8'))

    if hash_obj.hexdigest() != stored_password_hash:
        return flask.jsonify({"error": "Current password is incorrect."}), 400

    new_salt = uuid.uuid4().hex
    new_hash_obj = hashlib.new(algorithm)
    new_hash_obj.update((new_salt + new_password).encode('utf-8'))
    new_password_hash = new_hash_obj.hexdigest()
    new_password_db_string = "$".join([algorithm, new_salt, new_password_hash])

    cursor.execute('UPDATE brothers SET password = ? WHERE user_id = ?', (new_password_db_string, user_id))
    conn.commit()

    cursor.execute(
            "INSERT INTO change_log(user_id, desc) "
            "VALUES(?, ?); ",
            (user_id, f"{flask.session['name']} changed password"),
        )
    conn.commit()



    return flask.jsonify({"success": "Password changed successfully."}), 200

@obhapp.app.route('/portal/directory/')
def show_portal_directory():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    user_id = flask.session['user_id']
    context = {"user_id": user_id}
    con = obhapp.model.get_db()
    cur = con.execute(
        "SELECT user_id, fullname, username, line, line_num, uniqname FROM brothers "
        "ORDER BY line ASC, line_num ASC;",
    )
    brothers = cur.fetchall()
    last_line = brothers[-1]["line"]
    line_dict = {}
    for i in range(int(last_line) + 1):
        line = line_int_to_line[str(i)]
        line_dict[line] = [brother for brother in brothers if brother["line"] == i]

    context["brothers"] = line_dict
    return flask.render_template("portal_directory.html", **context)

@obhapp.app.route('/portal/directory/<name>/')
def show_directory_brother(name):
    con = obhapp.model.get_db()
    cur = con.execute(
        "SELECT * FROM brothers "
        "WHERE username = ? ",
        (name, )
    )
    bro = cur.fetchone()
    bro["line_name"] = line_int_to_line[str(bro["line"])]
    # return bro

    bro['grad_time'] = datetime.strptime(bro['grad_time'], '%Y-%m').strftime('%B %Y') if bro['grad_time'] else 'N/A'
    return flask.render_template("portal_brother.html", **bro)

@obhapp.app.route('/portal/log/')
def show_portal_log():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    con = obhapp.model.get_db()
    cur = con.execute(
        "SELECT * FROM change_log "
        "ORDER BY id DESC "
    )
    log = cur.fetchall()
    context = {"log": log}
    return flask.render_template("portal_log.html", **context)

@obhapp.app.route('/portal/recruits/')
def show_portal_recruits():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    con = obhapp.model.get_db()

    # only show certain buttons if user has the right permissions
    cur = con.execute(
        "SELECT role_name FROM roles "
        "WHERE user_id = ? ",
        (flask.session["user_id"],)
    )

    # currently up to president
    role = cur.fetchone()
    can_change = False
    if role:
        role = role["role_name"]
        can_change = role in ["Admin", "President", "Director of Recruitment"]

    cur = con.execute(
        "SELECT fullname, uniqname, email, accept, line_num, lion_name, accept FROM recruits "
    )
    recruits = cur.fetchall()
    context = {"recruits": recruits}
    return flask.render_template("portal_recruits.html", **context, can_change=can_change)

@obhapp.app.route('/portal/recruits/accept', methods=['POST'])
def accept_recruit():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    uniqname = flask.request.json['id']
    line_num = flask.request.json['line_num']
    lion_name = flask.request.json['lion_name']
    con = obhapp.model.get_db()
    con.execute(
        "UPDATE recruits SET line_num = ?, lion_name = ?, accept = 1 WHERE uniqname = ?",
        (line_num, lion_name, uniqname)
    )
    con.execute(
        "INSERT INTO change_log(user_id, desc) "
        "VALUEs(?, ?) ",
        (flask.session["user_id"], f"Recruit {uniqname} accepted")
    )
    con.commit()
    return flask.jsonify(success=True)

@obhapp.app.route('/portal/recruits/unaccept', methods=['POST'])
def unaccept_recruit():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    uniqname = flask.request.json['id']
    con = obhapp.model.get_db()
    con.execute(
        "UPDATE recruits SET accept = 0 WHERE uniqname = ?",
        (uniqname,)
    )
    con.execute(
        "INSERT INTO change_log(user_id, desc) "
        "VALUES(?, ?)",
        (flask.session["user_id"], f"Recruit {uniqname} unaccepted")
    )
    con.commit()
    return flask.jsonify(success=True)

@obhapp.app.route('/portal/recruits/remove/', methods=['POST'])
def remove_recruit():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    uniqname = flask.request.json['id']
    con = obhapp.model.get_db()
    con.execute(
        "DELETE FROM recruits WHERE uniqname = ?",
        (uniqname,)
    )
    con.execute(
        "INSERT INTO change_log(user_id, desc) "
        "VALUES(?, ?) ",
        (flask.session["user_id"], f"Recruit {uniqname} deleted")
    )
    con.commit()
    return flask.jsonify(success=True)

@obhapp.app.route('/portal/recruits/move/', methods=['POST'])
def move_recruits():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    con = obhapp.model.get_db()
    cur = con.execute(
        "SELECT * FROM recruits "
        "WHERE accept = 1 "
    )
    rec = cur.fetchall()
    for recruit in rec:
        time_made = datetime.now()
        reference = datetime(2018, 1, 1)
        year_diff = (time_made.year - reference.year) - (1 if (time_made.month, time_made.day) < (reference.month, reference.day) else 0)
        line = year_diff
        cross_time = "SP' " + str(2018 + year_diff)
        username = recruit["fullname"].lower().replace(" ", "")
        counter = 0
        temp_user = username
        cur = con.execute(
            "SELECT username FROM brothers "
            "WHERE username = ? ",
            (username,)
        )
        while cur.fetchone():
            counter += 1
            temp_user = username + str(counter)
            cur = con.execute(
                "SELECT username FROM brothers "
                "WHERE username = ? ",
                (temp_user,)
            )
        username = temp_user

        algorithm = 'sha512'
        salt = uuid.uuid4().hex
        hash_obj = hashlib.new(algorithm)
        hash_obj.update((salt + "password").encode('utf-8'))
        password_hash = hash_obj.hexdigest()
        password_db_string = "$".join([algorithm, salt, password_hash])

        con.execute(
            "INSERT INTO brothers(username, password, uniqname, fullname, line, line_num, lion_name, cross_time, active) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?, 1); ",
            (username, password_db_string, recruit["uniqname"], recruit["fullname"], line, recruit["line_num"], recruit["lion_name"], cross_time)
        )
        con.execute(
            "INSERT INTO change_log(user_id, desc) "
            "VALUES(?, ?); ",
            (flask.session["user_id"], f"Recruit {recruit['uniqname']} moved to Brothers as {username}")
        )
        con.commit()

    con.execute(
        "DELETE FROM recruits WHERE accept = 1"
    )
    con.commit()

    return flask.jsonify(success=True)

@obhapp.app.route('/portal/logout/')
def logout():
    flask.session.clear()
    return flask.redirect(flask.url_for('show_index'))

@obhapp.app.route('/portal/upload/', methods=['GET', 'POST'])
def upload():
    if flask.request.method == 'POST':
        description = flask.request.form['description']
        file = flask.request.files['profile_picture']
        connection = obhapp.model.get_db()

        if file:
            filename = file.filename
            stem = uuid.uuid4().hex
            suffix = pathlib.Path(filename).suffix.lower()
            uuid_basename = f"{stem}{suffix}"
            path = obhapp.app.config['UPLOAD_FOLDER'] / uuid_basename
            file.save(path)
            # Save description and file path to the database if necessary

            curr = connection.execute(
                "INSERT INTO gallery(filename, desc) "
                "VALUES(?, ?) ",
                (uuid_basename, description)
            )

            return flask.redirect(flask.url_for('upload'))

    return flask.render_template('portal_upload.html')


def get_active_brothers():
    connection = obhapp.model.get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT user_id, fullname FROM brothers WHERE active = 1")
    brothers = cursor.fetchall()
    #print(brothers)
    return brothers

@obhapp.app.route('/portal/board/', methods=['GET', 'POST'])
def assign_roles():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    if flask.request.method == 'POST':
        # Handle role assignment logic
        role_assignments = flask.request.form.to_dict()
        print(role_assignments)
        connection = obhapp.model.get_db()
        cursor = connection.cursor()
        for role, user_id in role_assignments.items():
            if user_id:
                cursor.execute("UPDATE roles SET user_id = ? WHERE role_name = ?", (user_id, role))
        connection.commit()

        cursor.execute(
            "INSERT INTO change_log(user_id, desc) "
            "VALUES(?, ?); ",
            (flask.session["user_id"], f"{flask.session['name']} updated roles"),
        )

        connection.commit()

        return flask.redirect(flask.url_for('assign_roles'))

    connection = obhapp.model.get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT role_name, user_id FROM roles")
    roles = cursor.fetchall()
    for role in roles:
        cursor.execute("SELECT username FROM brothers WHERE user_id = ?", (role['user_id'],))
        role_user = cursor.fetchone()
        if role_user:
            role_user = role_user['username']
        role["username"] = role_user
    active_brothers = get_active_brothers()
    cursor.execute("SELECT role_name FROM roles WHERE user_id = ?", (flask.session['user_id'],))
    can_change = False
    current_role = cursor.fetchone()
    if current_role:
        current_role = current_role["role_name"]
        can_change = current_role == 'Admin' or current_role == 'President'
    return flask.render_template('portal_board.html', brothers=active_brothers, roles=roles, can_change=can_change)

@obhapp.app.route('/portal/messages/')
def show_messages():
    """Show the contact messages in the portal."""
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    connection = obhapp.model.get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM messages")
    messages = cursor.fetchall()
    return flask.render_template('portal_messages.html', messages=messages)