"""Omega Beta Eta package initializer."""
import flask
from dotenv import load_dotenv
import os
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build

# app is a single object used by all the code modules in this package
app = flask.Flask(__name__)  # pylint: disable=invalid-name

# Read settings from config module (obhapp/config.py)
app.config.from_object('obhapp.config')

app.debug = True

# Load environment variables
load_dotenv()

# Access the service account file path and calendar ID from environment variables
SERVICE_ACCOUNT_FILE = os.getenv('omegabetaeta-a2a6d02aedd3.json')  # Path to the service account JSON file
PORTAL_CALENDAR_ID = os.getenv('PORTAL_CALENDAR_ID')  # Calendar ID for the private calendar

# Ensure necessary environment variables are set
if not SERVICE_ACCOUNT_FILE or not PORTAL_CALENDAR_ID:
    raise EnvironmentError("SERVICE_ACCOUNT_FILE or PORTAL_CALENDAR_ID not set in the environment variables.")

@app.route('/get-events', methods=['GET'])
def get_events():
    """Return the events for the calendar using a service account."""
    try:
        # Set up credentials using the service account JSON file
        SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )

        # Build the calendar service
        service = build('calendar', 'v3', credentials=credentials)

        # Fetch events from the calendar
        events_result = service.events().list(calendarId=PORTAL_CALENDAR_ID).execute()
        events = events_result.get('items', [])

        return flask.jsonify(events)

    except Exception as e:
        # Log the error for debugging
        print(f"Error fetching events: {e}")
        return flask.jsonify({'error': str(e)}), 500

# Ignore coding style violations for these imports
import obhapp.views  # noqa: E402  pylint: disable=wrong-import-position
import obhapp.model  # noqa: E402  pylint: disable=wrong-import-position
