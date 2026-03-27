import flask
from datetime import datetime
import obhapp
from obhapp.utils import line_int_to_line


@obhapp.app.route('/brothers/')
def show_brothers():
    con = obhapp.model.get_db()
    cur = con.execute(
        "SELECT fullname, username, line, line_num, lion_name, uniqname, profile_picture FROM brothers "
        "WHERE active = 1 "
        "ORDER BY line ASC, line_num ASC;",
    )
    brothers = cur.fetchall()
    line_dict = {}
    if brothers:
        last_line = brothers[-1]["line"]
        for i in range(int(last_line) + 1):
            members = [bro for bro in brothers if bro["line"] == i]
            if members:
                line_name = line_int_to_line[str(i)]
                line_dict[line_name] = members

    return flask.render_template("brothers.html", brothers=line_dict)

@obhapp.app.route('/brothers/<name>/')
def show_brother(name):
    con = obhapp.model.get_db()
    cur = con.execute(
        "SELECT fullname, uniqname, profile_picture, major, desc, campus, contacts, cross_time, grad_time, line, line_num, lion_name FROM brothers "
        "WHERE username = ? ",
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

    # Check if this person was previously deleted — bring them back
    existing = con.execute(
        "SELECT uniqname, deleted FROM recruits WHERE uniqname = ?",
        (uniqname,)
    ).fetchone()

    if existing and existing['deleted']:
        con.execute(
            "UPDATE recruits SET fullname = ?, email = ?, campus = ?, "
            "deleted = 0, accept = 0, line_num = NULL, lion_name = NULL "
            "WHERE uniqname = ?",
            (fullname, email, "Ann Arbor", uniqname)
        )
    elif not existing:
        con.execute(
            "INSERT INTO recruits "
            "(uniqname, fullname, email, campus) "
            "VALUES(?, ?, ?, ?) ",
            (uniqname, fullname, email, "Ann Arbor")
        )

    return flask.render_template("apply-confirm.html")
    