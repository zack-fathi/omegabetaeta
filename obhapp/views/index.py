import flask
import obhapp


@obhapp.app.route('/uploads/<filename>')
def uploaded_file(filename):
    return flask.send_from_directory(obhapp.app.config['UPLOAD_FOLDER'], filename)

@obhapp.app.route('/')
def show_index():
    return flask.render_template("index.html")