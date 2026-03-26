"""Omega Beta Eta package initializer."""
import flask
from dotenv import load_dotenv
import os

# Load environment variables before anything else
load_dotenv()

# app is a single object used by all the code modules in this package
app = flask.Flask(__name__)  # pylint: disable=invalid-name

# Read settings from config module (obhapp/config.py)
app.config.from_object('obhapp.config')

app.debug = True


@app.context_processor
def inject_user_roles():
    """Return the user roles for the current session."""
    if "user_id" in flask.session:
        user_id = flask.session["user_id"]
        con = obhapp.model.get_db()
        cur = con.execute(
            "SELECT role_name FROM roles WHERE user_id = ?",
            (user_id,)
        )
        user_roles = {row["role_name"] for row in cur.fetchall()}
        return {"user_roles": user_roles}
    return {"user_roles": set()}


# Google Calendar integration (optional for local development)
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')
PORTAL_CALENDAR_ID = os.getenv('PORTAL_CALENDAR_ID')
GOOGLE_CALENDAR_ENABLED = bool(SERVICE_ACCOUNT_FILE and PORTAL_CALENDAR_ID)

if not GOOGLE_CALENDAR_ENABLED:
    print("WARNING: Google Calendar not configured. Calendar events will be empty.")
    print("Set SERVICE_ACCOUNT_FILE and PORTAL_CALENDAR_ID in .env to enable.")


@app.route('/get-events', methods=['GET'])
def get_events():
    """Return the events for the calendar using a service account."""
    if not GOOGLE_CALENDAR_ENABLED:
        return flask.jsonify([])

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build('calendar', 'v3', credentials=credentials)
        events_result = service.events().list(calendarId=PORTAL_CALENDAR_ID).execute()
        events = events_result.get('items', [])
        return flask.jsonify(events)

    except Exception as e:
        print(f"Error fetching events: {e}")
        return flask.jsonify({'error': str(e)}), 500


# Ignore coding style violations for these imports
import obhapp.views  # noqa: E402  pylint: disable=wrong-import-position
import obhapp.model  # noqa: E402  pylint: disable=wrong-import-position
