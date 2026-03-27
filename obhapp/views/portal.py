import uuid
import hashlib
import pathlib
import secrets
import flask
import obhapp
from datetime import datetime
import obhapp.model
from obhapp.utils import line_int_to_line
from obhapp.email_utils import (
    send_default_password_email,
    send_message_reply_email,
)


@obhapp.app.before_request
def check_forced_password_change():
    """Redirect to forced password change page if user hasn't changed default password."""
    if flask.session.get("force_password_change"):
        allowed_endpoints = {
            'force_change_password', 'logout', 'static', 'uploaded_file',
            'show_login', 'login', 'show_index',
        }
        if flask.request.endpoint and flask.request.endpoint not in allowed_endpoints:
            return flask.redirect(flask.url_for('force_change_password'))



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
        "SELECT user_id, password, profile_picture, fullname, password_changed FROM brothers "
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

    # If password hasn't been changed from default, force a change
    if not user["password_changed"]:
        flask.session["force_password_change"] = True
        return flask.redirect(flask.url_for('force_change_password'))

    target = flask.request.args.get('target', flask.url_for('show_portal'))
    return flask.redirect(target)

@obhapp.app.route('/portal/')
def show_portal():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    if flask.session.get("force_password_change"):
        return flask.redirect(flask.url_for("force_change_password"))
    
    return flask.render_template("portal_index.html")


@obhapp.app.route('/portal/force-change-password/', methods=['GET', 'POST'])
def force_change_password():
    """Force a user to change their default password before accessing the portal."""
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    if not flask.session.get("force_password_change"):
        return flask.redirect(flask.url_for("show_portal"))

    if flask.request.method == 'POST':
        new_password = flask.request.form.get('new_password', '')
        confirm_password = flask.request.form.get('confirm_new_password', '')

        if not new_password or len(new_password) < 6:
            flask.flash('Password must be at least 6 characters.', 'error')
            return flask.redirect(flask.url_for('force_change_password'))

        if new_password != confirm_password:
            flask.flash('Passwords do not match.', 'error')
            return flask.redirect(flask.url_for('force_change_password'))

        user_id = flask.session['user_id']
        conn = obhapp.model.get_db()

        algorithm = 'sha512'
        new_salt = uuid.uuid4().hex
        hash_obj = hashlib.new(algorithm)
        hash_obj.update((new_salt + new_password).encode('utf-8'))
        new_password_hash = hash_obj.hexdigest()
        new_password_db_string = "$".join([algorithm, new_salt, new_password_hash])

        conn.execute(
            "UPDATE brothers SET password = ?, password_changed = 1, default_password = NULL "
            "WHERE user_id = ?",
            (new_password_db_string, user_id)
        )
        conn.execute(
            "INSERT INTO change_log(user_id, desc) VALUES(?, ?)",
            (user_id, "Changed default password on first login")
        )
        conn.commit()

        flask.session.pop("force_password_change", None)
        flask.flash('Password changed successfully! Welcome to the portal.', 'success')
        return flask.redirect(flask.url_for('show_portal'))

    return flask.render_template("portal_force_password.html")


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

    cursor.execute('UPDATE brothers SET password = ?, password_changed = 1, default_password = NULL WHERE user_id = ?', (new_password_db_string, user_id))
    conn.commit()

    cursor.execute(
            "INSERT INTO change_log(user_id, desc) "
            "VALUES(?, ?); ",
            (user_id, "Changed password"),
        )
    conn.commit()



    return flask.jsonify({"success": "Password changed successfully."}), 200


def _generate_default_password():
    """Generate an 8-digit random numeric password."""
    return ''.join([str(secrets.randbelow(10)) for _ in range(8)])


def _set_default_password(con, user_id):
    """Generate, hash, and store a default password for a brother. Returns (plaintext_password, username, fullname, email)."""
    plain_pw = _generate_default_password()
    algorithm = 'sha512'
    salt = uuid.uuid4().hex
    hash_obj = hashlib.new(algorithm)
    hash_obj.update((salt + plain_pw).encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])

    con.execute(
        "UPDATE brothers SET password = ?, default_password = ?, password_changed = 0 "
        "WHERE user_id = ?",
        (password_db_string, plain_pw, user_id)
    )
    cur = con.execute(
        "SELECT username, fullname, uniqname FROM brothers WHERE user_id = ?",
        (user_id,)
    )
    bro = cur.fetchone()
    email = f"{bro['uniqname']}@umich.edu" if bro['uniqname'] and bro['uniqname'] != 'N/A' else None
    return plain_pw, bro['username'], bro['fullname'], email


@obhapp.app.route('/portal/directory/<name>/send-password/', methods=['POST'])
def send_brother_password(name):
    """Generate a new default password for a brother and email it."""
    if "user_id" not in flask.session:
        return flask.jsonify(success=False, error="Not logged in"), 401
    con = obhapp.model.get_db()

    # Check permissions — Admin or President only
    cur = con.execute("SELECT role_name FROM roles WHERE user_id = ?", (flask.session["user_id"],))
    user_roles = [row["role_name"] for row in cur.fetchall()]
    if not any(r in user_roles for r in ["Admin", "President"]):
        return flask.jsonify(success=False, error="No permission"), 403

    cur = con.execute("SELECT user_id, fullname, uniqname FROM brothers WHERE username = ?", (name,))
    bro = cur.fetchone()
    if not bro:
        return flask.jsonify(success=False, error="Member not found"), 404

    plain_pw, username, fullname, email = _set_default_password(con, bro['user_id'])

    if not email:
        con.commit()
        return flask.jsonify(success=False, error="Brother has no uniqname set — cannot send email"), 400

    sent = send_default_password_email(email, fullname, username, plain_pw)
    if sent:
        con.execute(
            "UPDATE brothers SET email_sent = 1 WHERE user_id = ?",
            (bro['user_id'],)
        )

    con.execute(
        "INSERT INTO change_log(user_id, desc) VALUES(?, ?)",
        (flask.session["user_id"], f"{'Sent' if sent else 'Generated'} default password for {fullname}")
    )
    con.commit()

    return flask.jsonify(
        success=True,
        email_sent=sent,
        message=f"Password {'sent to ' + email if sent else 'generated (email failed)'}"
    )


@obhapp.app.route('/portal/directory/send-all-passwords/', methods=['POST'])
def send_all_passwords():
    """Send default passwords to all brothers who haven't been emailed yet."""
    if "user_id" not in flask.session:
        return flask.jsonify(success=False, error="Not logged in"), 401
    con = obhapp.model.get_db()

    # Check permissions — Admin or President only
    cur = con.execute("SELECT role_name FROM roles WHERE user_id = ?", (flask.session["user_id"],))
    user_roles = [row["role_name"] for row in cur.fetchall()]
    if not any(r in user_roles for r in ["Admin", "President"]):
        return flask.jsonify(success=False, error="No permission"), 403

    cur = con.execute(
        "SELECT user_id, fullname, uniqname, username FROM brothers "
        "WHERE email_sent = 0 AND uniqname IS NOT NULL AND uniqname != 'N/A' AND uniqname != ''"
    )
    unsent_brothers = cur.fetchall()

    if not unsent_brothers:
        return flask.jsonify(success=False, error="No brothers pending email")

    sent_count = 0
    failed_count = 0
    for bro in unsent_brothers:
        plain_pw, username, fullname, email = _set_default_password(con, bro['user_id'])
        if email:
            sent = send_default_password_email(email, fullname, username, plain_pw)
            if sent:
                con.execute("UPDATE brothers SET email_sent = 1 WHERE user_id = ?", (bro['user_id'],))
                sent_count += 1
            else:
                failed_count += 1
        else:
            failed_count += 1

    con.execute(
        "INSERT INTO change_log(user_id, desc) VALUES(?, ?)",
        (flask.session["user_id"], f"Bulk sent default passwords: {sent_count} sent, {failed_count} failed")
    )
    con.commit()

    return flask.jsonify(
        success=True,
        sent=sent_count,
        failed=failed_count,
        message=f"Sent {sent_count} email(s), {failed_count} failed"
    )


@obhapp.app.route('/portal/directory/unsent-brothers/')
def get_unsent_brothers():
    """Get list of brothers who haven't been sent their password email."""
    if "user_id" not in flask.session:
        return flask.jsonify(success=False, error="Not logged in"), 401
    con = obhapp.model.get_db()

    cur = con.execute("SELECT role_name FROM roles WHERE user_id = ?", (flask.session["user_id"],))
    user_roles = [row["role_name"] for row in cur.fetchall()]
    if not any(r in user_roles for r in ["Admin", "President"]):
        return flask.jsonify(success=False, error="No permission"), 403

    cur = con.execute(
        "SELECT user_id, fullname, username, uniqname FROM brothers "
        "WHERE email_sent = 0 AND uniqname IS NOT NULL AND uniqname != 'N/A' AND uniqname != ''"
    )
    brothers = [dict(row) for row in cur.fetchall()]
    return flask.jsonify(success=True, brothers=brothers, count=len(brothers))

@obhapp.app.route('/portal/directory/')
def show_portal_directory():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    con = obhapp.model.get_db()
    cur = con.execute(
        "SELECT b.user_id, b.fullname, b.username, b.line, b.line_num, "
        "ln.name AS lion_name, b.uniqname, b.profile_picture, b.active "
        "FROM brothers b "
        "LEFT JOIN lion_names ln ON b.lion_name_id = ln.lion_name_id "
        "ORDER BY b.line ASC, b.line_num ASC;",
    )
    brothers = cur.fetchall()

    # Build line groups
    line_dict = {}
    if brothers:
        last_line = brothers[-1]["line"]
        for i in range(int(last_line) + 1):
            line_name = line_int_to_line[str(i)]
            line_dict[line_name] = [dict(brother) for brother in brothers if brother["line"] == i]

    # Check permissions
    can_edit = False
    can_manage_passwords = False
    cur = con.execute("SELECT role_name FROM roles WHERE user_id = ?", (flask.session["user_id"],))
    user_roles = [row["role_name"] for row in cur.fetchall()]
    if any(r in user_roles for r in ["Admin", "President", "Internal Vice President",
                                      "External Vice President", "Director of Recruitment",
                                      "Director of External"]):
        can_edit = True
    if any(r in user_roles for r in ["Admin", "President"]):
        can_manage_passwords = True

    # Count unsent password emails for the badge
    unsent_count = 0
    if can_manage_passwords:
        cur = con.execute(
            "SELECT COUNT(*) as cnt FROM brothers "
            "WHERE email_sent = 0 AND uniqname IS NOT NULL AND uniqname != 'N/A' AND uniqname != ''"
        )
        unsent_count = cur.fetchone()["cnt"]

    context = {
        "brothers": line_dict,
        "all_brothers": [dict(b) for b in brothers],
        "can_edit": can_edit,
        "can_manage_passwords": can_manage_passwords,
        "unsent_count": unsent_count,
        "line_map": line_int_to_line,
    }
    return flask.render_template("portal_directory.html", **context)

@obhapp.app.route('/portal/directory/<name>/')
def show_directory_brother(name):
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    con = obhapp.model.get_db()
    cur = con.execute(
        "SELECT b.*, ln.name AS lion_name "
        "FROM brothers b "
        "LEFT JOIN lion_names ln ON b.lion_name_id = ln.lion_name_id "
        "WHERE b.username = ?",
        (name,)
    )
    bro = cur.fetchone()
    if not bro:
        flask.flash("Member not found.", "error")
        return flask.redirect(flask.url_for("show_portal_directory"))
    bro = dict(bro)
    bro["line_name"] = line_int_to_line[str(bro["line"])]
    bro['grad_time_display'] = datetime.strptime(bro['grad_time'], '%Y-%m').strftime('%B %Y') if bro['grad_time'] else 'N/A'

    # Get all lion names for dropdown
    cur = con.execute("SELECT lion_name_id, name FROM lion_names ORDER BY name")
    lion_names = cur.fetchall()

    # Check permissions
    can_edit = False
    can_manage_passwords = False
    cur = con.execute("SELECT role_name FROM roles WHERE user_id = ?", (flask.session["user_id"],))
    user_roles = [row["role_name"] for row in cur.fetchall()]
    if any(r in user_roles for r in ["Admin", "President", "Internal Vice President",
                                      "External Vice President", "Director of Recruitment",
                                      "Director of External"]):
        can_edit = True
    if any(r in user_roles for r in ["Admin", "President"]):
        can_manage_passwords = True

    return flask.render_template("portal_brother.html", brother=bro, can_edit=can_edit,
                                 can_manage_passwords=can_manage_passwords, lion_names=lion_names)

@obhapp.app.route('/portal/directory/<name>/edit/', methods=['POST'])
def edit_member(name):
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    con = obhapp.model.get_db()

    # Check permissions
    cur = con.execute("SELECT role_name FROM roles WHERE user_id = ?", (flask.session["user_id"],))
    user_roles = [row["role_name"] for row in cur.fetchall()]
    if not any(r in user_roles for r in ["Admin", "President", "Internal Vice President",
                                          "External Vice President", "Director of Recruitment",
                                          "Director of External"]):
        flask.flash("No permission.", "error")
        return flask.redirect(flask.url_for("show_directory_brother", name=name))

    # Get existing brother
    cur = con.execute("SELECT * FROM brothers WHERE username = ?", (name,))
    bro = cur.fetchone()
    if not bro:
        flask.flash("Member not found.", "error")
        return flask.redirect(flask.url_for("show_portal_directory"))

    new_username = flask.request.form['username']
    fullname = flask.request.form['fullname']
    uniqname = flask.request.form['uniqname']
    major = flask.request.form['major']
    job = flask.request.form['job']
    desc = flask.request.form['desc']
    contacts = flask.request.form['contacts']
    campus = flask.request.form['campus']
    cross_time = flask.request.form['cross_time']
    grad_time = flask.request.form['grad_time']
    line = flask.request.form['line']
    line_num = flask.request.form['line_num']
    lion_name_id = flask.request.form['lion_name_id']
    active = flask.request.form.get('active', 0)

    file = flask.request.files.get("profile_picture")
    if file and file.filename:
        stem = uuid.uuid4().hex
        suffix = pathlib.Path(file.filename).suffix.lower()
        uuid_basename = f"{stem}{suffix}"
        path = obhapp.app.config["UPLOAD_FOLDER"] / uuid_basename
        file.save(path)
    else:
        uuid_basename = bro['profile_picture']

    con.execute('''
        UPDATE brothers SET username = ?, fullname = ?, uniqname = ?, profile_picture = ?,
        major = ?, job = ?, desc = ?, contacts = ?, campus = ?, cross_time = ?,
        grad_time = ?, line = ?, line_num = ?, lion_name_id = ?, active = ?
        WHERE user_id = ?
    ''', (new_username, fullname, uniqname, uuid_basename, major, job, desc, contacts,
          campus, cross_time, grad_time, line, line_num, lion_name_id, active, bro['user_id']))

    con.execute(
        "INSERT INTO change_log(user_id, desc) VALUES(?, ?)",
        (flask.session["user_id"], f"Edited member {fullname} (ID: {bro['user_id']})")
    )
    con.commit()

    flask.flash("Member updated successfully.", "success")
    return flask.redirect(flask.url_for("show_directory_brother", name=new_username))

@obhapp.app.route('/portal/directory/<name>/delete/', methods=['POST'])
def delete_member(name):
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    con = obhapp.model.get_db()

    # Check permissions - admin only for delete
    cur = con.execute("SELECT role_name FROM roles WHERE user_id = ?", (flask.session["user_id"],))
    user_roles = [row["role_name"] for row in cur.fetchall()]
    if 'Admin' not in user_roles:
        flask.flash("Only admins can delete members.", "error")
        return flask.redirect(flask.url_for("show_directory_brother", name=name))

    cur = con.execute("SELECT user_id, fullname FROM brothers WHERE username = ?", (name,))
    bro = cur.fetchone()
    if not bro:
        flask.flash("Member not found.", "error")
        return flask.redirect(flask.url_for("show_portal_directory"))

    # Prevent deleting yourself
    if bro['user_id'] == flask.session['user_id']:
        flask.flash("You cannot delete your own account.", "error")
        return flask.redirect(flask.url_for("show_directory_brother", name=name))

    # Remove roles first
    con.execute("DELETE FROM roles WHERE user_id = ?", (bro['user_id'],))
    con.execute("DELETE FROM brothers WHERE user_id = ?", (bro['user_id'],))

    con.execute(
        "INSERT INTO change_log(user_id, desc) VALUES(?, ?)",
        (flask.session["user_id"], f"Deleted member {bro['fullname']} (ID: {bro['user_id']})")
    )
    con.commit()

    flask.flash(f"Member {bro['fullname']} has been deleted.", "success")
    return flask.redirect(flask.url_for("show_portal_directory"))

@obhapp.app.route('/portal/log/')
def show_portal_log():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    con = obhapp.model.get_db()
    cur = con.execute(
        "SELECT c.id, c.user_id, c.change_time, c.desc, "
        "b.fullname, b.profile_picture "
        "FROM change_log c "
        "LEFT JOIN brothers b ON c.user_id = b.user_id "
        "ORDER BY c.id DESC "
    )
    log = cur.fetchall()
    context = {"log": log}
    return flask.render_template("portal_log.html", **context)

@obhapp.app.route('/portal/recruits/')
def show_portal_recruits():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
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
        "SELECT r.fullname, r.uniqname, r.email, r.accept, r.line_num, "
        "ln.name AS lion_name, r.lion_name_id "
        "FROM recruits r "
        "LEFT JOIN lion_names ln ON r.lion_name_id = ln.lion_name_id "
        "WHERE r.deleted = 0 "
    )
    recruits = cur.fetchall()

    cur = con.execute(
        "SELECT r.fullname, r.uniqname, r.email, r.line_num, "
        "ln.name AS lion_name, r.lion_name_id "
        "FROM recruits r "
        "LEFT JOIN lion_names ln ON r.lion_name_id = ln.lion_name_id "
        "WHERE r.deleted = 1 "
    )
    deleted_recruits = cur.fetchall()

    # Get all lion names for dropdown
    cur = con.execute("SELECT lion_name_id, name FROM lion_names ORDER BY name")
    all_lion_names = cur.fetchall()

    return flask.render_template(
        "portal_recruits.html",
        recruits=recruits,
        deleted_recruits=deleted_recruits,
        can_change=can_change,
        lion_names=all_lion_names
    )

@obhapp.app.route('/portal/recruits/accept', methods=['POST'])
def accept_recruit():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    uniqname = flask.request.json['id']
    line_num = flask.request.json['line_num']
    lion_name_id = flask.request.json['lion_name_id']
    con = obhapp.model.get_db()
    con.execute(
        "UPDATE recruits SET line_num = ?, lion_name_id = ?, accept = 1 WHERE uniqname = ?",
        (line_num, lion_name_id, uniqname)
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
        return flask.redirect(flask.url_for("show_login"))
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
        return flask.redirect(flask.url_for("show_login"))
    uniqname = flask.request.json['id']
    con = obhapp.model.get_db()
    con.execute(
        "UPDATE recruits SET deleted = 1, accept = 0 WHERE uniqname = ?",
        (uniqname,)
    )
    con.execute(
        "INSERT INTO change_log(user_id, desc) "
        "VALUES(?, ?) ",
        (flask.session["user_id"], f"Recruit {uniqname} deleted")
    )
    con.commit()
    # Return recruit data so it can be added to deleted section
    cur = con.execute(
        "SELECT r.fullname, r.uniqname, r.email, r.line_num, "
        "ln.name AS lion_name, r.lion_name_id "
        "FROM recruits r "
        "LEFT JOIN lion_names ln ON r.lion_name_id = ln.lion_name_id "
        "WHERE r.uniqname = ?",
        (uniqname,)
    )
    recruit = cur.fetchone()
    return flask.jsonify(success=True, recruit=dict(recruit) if recruit else None)

@obhapp.app.route('/portal/recruits/restore/', methods=['POST'])
def restore_recruit():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    uniqname = flask.request.json['id']
    con = obhapp.model.get_db()
    con.execute(
        "UPDATE recruits SET deleted = 0, accept = 0 WHERE uniqname = ?",
        (uniqname,)
    )
    con.execute(
        "INSERT INTO change_log(user_id, desc) "
        "VALUES(?, ?) ",
        (flask.session["user_id"], f"Recruit {uniqname} restored")
    )
    con.commit()
    # Return recruit data so it can be added back to active section
    cur = con.execute(
        "SELECT r.fullname, r.uniqname, r.email, r.accept, r.line_num, "
        "ln.name AS lion_name, r.lion_name_id "
        "FROM recruits r "
        "LEFT JOIN lion_names ln ON r.lion_name_id = ln.lion_name_id "
        "WHERE r.uniqname = ?",
        (uniqname,)
    )
    recruit = cur.fetchone()
    return flask.jsonify(success=True, recruit=dict(recruit) if recruit else None)

@obhapp.app.route('/portal/recruits/move/', methods=['POST'])
def move_recruits():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    con = obhapp.model.get_db()

    # Check that no recruits are still pending (neither accepted nor deleted)
    cur = con.execute(
        "SELECT COUNT(*) as cnt FROM recruits WHERE accept = 0 AND deleted = 0"
    )
    pending = cur.fetchone()["cnt"]
    if pending > 0:
        return flask.jsonify(
            success=False,
            error=f"{pending} recruit(s) still pending. Accept or delete all recruits before moving to brothers."
        )

    cur = con.execute(
        "SELECT * FROM recruits "
        "WHERE accept = 1 AND deleted = 0"
    )
    rec = cur.fetchall()

    if not rec:
        return flask.jsonify(success=False, error="No accepted recruits to move.")

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

        # Generate default password instead of hardcoded "password"
        plain_pw = _generate_default_password()
        algorithm = 'sha512'
        salt = uuid.uuid4().hex
        hash_obj = hashlib.new(algorithm)
        hash_obj.update((salt + plain_pw).encode('utf-8'))
        password_hash = hash_obj.hexdigest()
        password_db_string = "$".join([algorithm, salt, password_hash])

        con.execute(
            "INSERT INTO brothers(username, password, default_password, password_changed, "
            "uniqname, fullname, line, line_num, lion_name_id, cross_time, active) "
            "VALUES(?, ?, ?, 0, ?, ?, ?, ?, ?, ?, 1); ",
            (username, password_db_string, plain_pw, recruit["uniqname"],
             recruit["fullname"], line, recruit["line_num"], recruit["lion_name_id"], cross_time)
        )

        # Send default password email to the new brother
        email = f"{recruit['uniqname']}@umich.edu" if recruit['uniqname'] else None
        email_sent = False
        if email:
            email_sent = send_default_password_email(email, recruit["fullname"], username, plain_pw)

        # Update email_sent status
        cur = con.execute("SELECT user_id FROM brothers WHERE username = ?", (username,))
        new_bro = cur.fetchone()
        if new_bro and email_sent:
            con.execute("UPDATE brothers SET email_sent = 1 WHERE user_id = ?", (new_bro['user_id'],))

        con.execute(
            "INSERT INTO change_log(user_id, desc) "
            "VALUES(?, ?); ",
            (flask.session["user_id"], f"Recruit {recruit['uniqname']} moved to Brothers as {username}")
        )
        con.commit()

    con.execute(
        "DELETE FROM recruits WHERE accept = 1 AND deleted = 0"
    )
    con.commit()

    return flask.jsonify(success=True)

@obhapp.app.route('/portal/logout/')
def logout():
    flask.session.clear()
    return flask.redirect(flask.url_for('show_index'))

@obhapp.app.route('/portal/upload/', methods=['GET', 'POST'])
def upload():
    return flask.redirect(flask.url_for("gallery_manage"))


def check_gallery_permission():
    """Check if current user has gallery management permission."""
    if "user_id" not in flask.session:
        return False
    con = obhapp.model.get_db()
    cur = con.execute("SELECT role_name FROM roles WHERE user_id = ?", (flask.session["user_id"],))
    role = cur.fetchone()
    return role and role["role_name"] in ["Admin", "President", "Vice President", "Director of External"]


@obhapp.app.route('/portal/gallery/', methods=['GET'])
def gallery_manage():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    if not check_gallery_permission():
        flask.flash("You don't have permission to manage the gallery.", "error")
        return flask.redirect(flask.url_for("show_portal"))
    con = obhapp.model.get_db()
    cur = con.execute("SELECT filename, desc, sort_order FROM gallery ORDER BY sort_order")
    images = cur.fetchall()
    return flask.render_template('portal_gallery.html', images=images)


@obhapp.app.route('/portal/gallery/upload/', methods=['POST'])
def gallery_upload():
    if "user_id" not in flask.session:
        return flask.jsonify(success=False, error="Not logged in"), 401
    if not check_gallery_permission():
        return flask.jsonify(success=False, error="No permission"), 403

    file = flask.request.files.get('file')
    description = flask.request.form.get('description', '')
    if not file or not file.filename:
        return flask.jsonify(success=False, error="No file provided"), 400

    suffix = pathlib.Path(file.filename).suffix.lower()
    if suffix.lstrip('.') not in obhapp.app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'}):
        return flask.jsonify(success=False, error="File type not allowed"), 400

    con = obhapp.model.get_db()
    # Get next sort order
    cur = con.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 AS next_order FROM gallery")
    next_order = cur.fetchone()["next_order"]

    stem = uuid.uuid4().hex
    uuid_basename = f"{stem}{suffix}"
    path = obhapp.app.config['UPLOAD_FOLDER'] / uuid_basename
    file.save(path)

    con.execute(
        "INSERT INTO gallery(filename, desc, sort_order) VALUES(?, ?, ?)",
        (uuid_basename, description, next_order)
    )
    con.commit()

    con.execute(
        "INSERT INTO change_log(user_id, desc) VALUES(?, ?)",
        (flask.session["user_id"], f"Uploaded gallery photo: {description}")
    )
    con.commit()

    return flask.jsonify(success=True, filename=uuid_basename, description=description, sort_order=next_order)


@obhapp.app.route('/portal/gallery/delete/', methods=['POST'])
def gallery_delete():
    if "user_id" not in flask.session:
        return flask.jsonify(success=False, error="Not logged in"), 401
    if not check_gallery_permission():
        return flask.jsonify(success=False, error="No permission"), 403

    data = flask.request.get_json()
    filename = data.get('filename')
    if not filename:
        return flask.jsonify(success=False, error="No filename"), 400

    con = obhapp.model.get_db()
    cur = con.execute("SELECT desc FROM gallery WHERE filename = ?", (filename,))
    image = cur.fetchone()
    if not image:
        return flask.jsonify(success=False, error="Image not found"), 404

    con.execute("DELETE FROM gallery WHERE filename = ?", (filename,))
    con.commit()

    # Try to remove the file
    file_path = obhapp.app.config['UPLOAD_FOLDER'] / filename
    if file_path.is_file():
        file_path.unlink()

    con.execute(
        "INSERT INTO change_log(user_id, desc) VALUES(?, ?)",
        (flask.session["user_id"], f"Deleted gallery photo: {image['desc']}")
    )
    con.commit()

    return flask.jsonify(success=True)


@obhapp.app.route('/portal/gallery/edit/', methods=['POST'])
def gallery_edit():
    if "user_id" not in flask.session:
        return flask.jsonify(success=False, error="Not logged in"), 401
    if not check_gallery_permission():
        return flask.jsonify(success=False, error="No permission"), 403

    data = flask.request.get_json()
    filename = data.get('filename')
    description = data.get('description', '')
    if not filename:
        return flask.jsonify(success=False, error="No filename"), 400

    con = obhapp.model.get_db()
    con.execute("UPDATE gallery SET desc = ? WHERE filename = ?", (description, filename))
    con.commit()

    con.execute(
        "INSERT INTO change_log(user_id, desc) VALUES(?, ?)",
        (flask.session["user_id"], f"Edited gallery photo description to: {description}")
    )
    con.commit()

    return flask.jsonify(success=True)


@obhapp.app.route('/portal/gallery/reorder/', methods=['POST'])
def gallery_reorder():
    if "user_id" not in flask.session:
        return flask.jsonify(success=False, error="Not logged in"), 401
    if not check_gallery_permission():
        return flask.jsonify(success=False, error="No permission"), 403

    data = flask.request.get_json()
    order = data.get('order', [])
    if not order:
        return flask.jsonify(success=False, error="No order data"), 400

    con = obhapp.model.get_db()
    for idx, filename in enumerate(order):
        con.execute("UPDATE gallery SET sort_order = ? WHERE filename = ?", (idx + 1, filename))
    con.commit()

    con.execute(
        "INSERT INTO change_log(user_id, desc) VALUES(?, ?)",
        (flask.session["user_id"], f"Reordered gallery photos ({len(order)} images)")
    )
    con.commit()

    return flask.jsonify(success=True)



def get_active_brothers():
    connection = obhapp.model.get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT user_id, fullname, profile_picture FROM brothers WHERE active = 1 ORDER BY fullname")
    brothers = cursor.fetchall()
    return brothers

@obhapp.app.route('/portal/board/', methods=['GET', 'POST'])
def assign_roles():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    if flask.request.method == 'POST':
        # Handle role assignment logic
        role_assignments = flask.request.form.to_dict()
        connection = obhapp.model.get_db()
        cursor = connection.cursor()
        changes = []
        for role_id_str, value in role_assignments.items():
            if not value:
                continue  # "No change" selected — skip
            # Get role name for logging
            cursor.execute("SELECT role_name, user_id FROM roles WHERE role_id = ?", (role_id_str,))
            role_info = cursor.fetchone()
            if not role_info:
                continue
            role_name = role_info["role_name"]
            old_user_id = role_info["user_id"]
            if value == 'CLEAR':
                if old_user_id:
                    cursor.execute("SELECT fullname FROM brothers WHERE user_id = ?", (old_user_id,))
                    old_bro = cursor.fetchone()
                    old_name = old_bro["fullname"] if old_bro else "Unknown"
                    changes.append(f"Removed {old_name} from {role_name}")
                cursor.execute("UPDATE roles SET user_id = NULL WHERE role_id = ?", (role_id_str,))
            else:
                cursor.execute("SELECT fullname FROM brothers WHERE user_id = ?", (value,))
                new_bro = cursor.fetchone()
                new_name = new_bro["fullname"] if new_bro else "Unknown"
                changes.append(f"Assigned {new_name} to {role_name}")
                cursor.execute("UPDATE roles SET user_id = ? WHERE role_id = ?", (value, role_id_str))
        connection.commit()

        if changes:
            desc = "Board changes: " + "; ".join(changes)
            cursor.execute(
                "INSERT INTO change_log(user_id, desc) "
                "VALUES(?, ?); ",
                (flask.session["user_id"], desc),
            )
            connection.commit()

        flask.flash("Board roles updated successfully.", "success")
        return flask.redirect(flask.url_for('assign_roles'))

    connection = obhapp.model.get_db()
    cursor = connection.cursor()

    # Get board roles (non-Admin)
    cursor.execute(
        "SELECT r.role_id, r.role_name, r.user_id, b.fullname, b.profile_picture "
        "FROM roles r LEFT JOIN brothers b ON r.user_id = b.user_id "
        "WHERE r.role_name != 'Admin' "
        "ORDER BY r.role_id"
    )
    roles = cursor.fetchall()

    # Get admins
    cursor.execute(
        "SELECT r.role_id, r.user_id, b.fullname, b.profile_picture, b.username "
        "FROM roles r JOIN brothers b ON r.user_id = b.user_id "
        "WHERE r.role_name = 'Admin' "
        "ORDER BY b.fullname"
    )
    admins = cursor.fetchall()

    active_brothers = get_active_brothers()

    # All brothers for admin assignment (admins can be inactive alumni)
    cursor.execute("SELECT user_id, fullname FROM brothers ORDER BY fullname")
    all_brothers = cursor.fetchall()

    # Check if current user can edit
    can_change = False
    is_admin = False
    cursor.execute("SELECT role_name FROM roles WHERE user_id = ?", (flask.session['user_id'],))
    user_roles = [row["role_name"] for row in cursor.fetchall()]
    if 'Admin' in user_roles or 'President' in user_roles:
        can_change = True
    if 'Admin' in user_roles:
        is_admin = True

    return flask.render_template(
        'portal_board.html',
        brothers=active_brothers,
        all_brothers=all_brothers,
        roles=roles,
        admins=admins,
        can_change=can_change,
        is_admin=is_admin
    )


@obhapp.app.route('/portal/board/admin/add/', methods=['POST'])
def add_admin():
    if "user_id" not in flask.session:
        return flask.jsonify(success=False, error="Not logged in"), 401
    con = obhapp.model.get_db()
    cur = con.execute("SELECT role_name FROM roles WHERE user_id = ?", (flask.session["user_id"],))
    user_roles = [row["role_name"] for row in cur.fetchall()]
    if 'Admin' not in user_roles:
        return flask.jsonify(success=False, error="Only admins can manage admins"), 403

    data = flask.request.get_json()
    new_admin_id = data.get('user_id')
    if not new_admin_id:
        return flask.jsonify(success=False, error="No user specified"), 400

    # Check user exists
    cur = con.execute("SELECT fullname, profile_picture, username FROM brothers WHERE user_id = ?", (new_admin_id,))
    brother = cur.fetchone()
    if not brother:
        return flask.jsonify(success=False, error="User not found"), 404

    # Check not already admin
    cur = con.execute("SELECT role_id FROM roles WHERE role_name = 'Admin' AND user_id = ?", (new_admin_id,))
    if cur.fetchone():
        return flask.jsonify(success=False, error="Already an admin"), 400

    con.execute("INSERT INTO roles (role_name, user_id) VALUES ('Admin', ?)", (new_admin_id,))
    con.commit()

    con.execute(
        "INSERT INTO change_log(user_id, desc) VALUES(?, ?)",
        (flask.session["user_id"], f"Added {brother['fullname']} as Admin")
    )
    con.commit()

    # Get the new role_id
    cur = con.execute("SELECT role_id FROM roles WHERE role_name = 'Admin' AND user_id = ?", (new_admin_id,))
    role = cur.fetchone()

    return flask.jsonify(
        success=True,
        role_id=role["role_id"],
        fullname=brother["fullname"],
        profile_picture=brother["profile_picture"],
        username=brother["username"]
    )


@obhapp.app.route('/portal/board/admin/remove/', methods=['POST'])
def remove_admin():
    if "user_id" not in flask.session:
        return flask.jsonify(success=False, error="Not logged in"), 401
    con = obhapp.model.get_db()
    cur = con.execute("SELECT role_name FROM roles WHERE user_id = ?", (flask.session["user_id"],))
    user_roles = [row["role_name"] for row in cur.fetchall()]
    if 'Admin' not in user_roles:
        return flask.jsonify(success=False, error="Only admins can manage admins"), 403

    data = flask.request.get_json()
    role_id = data.get('role_id')
    if not role_id:
        return flask.jsonify(success=False, error="No role specified"), 400

    # Prevent removing yourself if you're the last admin
    cur = con.execute("SELECT COUNT(*) as cnt FROM roles WHERE role_name = 'Admin'")
    count = cur.fetchone()["cnt"]
    cur = con.execute("SELECT user_id FROM roles WHERE role_id = ?", (role_id,))
    target = cur.fetchone()
    if not target:
        return flask.jsonify(success=False, error="Role not found"), 404

    if count <= 1:
        return flask.jsonify(success=False, error="Cannot remove the last admin"), 400

    # Get name for log
    cur = con.execute("SELECT fullname FROM brothers WHERE user_id = ?", (target["user_id"],))
    brother = cur.fetchone()

    con.execute("DELETE FROM roles WHERE role_id = ?", (role_id,))
    con.commit()

    con.execute(
        "INSERT INTO change_log(user_id, desc) VALUES(?, ?)",
        (flask.session["user_id"], f"Removed {brother['fullname']} from Admin")
    )
    con.commit()

    return flask.jsonify(success=True)

@obhapp.app.route('/portal/messages/')
def show_messages():
    """Show the contact messages in the portal."""
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    connection = obhapp.model.get_db()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT m.*, b.fullname as replier_name "
        "FROM messages m "
        "LEFT JOIN brothers b ON m.replied_by = b.user_id "
        "ORDER BY m.created_at DESC"
    )
    messages = cursor.fetchall()
    return flask.render_template('portal_messages.html', messages=messages)


@obhapp.app.route('/portal/messages/<int:message_id>/reply/', methods=['POST'])
def reply_to_message(message_id):
    """Reply to a contact message via email."""
    if "user_id" not in flask.session:
        return flask.jsonify(success=False, error="Not logged in"), 401

    con = obhapp.model.get_db()
    cur = con.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
    msg = cur.fetchone()
    if not msg:
        return flask.jsonify(success=False, error="Message not found"), 404

    data = flask.request.get_json()
    reply_text = (data.get('reply_text') or '').strip()
    if not reply_text:
        return flask.jsonify(success=False, error="Reply cannot be empty"), 400

    # Get replier name
    cur = con.execute("SELECT fullname FROM brothers WHERE user_id = ?", (flask.session["user_id"],))
    replier = cur.fetchone()
    replier_name = replier["fullname"] if replier else "ΩBH Member"

    sent = send_message_reply_email(
        msg['email'], msg['name'], msg['subject'], reply_text, replier_name
    )

    if not sent:
        return flask.jsonify(success=False, error="Failed to send email. Check email configuration."), 500

    con.execute(
        "UPDATE messages SET reply_text = ?, replied_at = CURRENT_TIMESTAMP, replied_by = ? "
        "WHERE id = ?",
        (reply_text, flask.session["user_id"], message_id)
    )
    con.execute(
        "INSERT INTO change_log(user_id, desc) VALUES(?, ?)",
        (flask.session["user_id"], f"Replied to message from {msg['name']} (subject: {msg['subject']})")
    )
    con.commit()

    return flask.jsonify(success=True, message="Reply sent successfully")

@obhapp.app.route('/portal/lion-names/')
def show_lion_names():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    con = obhapp.model.get_db()

    # Get all lion names with their brothers
    cur = con.execute("SELECT lion_name_id, name, meaning FROM lion_names")
    lion_names_raw = cur.fetchall()

    # Hardcoded founding-line order: Hareth (Fraternal Father), then Aklaaf through Dhergham
    FOUNDING_ORDER = [
        "Hareth", "Aklaaf", "Haidar", "Abbas", "Furhud", "Hamza",
        "Sarem", "Usayd", "Feras", "Asrul", "Layth", "Baqer",
        "Shibel", "Bassel", "Muthafar", "Rebaal", "Dhergham",
    ]
    order_map = {name: i for i, name in enumerate(FOUNDING_ORDER)}
    lion_names = sorted(
        lion_names_raw,
        key=lambda ln: (order_map.get(ln["name"], len(FOUNDING_ORDER)), ln["name"])
    )

    # Get brothers grouped by lion_name_id, sorted by line (oldest first)
    cur = con.execute(
        "SELECT b.fullname, b.username, b.profile_picture, b.lion_name_id, b.active, "
        "b.line, b.line_num "
        "FROM brothers b WHERE b.lion_name_id IS NOT NULL "
        "ORDER BY b.line ASC, b.line_num ASC"
    )
    all_brothers = cur.fetchall()

    # Build a dict of lion_name_id -> list of brothers
    brothers_by_lion = {}
    for bro in all_brothers:
        lid = bro["lion_name_id"]
        if lid not in brothers_by_lion:
            brothers_by_lion[lid] = []
        brothers_by_lion[lid].append(dict(bro))

    # Check permissions
    cur = con.execute("SELECT role_name FROM roles WHERE user_id = ?", (flask.session["user_id"],))
    user_roles = [row["role_name"] for row in cur.fetchall()]
    can_edit = any(r in user_roles for r in ["Admin", "President"])

    return flask.render_template(
        "portal_lion_names.html",
        lion_names=lion_names,
        brothers_by_lion=brothers_by_lion,
        can_edit=can_edit
    )

@obhapp.app.route('/portal/lion-names/edit/', methods=['POST'])
def edit_lion_name():
    if "user_id" not in flask.session:
        return flask.jsonify(success=False, error="Not logged in"), 401
    con = obhapp.model.get_db()

    cur = con.execute("SELECT role_name FROM roles WHERE user_id = ?", (flask.session["user_id"],))
    user_roles = [row["role_name"] for row in cur.fetchall()]
    if not any(r in user_roles for r in ["Admin", "President"]):
        return flask.jsonify(success=False, error="No permission"), 403

    data = flask.request.get_json()
    lion_name_id = data.get("lion_name_id")
    meaning = data.get("meaning", "")

    if not lion_name_id:
        return flask.jsonify(success=False, error="No lion name specified"), 400

    con.execute("UPDATE lion_names SET meaning = ? WHERE lion_name_id = ?", (meaning, lion_name_id))
    con.execute(
        "INSERT INTO change_log(user_id, desc) VALUES(?, ?)",
        (flask.session["user_id"], f"Edited lion name meaning (ID: {lion_name_id})")
    )
    con.commit()
    return flask.jsonify(success=True)

@obhapp.app.route('/portal/lion-names/add/', methods=['POST'])
def add_lion_name():
    if "user_id" not in flask.session:
        return flask.jsonify(success=False, error="Not logged in"), 401
    con = obhapp.model.get_db()

    cur = con.execute("SELECT role_name FROM roles WHERE user_id = ?", (flask.session["user_id"],))
    user_roles = [row["role_name"] for row in cur.fetchall()]
    if not any(r in user_roles for r in ["Admin", "President"]):
        return flask.jsonify(success=False, error="No permission"), 403

    data = flask.request.get_json()
    name = (data.get("name") or "").strip()
    meaning = (data.get("meaning") or "").strip()

    if not name:
        return flask.jsonify(success=False, error="Name is required"), 400

    # Check uniqueness
    cur = con.execute("SELECT lion_name_id FROM lion_names WHERE name = ?", (name,))
    if cur.fetchone():
        return flask.jsonify(success=False, error="A lion name with that name already exists"), 400

    con.execute("INSERT INTO lion_names(name, meaning) VALUES(?, ?)", (name, meaning))
    con.execute(
        "INSERT INTO change_log(user_id, desc) VALUES(?, ?)",
        (flask.session["user_id"], f"Added lion name: {name}")
    )
    con.commit()

    cur = con.execute("SELECT lion_name_id FROM lion_names WHERE name = ?", (name,))
    new_id = cur.fetchone()["lion_name_id"]

    return flask.jsonify(success=True, lion_name_id=new_id, name=name, meaning=meaning)

@obhapp.app.route('/portal/lion-names/delete/', methods=['POST'])
def delete_lion_name():
    if "user_id" not in flask.session:
        return flask.jsonify(success=False, error="Not logged in"), 401
    con = obhapp.model.get_db()

    cur = con.execute("SELECT role_name FROM roles WHERE user_id = ?", (flask.session["user_id"],))
    user_roles = [row["role_name"] for row in cur.fetchall()]
    if not any(r in user_roles for r in ["Admin", "President"]):
        return flask.jsonify(success=False, error="No permission"), 403

    data = flask.request.get_json()
    lion_name_id = data.get("lion_name_id")
    if not lion_name_id:
        return flask.jsonify(success=False, error="No lion name specified"), 400

    # Get the name for logging
    cur = con.execute("SELECT name FROM lion_names WHERE lion_name_id = ?", (lion_name_id,))
    row = cur.fetchone()
    if not row:
        return flask.jsonify(success=False, error="Lion name not found"), 404
    lion_name = row["name"]

    # Check if any brothers or recruits still reference this lion name
    cur = con.execute("SELECT COUNT(*) as cnt FROM brothers WHERE lion_name_id = ?", (lion_name_id,))
    bro_count = cur.fetchone()["cnt"]
    cur = con.execute("SELECT COUNT(*) as cnt FROM recruits WHERE lion_name_id = ?", (lion_name_id,))
    rec_count = cur.fetchone()["cnt"]
    if bro_count > 0 or rec_count > 0:
        return flask.jsonify(
            success=False,
            error=f"Cannot delete '{lion_name}' — it is assigned to {bro_count} brother(s) and {rec_count} recruit(s). Reassign them first."
        ), 400

    con.execute("DELETE FROM lion_names WHERE lion_name_id = ?", (lion_name_id,))
    con.execute(
        "INSERT INTO change_log(user_id, desc) VALUES(?, ?)",
        (flask.session["user_id"], f"Deleted lion name: {lion_name} (ID: {lion_name_id})")
    )
    con.commit()
    return flask.jsonify(success=True)

@obhapp.app.route('/portal/help/')
def show_portal_help():
    if "user_id" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    return flask.render_template("portal_help.html")