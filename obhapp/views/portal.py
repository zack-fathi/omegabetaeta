import flask
import obhapp


@obhapp.app.route('/login/')
def show_login():
    if "user" in flask.session:
        return flask.redirect(flask.url_for("show_portal"))
    return flask.render_template("login.html")

@obhapp.app.route('/login/', methods=["POST"])
def login():
    username = flask.request.form["username"]
    password = flask.request.form["password"]
    if not username or not password:
        flask.abort(400)
    connection = obhapp.model.get_db()
    cur = connection.execute(
        "SELECT password FROM brothers "
        "WHERE uniqname = ? OR name = ?",
        (username, username)
    )
    pw = cur.fetchone()
    if pw is None:
        flask.abort(403)
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
        flask.abort(403)
    return flask.redirect(flask.request.args.get('target'))

@obhapp.app.route('/portal/')
def show_portal():
    if "user" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    return flask.render_template("portal.html")