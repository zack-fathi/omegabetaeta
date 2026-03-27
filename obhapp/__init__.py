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


# Google Calendar integration via service account (calendars stay private)
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')
PORTAL_CALENDAR_ID = os.getenv('PORTAL_CALENDAR_ID')
PUBLIC_CALENDAR_ID = os.getenv('PUBLIC_CALENDAR_ID')

if not (SERVICE_ACCOUNT_FILE and PORTAL_CALENDAR_ID and PUBLIC_CALENDAR_ID):
    print("WARNING: Google Calendar not fully configured. Set SERVICE_ACCOUNT_FILE, PORTAL_CALENDAR_ID, and PUBLIC_CALENDAR_ID in .env.")


@app.context_processor
def inject_calendar_config():
    """Expose Google Calendar config to all templates."""
    return {
        'PORTAL_CALENDAR_ID': PORTAL_CALENDAR_ID or '',
        'PUBLIC_CALENDAR_ID': PUBLIC_CALENDAR_ID or '',
    }


# Ignore coding style violations for these imports
import obhapp.views  # noqa: E402  pylint: disable=wrong-import-position
import obhapp.model  # noqa: E402  pylint: disable=wrong-import-position
