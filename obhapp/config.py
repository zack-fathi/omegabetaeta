"""omegabetaeta development configuration."""

import pathlib

# Root of this application, useful if it doesn't occupy an entire domain
APPLICATION_ROOT = '/'

# Secret key for encrypting cookies
s = b'\xbf\x8d\x9d\xc6\xd9\x0c\xf3\x97}\x85tZ"'
k = b'\x92\xf6\r\xca\xaf\x8f\x14\xf7\xd8V\xd6'
SECRET_KEY = s + k
SESSION_COOKIE_NAME = 'login'

# File Upload to var/uploads/
OBHAPP_ROOT = pathlib.Path(__file__).resolve().parent.parent
UPLOAD_FOLDER = OBHAPP_ROOT/'var'/'uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Database file is var/insta485.sqlite3
DATABASE_FILENAME = OBHAPP_ROOT/'var'/'obhapp.sqlite3'
