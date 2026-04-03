"""omegabetaeta configuration."""

import os
import pathlib

# Root of this application, useful if it doesn't occupy an entire domain
APPLICATION_ROOT = '/'

# Secret key for encrypting cookies
# In production, set SECRET_KEY env var. Falls back to dev key for local use.
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-change-me')
SESSION_COOKIE_NAME = 'login'

# Data directory: on the server, /home/obh/omegabetaeta/var. Locally, var/.
OBHAPP_ROOT = pathlib.Path(__file__).resolve().parent.parent
_DATA_DIR = OBHAPP_ROOT / 'var'

# File Upload
UPLOAD_FOLDER = _DATA_DIR / 'uploads'
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Database
DATABASE_FILENAME = _DATA_DIR / 'obhapp.sqlite3'

# reCAPTCHA
RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '')
RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '')


