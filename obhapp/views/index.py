import flask
import obhapp


@obhapp.app.route('/uploads/<filename>')
def uploaded_file(filename):
    return flask.send_from_directory(obhapp.app.config['UPLOAD_FOLDER'], filename)


@obhapp.app.route('/')
def show_index():
    return flask.render_template("index.html")


@obhapp.app.route('/about/')
def show_about():
    return flask.render_template("about.html")


@obhapp.app.route('/gallery/')
def show_gallery():
    con = obhapp.model.get_db()
    cur = con.execute(
        "SELECT * FROM gallery "
    )
    context = {
        "images": cur.fetchall()
    }
    return flask.render_template("gallery.html", **context)
