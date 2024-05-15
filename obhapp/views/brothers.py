import flask
import datetime
import obhapp
from obhapp.utils import line_int_to_line


@obhapp.app.route('/brothers/')
def show_brothers():
    con = obhapp.model.get_db()
    cur = con.execute(
        "SELECT fullname, name, line, line_num, uniqname, profile_picture FROM brothers "
        "WHERE active = 1 "
        "ORDER BY fullname ASC;",
    )
    brothers = cur.fetchall()
    context = {}
    context["brothers"] = brothers
    
    return flask.render_template("brothers.html", **context)

@obhapp.app.route('/brothers/<name>/')
def show_brother(name):
    con = obhapp.model.get_db()
    cur = con.execute(
        "SELECT fullname, uniqname, profile_picture, major, desc, campus, contacts, cross_time, grad_time, line, line_num FROM brothers "
        "WHERE name = ? ",
        (name, )
    )
    bro = cur.fetchone()
    bro["line_name"] = line_int_to_line[str(bro["line"])]
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
    
    con = obhapp.model.get_db()
    cur = con.execute(
        "INSERT INTO recruits "
        "(uniqname, fullname, email, campus) "
        "VALUES(?, ?, ?, ?) ",
        (uniqname, fullname, email, "Ann Arbor")
    )


    return flask.render_template("apply.html")
    