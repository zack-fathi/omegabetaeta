import flask
from datetime import datetime
import obhapp
from obhapp.utils import line_int_to_line
from obhapp.email_utils import send_application_confirmation_email


@obhapp.app.route('/brothers/')
def show_brothers():
    con = obhapp.model.get_db()
    cur = con.execute(
        "SELECT b.fullname, b.username, b.line, b.line_num, ln.name AS lion_name, "
        "b.uniqname, b.profile_picture "
        "FROM brothers b "
        "LEFT JOIN lion_names ln ON b.lion_name_id = ln.lion_name_id "
        "WHERE b.active = 1 "
        "ORDER BY b.fullname ASC;",
    )
    brothers = cur.fetchall()
    for bro in brothers:
        bro["line_name"] = line_int_to_line.get(str(bro["line"]), "")

    return flask.render_template("brothers.html", brothers=brothers)

@obhapp.app.route('/brothers/<name>/')
def show_brother(name):
    con = obhapp.model.get_db()
    cur = con.execute(
        "SELECT b.fullname, b.uniqname, b.profile_picture, b.major, b.desc, "
        "b.campus, b.contacts, b.cross_time, b.grad_time, b.line, b.line_num, "
        "ln.name AS lion_name "
        "FROM brothers b "
        "LEFT JOIN lion_names ln ON b.lion_name_id = ln.lion_name_id "
        "WHERE b.username = ? ",
        (name, )
    )
    bro = cur.fetchone()
    if not bro:
        flask.abort(404)
    bro["line_name"] = line_int_to_line[str(bro["line"])]
    bro['grad_time'] = datetime.strptime(bro['grad_time'], '%Y-%m').strftime('%B %Y') if bro['grad_time'] else 'N/A'
    return flask.render_template("brother.html", brother=bro)

@obhapp.app.route('/apply/')
def show_apply():
    return flask.render_template("apply.html")

@obhapp.app.route('/apply/', methods=['POST'])
def apply_rec():
    uniqname = flask.request.form["uniqname"]
    email = flask.request.form["email"]
    fullname = flask.request.form["fullname"]

    con = obhapp.model.get_db()

    # Check if this uniqname already belongs to a brother
    bro = con.execute(
        "SELECT uniqname FROM brothers WHERE uniqname = ?",
        (uniqname,)
    ).fetchone()
    if bro:
        flask.flash('This uniqname is already associated with a brother.', 'error')
        return flask.redirect(flask.url_for('show_apply'))

    # Check if this person was previously deleted — bring them back
    existing = con.execute(
        "SELECT uniqname, deleted FROM recruits WHERE uniqname = ?",
        (uniqname,)
    ).fetchone()

    if existing and existing['deleted']:
        con.execute(
            "UPDATE recruits SET fullname = ?, email = ?, campus = ?, "
            "deleted = 0, accept = 0, line_num = NULL, lion_name_id = NULL "
            "WHERE uniqname = ?",
            (fullname, email, "Ann Arbor", uniqname)
        )
    elif existing:
        flask.flash('This uniqname has already applied.', 'error')
        return flask.redirect(flask.url_for('show_apply'))
    else:
        con.execute(
            "INSERT INTO recruits "
            "(uniqname, fullname, email, campus) "
            "VALUES(?, ?, ?, ?) ",
            (uniqname, fullname, email, "Ann Arbor")
        )

    # Send confirmation email
    send_application_confirmation_email(email, fullname)

    return flask.render_template("apply-confirm.html")
    