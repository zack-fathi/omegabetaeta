import flask
import obhapp
import os

@obhapp.app.route('/uploads/<filename>')
def uploaded_file(filename):
    return flask.send_from_directory(obhapp.app.config['UPLOAD_FOLDER'], filename)


@obhapp.app.route('/')
def show_index():

    # Get the path to the carousel images folder
    carousel_folder = os.path.join(
        obhapp.app.static_folder, 'images/carousel_images'
    )
    
    # Dynamically list all image files in the folder
    images = [
        f'images/carousel_images/{file}'
        for file in os.listdir(carousel_folder)
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
    ]
    
    # Render the template and pass the image list
    return flask.render_template("index.html", images=images)



@obhapp.app.route('/about/')
def show_about():
    return flask.render_template("about.html")

@obhapp.app.route('/contact/', methods=['GET', 'POST'])
def show_contact():
    if flask.request.method == "POST":
        # Retrieve form data
        name = flask.request.form.get('name')
        email = flask.request.form.get('email')
        subject = flask.request.form.get('subject')
        message = flask.request.form.get('message')
        
        # Validate form data
        if not name or not email or not message:
            flask.flash('Please fill out all required fields.', 'danger')
            return flask.redirect(flask.url_for('show_contact'))

        # Process the message (e.g., send an email or save to database)
        # For now, redirect to a thank-you page
        flask.flash('Your message has been sent successfully!', 'success')
        return flask.redirect(flask.url_for('contact_thank_you'))
    
    return flask.render_template("contact.html")

@obhapp.app.route('/donate/')
def show_donate():
    return flask.render_template("donate.html")

@obhapp.app.route('/calendar/')
def show_calendar():
    return flask.render_template("calendar.html")


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

@obhapp.app.route('/contact_thank_you/')
def contact_thank_you():
    return flask.render_template("contact_thank_you.html")
