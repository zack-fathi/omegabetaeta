import flask
import datetime
import obhapp
from obhapp.utils import line_int_to_line


@obhapp.app.route('/brothers/')
def show_brothers():
    con = obhapp.model.get_db()
    cur = con.execute(
        "SELECT fullname, name, line, line_num, uniqname FROM brothers "
        "ORDER BY line ASC, line_num ASC;",
    )
    brothers = cur.fetchall()
    last_line = brothers[-1]["line"]
    context = {}

    for i in range(last_line + 1):
        line = line_int_to_line[str(i)]
        context[line] = [brother for brother in brothers if brother["line"] == i]


    ret = {
        "context": context
    }
    return flask.render_template("brothers.html", **ret)

@obhapp.app.route('/brothers/<name>/')
def show_brother(name):
    con = obhapp.model.get_db()
    cur = con.execute(
        "SELECT fullname, uniqname, profile_picture, major, desc, campus, contacts, cross_time, grad_time, line, line_num FROM brothers "
        "WHERE name = ? ",
        (name, )
    )
    bro = cur.fetchone()
    # return bro
    return flask.render_template("brother.html", **bro)

@obhapp.app.route('/apply/')
def show_apply():
    return flask.render_template("apply.html")

@obhapp.app.route('/apply/', methods=['POST'])
def apply_rec():
    uniqname = flask.request.form["uniqname"]
    email = flask.request.form["email"]
    fullname = flask.request.form["fullname"]

    time_made = datetime.datetime.now()
    oct = datetime.datetime(2016, 10, 1)
    year_diff = (time_made.year - oct.year) - (1 if (time_made.month, time_made.day) < (oct.month, oct.day) else 0)
    line = line_int_to_line[str(year_diff)]
    crosstime = "SP' " + str(2018 + year_diff)
    
    con = obhapp.model.get_db()
    cur = con.execute(
        "INSERT INTO recruits "
        "(uniqname, fullname, email, cross_time, line, campus, accept) "
        "VALUES(?, ?, ?, ?, ?, ?, ?) ",
        (uniqname, fullname, email, crosstime, line, "Ann Arbor", 0)
    )


    return flask.render_template("apply.html")
    