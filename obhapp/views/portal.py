import flask
import obhapp
import datetime
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
        "SELECT password FROM brothers "
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
    else:
        flask.flash('Incorrect password', 'error')
        return flask.redirect(flask.url_for('show_login'))
    return flask.redirect(flask.request.args.get('target'))


@obhapp.app.route('/portal/')
def show_portal():
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    return flask.render_template("portal_index.html")


@obhapp.app.route('/portal/account/')
def show_portal_account():
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    user = flask.session['user']
    context = {"user": user}
    return flask.render_template("portal_account.html")


@obhapp.app.route('/portal/agenda/')
def show_portal_agenda():
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    return flask.render_template("portal_agenda.html")


@obhapp.app.route('/portal/calendar/')
def show_portal_calender():
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    return flask.render_template("portal_calendar.html")


@obhapp.app.route('/portal/log/')
def show_portal_log():
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    return flask.render_template("portal_log.html")


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
    recruit_id = flask.request.json['id']
    line_num = flask.request.json['line_num']
    lion_name = flask.request.json['lion_name']
    con = obhapp.model.get_db()
    con.execute(
        "UPDATE recruits SET line_num = ?, lion_name = ?, accept = 1 WHERE uniqname = ?",
        (line_num, lion_name, recruit_id)
    )
    con.commit()
    return flask.jsonify(success=True)

@obhapp.app.route('/portal/recruits/remove', methods=['POST'])
def remove_recruit():
    recruit_id = flask.request.json['id']
    con = obhapp.model.get_db()
    con.execute(
        "DELETE FROM recruits WHERE uniqname = ?",
        (recruit_id,)
    )
    con.commit()
    return flask.jsonify(success=True)

@obhapp.app.route('/portal/recruits/move', methods=['POST'])
def move_recruits():
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
            "INSERT INTO brothers(name, uniqname, fullname, line, line_num, lion_name, cross_time) "
            "VALUES(?, ?, ?, ?, ?, ?, ?); ",
            (name, recruit["uniqname"], recruit["fullname"], line, recruit["line_num"], recruit["lion_name"], cross_time)
        )
        con.commit()

    con.execute(
        "DELETE FROM recruits WHERE accept = 1"
    )
    con.commit()
    return flask.jsonify(success=True)

