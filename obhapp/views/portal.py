import uuid
import pathlib
import flask
import obhapp
import datetime
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
        "SELECT password, profile_picture, fullname FROM brothers "
        "WHERE uniqname = ? OR name = ?",
        (username, username)
    )
    pw = cur.fetchone()
    if pw is None:
        flask.flash('User does not exist', 'error')
        return flask.redirect(flask.url_for('show_login'))
    stored_pw = pw["password"]
    # alg, salt, stored_hash = stored_pw.split('$')
    # hash_obj = hashlib.new(alg)
    # password_salted = salt + password
    # hash_obj.update(password_salted.encode('utf-8'))
    # password_hash = hash_obj.hexdigest()
    # if password_hash == stored_hash:
    #     flask.session["user"] = username
    if stored_pw == password:
        flask.session["user"] = username
        flask.session["pfp"] = pw["profile_picture"]
        flask.session["name"] = pw["fullname"]
    else:
        flask.flash('Incorrect password', 'error')
        return flask.redirect(flask.url_for('show_login'))
    return flask.redirect(flask.request.args.get('target'))


@obhapp.app.route('/portal/')
def show_portal():
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    return flask.render_template("portal_index.html")



@obhapp.app.route('/portal/account/', methods=['GET', 'POST'])
def edit_profile():
    # if 'username' not in flask.session:
    #     return flask.redirect(flask.url_for('login'))
    
    username = flask.session['user']
    con = obhapp.model.get_db()

    if flask.request.method == 'POST':
        # Get the form data
        fullname = flask.request.form['fullname']
        password = flask.request.form['password']
        major = flask.request.form['major']
        job = flask.request.form['job']
        desc = flask.request.form['desc']
        campus = flask.request.form['campus']
        contacts = flask.request.form['contacts']
        cross_time = flask.request.form['cross_time']
        grad_time = flask.request.form['grad_time']
        line = flask.request.form['line']
        line_num = flask.request.form['line_num']
        lion_name = flask.request.form['lion_name']
        active = flask.request.form.get('active', 0)

        file = flask.request.files["profile_picture"]
        if not file:
            flask.abort(400)

        filename = file.filename
        stem = uuid.uuid4().hex
        suffix = pathlib.Path(filename).suffix.lower()
        uuid_basename = f"{stem}{suffix}"
        path = obhapp.app.config["UPLOAD_FOLDER"]/uuid_basename
        file.save(path)

        print("Updating profile for:", username)  # Debug statement
        print("Form data:", fullname, uuid_basename, password, major, job, desc, campus, contacts, cross_time, grad_time, line, line_num, lion_name, active)  # Debug statement
        
        # Update the user's information in the database
        con.execute('''
            UPDATE brothers SET fullname = ?, profile_picture = ?, password = ?, major = ?, job = ?, desc = ?, 
            campus = ?, contacts = ?, cross_time = ?, grad_time = ?, line = ?, line_num = ?, lion_name = ?, active = ? 
            WHERE name = ? OR uniqname = ?
        ''', (fullname, uuid_basename, password, major, job, desc, campus, contacts, cross_time, grad_time, line, line_num, lion_name, active, username, username))
        
        con.commit()
        return flask.redirect(flask.url_for('edit_profile'))

    # Fetch the user's current information
    cur = con.execute('SELECT * FROM brothers WHERE name = ? OR uniqname = ?', (username, username))
    brother = cur.fetchone()
    context = {"brother": brother}

    print("Fetched brother data:", brother)  # Debug statement

    return flask.render_template('portal_account.html', **context)



@obhapp.app.route('/portal/directory/')
def show_portal_directory():
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    user = flask.session['user']
    context = {"user": user}
    con = obhapp.model.get_db()
    cur = con.execute(
        "SELECT fullname, name, line, line_num, uniqname FROM brothers "
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


@obhapp.app.route('/portal/log/')
def show_portal_log():
    if "user" not in flask.session:
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
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    con = obhapp.model.get_db()
    cur = con.execute(
        "SELECT fullname, uniqname, email, accept, line_num, lion_name FROM recruits "
    )
    recruits = cur.fetchall()
    context = {"recruits": recruits}
    return flask.render_template("portal_recruits.html", **context)


@obhapp.app.route('/portal/recruits/accept', methods=['POST'])
def accept_recruit():
    if "user" not in flask.session:
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
        "INSERT INTO change_log(username, desc) "
        "VALUEs(?, ?) ",
        (flask.session["user"], f"Recruit {uniqname} accepted")
    )
    con.commit()
    con.commit()
    return flask.jsonify(success=True)

@obhapp.app.route('/portal/recruits/remove/', methods=['POST'])
def remove_recruit():
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    uniqname = flask.request.json['id']
    con = obhapp.model.get_db()
    con.execute(
        "DELETE FROM recruits WHERE uniqname = ?",
        (uniqname,)
    )
    con.execute(
        "INSERT INTO change_log(username, desc) "
        "VALUES(?, ?) ",
        (flask.session["user"], f"Recruit {uniqname} deleted")
    )
    con.commit()
    return flask.jsonify(success=True)

@obhapp.app.route('/portal/recruits/move/', methods=['POST'])
def move_recruits():
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    con = obhapp.model.get_db()
    cur = con.execute(
        "SELECT * FROM recruits "
        "WHERE accept = 1 "
    )
    rec = cur.fetchall()
    for recruit in rec:
        time_made = datetime.datetime.now()
        reference = datetime.datetime(2018, 1, 1)
        year_diff = (time_made.year - reference.year) - (1 if (time_made.month, time_made.day) < (reference.month, reference.day) else 0)
        line = year_diff
        cross_time = "SP' " + str(2018 + year_diff)
        name = recruit["fullname"].lower().replace(" ", "")
        con.execute(
            "INSERT INTO brothers(name, uniqname, fullname, line, line_num, lion_name, cross_time, active) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, 1); ",
            (name, recruit["uniqname"], recruit["fullname"], line, recruit["line_num"], recruit["lion_name"], cross_time)
        )
        con.execute(
            "INSERT INTO change_log(username, desc) "
            "VALUES(?, ?); ",
            (flask.session["user"], f"Recruit {name} moved to Brothers")
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

