import flask
import obhapp
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def _get_calendar_service():
    """Build a Google Calendar API service using the service account."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    sa_file = obhapp.SERVICE_ACCOUNT_FILE
    if not sa_file:
        return None
    creds = service_account.Credentials.from_service_account_file(
        sa_file, scopes=['https://www.googleapis.com/auth/calendar.readonly']
    )
    return build('calendar', 'v3', credentials=creds, cache_discovery=False)


def _fetch_events(calendar_ids, time_min, time_max):
    """Fetch events from one or more Google Calendars."""
    service = _get_calendar_service()
    if not service:
        logger.error("Calendar service unavailable — SERVICE_ACCOUNT_FILE not set")
        return []
    events = []
    for cal_id in calendar_ids:
        try:
            result = service.events().list(
                calendarId=cal_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime',
                maxResults=250,
            ).execute()
            for item in result.get('items', []):
                start = item['start'].get('dateTime', item['start'].get('date'))
                end = item['end'].get('dateTime', item['end'].get('date'))
                events.append({
                    'title': item.get('summary', '(No title)'),
                    'start': start,
                    'end': end,
                    'url': item.get('htmlLink', ''),
                })
        except Exception as e:
            logger.error("Failed to fetch events from calendar %s: %s", cal_id, e)
    return events


@obhapp.app.route('/api/calendar-events/')
def api_calendar_events():
    """Return calendar events as JSON for FullCalendar.

    Query params:
      scope: 'public' (default) or 'portal'
      start: ISO date string
      end:   ISO date string
    """
    scope = flask.request.args.get('scope', 'public')
    start = flask.request.args.get('start')
    end = flask.request.args.get('end')

    if not start or not end:
        now = datetime.utcnow()
        start = (now - timedelta(days=60)).isoformat() + 'Z'
        end = (now + timedelta(days=120)).isoformat() + 'Z'
    else:
        # FullCalendar sends full ISO timestamps (e.g. 2026-03-01T00:00:00-05:00)
        # or plain dates (2026-03-01). Google Calendar API accepts both as-is.
        # Only append Z for bare dates with no time component.
        if 'T' not in start:
            start += 'T00:00:00Z'
        if 'T' not in end:
            end += 'T00:00:00Z'

    cal_ids = []
    if obhapp.PUBLIC_CALENDAR_ID:
        cal_ids.append(obhapp.PUBLIC_CALENDAR_ID)
    if scope == 'portal' and obhapp.PORTAL_CALENDAR_ID:
        cal_ids.append(obhapp.PORTAL_CALENDAR_ID)

    events = _fetch_events(cal_ids, start, end)
    return flask.jsonify(events)

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

        # Save the message to the database
        con = obhapp.model.get_db()
        con.execute(
            "INSERT INTO messages (name, email, subject, message) "
            "VALUES (?, ?, ?, ?)",
            (name, email, subject, message)
        )
        con.commit()

        flask.flash('Your message has been saved successfully!', 'success')
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
        "SELECT * FROM gallery ORDER BY sort_order "
    )
    context = {
        "images": cur.fetchall()
    }
    return flask.render_template("gallery.html", **context)

@obhapp.app.route('/contact_thank_you/')
def contact_thank_you():
    return flask.render_template("contact_thank_you.html")
