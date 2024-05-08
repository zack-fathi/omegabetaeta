import flask
import obhapp

@obhapp.app.route('/')
def show_index():
    return flask.render_template("index.html")