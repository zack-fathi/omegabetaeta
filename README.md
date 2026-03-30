# OBH App

OBH App is a full-stack web application developed for the Omega Beta Eta fraternity. It serves as a comprehensive platform for both public engagement and internal fraternity management, blending modern design with powerful functionality.

## Features

### Public Website
- **Event Calendar**: Displays fraternity events dynamically, powered by **FullCalendar** and synchronized with Google Calendar.
- **Photo Gallery**: Showcases fraternity memories through a visually appealing gallery.
- **Donation Portal**: Enables secure online donations from members and supporters.

### Member Portal
Accessible only to fraternity members with role-based permissions:
- **Recruit Management**: Tracks and manages recruits, supporting transitions to active members.
- **Member Directory**: Categorizes members by their fraternity line with detailed profiles.
- **Account Management**: Allows members to update their profiles and manage personal details.
- **Password Management**: Admins/Presidents can generate and email unique default passwords to brothers. First-time login requires a password change.
- **Email Notifications**: Automatic confirmation emails for contact messages and applications. Portal message replies are sent via email.
- **Change Log**: Logs key actions for transparency and accountability.

## Technologies Used
- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, Bootstrap, JavaScript
  - Includes **FullCalendar** for interactive event displays.
- **Database**: SQLite
- **Hosting**: AWS
- **Integrations**: Google Calendar API, FullCalendar

## Live Demo
Explore the live web app: [OBH App](http://18.119.117.254/)

## Email Configuration
Add the following to your `.env` file to enable email functionality:
```
EMAIL_ADDRESS=omegabetaeta@umich.edu
EMAIL_PASSWORD=your-app-password
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
SITE_URL=https://omegabetaeta.org
```
For Google Workspace / Gmail, use an [App Password](https://support.google.com/accounts/answer/185833) for `EMAIL_PASSWORD`.

## Database Migration
If upgrading an existing database, run:
```bash
sqlite3 var/obhapp.sqlite3 < sql/migrate_email_passwords.sql
```

## Developer
Developed by Jawad Alsahlani and Zackery Fathi.

For inquiries or support, contact: [jawadals@umich.edu](mailto:jawadals@umich.edu).
