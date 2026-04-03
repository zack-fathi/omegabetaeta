"""Omega Beta Eta package initializer."""
import flask
from dotenv import load_dotenv
import json
import os
import sys
import tempfile

# Load environment variables before anything else
load_dotenv()

# app is a single object used by all the code modules in this package
app = flask.Flask(__name__)  # pylint: disable=invalid-name

# Read settings from config module (obhapp/config.py)
app.config.from_object('obhapp.config')

app.debug = os.environ.get('FLASK_ENV') != 'production'


@app.context_processor
def inject_user_roles():
    """Return the user roles and permission level for the current session."""
    if "user_id" in flask.session:
        user_id = flask.session["user_id"]
        con = obhapp.model.get_db()
        cur = con.execute(
            "SELECT role_name FROM roles WHERE user_id = ?",
            (user_id,)
        )
        user_roles = {row["role_name"] for row in cur.fetchall()}
        perm_cur = con.execute(
            "SELECT MIN(permission_level) as min_level FROM roles WHERE user_id = ?",
            (user_id,)
        )
        perm_row = perm_cur.fetchone()
        user_perm_level = perm_row["min_level"] if perm_row and perm_row["min_level"] is not None else 99
        return {"user_roles": user_roles, "user_perm_level": user_perm_level}
    return {"user_roles": set(), "user_perm_level": 99}


# Google Calendar integration via service account (calendars stay private)
# Supports either a file path (local/.env) or raw JSON string (env var on server)
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')
_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')

if _SERVICE_ACCOUNT_JSON and not SERVICE_ACCOUNT_FILE:
    # Write the JSON from env var to a temp file so google-auth can read it
    _tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    _tmp.write(_SERVICE_ACCOUNT_JSON)
    _tmp.close()
    SERVICE_ACCOUNT_FILE = _tmp.name

PORTAL_CALENDAR_ID = os.getenv('PORTAL_CALENDAR_ID')
PUBLIC_CALENDAR_ID = os.getenv('PUBLIC_CALENDAR_ID')

# ── Validate calendar config at startup ──
_missing = []
if not SERVICE_ACCOUNT_FILE:
    _missing.append('SERVICE_ACCOUNT_FILE')
if not PORTAL_CALENDAR_ID:
    _missing.append('PORTAL_CALENDAR_ID')
if not PUBLIC_CALENDAR_ID:
    _missing.append('PUBLIC_CALENDAR_ID')
if _missing:
    sys.exit(f"FATAL: Missing required .env variables: {', '.join(_missing)}. "
             "See the Help page in the portal for setup instructions.")

if not os.path.isfile(SERVICE_ACCOUNT_FILE):
    sys.exit(f"FATAL: SERVICE_ACCOUNT_FILE not found: {SERVICE_ACCOUNT_FILE}")

# Verify the service account can reach both calendars
try:
    from google.oauth2 import service_account as _sa
    from googleapiclient.discovery import build as _build

    _creds = _sa.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/calendar.readonly']
    )
    _service = _build('calendar', 'v3', credentials=_creds, cache_discovery=False)

    for _label, _cal_id in [('PUBLIC', PUBLIC_CALENDAR_ID), ('PORTAL', PORTAL_CALENDAR_ID)]:
        try:
            _service.calendars().get(calendarId=_cal_id).execute()
            print(f"  ✓ {_label} calendar OK: {_cal_id}")
        except Exception as e:
            sys.exit(
                f"FATAL: Cannot access {_label} calendar ({_cal_id}).\n"
                f"  Error: {e}\n"
                f"  Make sure the calendar is shared with the service account email."
            )
    del _creds, _service, _sa, _build, _label, _cal_id
except Exception as e:
    sys.exit(f"FATAL: Failed to initialize Google Calendar service: {e}")

print("Google Calendar integration verified.")


@app.context_processor
def inject_calendar_config():
    """Expose Google Calendar config to all templates."""
    return {
        'PORTAL_CALENDAR_ID': PORTAL_CALENDAR_ID or '',
        'PUBLIC_CALENDAR_ID': PUBLIC_CALENDAR_ID or '',
    }


import re as _re
import markupsafe as _markupsafe

@app.template_filter('nl2br')
def nl2br_filter(s):
    """Convert newlines to <br> tags and auto-link URLs."""
    if not s:
        return s
    s = str(_markupsafe.escape(s))
    # Auto-link URLs
    s = _re.sub(
        r'(https?://[^\s<]+)',
        r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>',
        s
    )
    s = s.replace('\n', '<br>')
    return _markupsafe.Markup(s)


# Ignore coding style violations for these imports
import obhapp.views  # noqa: E402  pylint: disable=wrong-import-position
import obhapp.model  # noqa: E402  pylint: disable=wrong-import-position
