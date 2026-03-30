# Deployment Guide — Render.com

## Why Render?

**Best fit for this project.** Here's why the other options don't work well:

- **GitHub Pages** — static hosting only, can't run Flask/Python. Eliminated.
- **Supabase** — great database, but you'd need to rewrite every SQL query from SQLite to PostgreSQL and rebuild the auth system. Major effort for no benefit.
- **AWS** (EC2/Lightsail) — cheapest raw price ($3.50/mo) but you'd manage your own server: install nginx, configure SSL certificates, set up systemd services, handle OS updates, security patches, firewall rules. Not maintainable by someone with little code experience.
- **Render** — connects to your GitHub repo, auto-deploys when you push, manages SSL and the server for you. Dashboard handles env vars, logs, and restarts. The $7/mo Starter plan gives persistent disk (needed for SQLite + uploaded photos). This is the right tradeoff between cost and ease of maintenance.

**Cost: $7/month** (Starter plan for persistent disk). Free tier won't work because the disk resets on every deploy — you'd lose all uploaded photos and the database.

---

## Step-by-Step Deployment

### Step 1: Push to GitHub
Create a private GitHub repo and push the code. Make sure these are **NOT** committed (already in .gitignore):
- `.env` (has your email password, calendar IDs)
- `var/` (database + uploads — these live on the server)
- `env/` (virtual environment)
- `*.json` (service account key file)

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin git@github.com:YOUR_USERNAME/omegabetaeta.git
git push -u origin main
```

### Step 2: Create a Render account
Go to [render.com](https://render.com) and sign up (connect your GitHub account).

### Step 3: Create a new Web Service
1. Click **New → Web Service**
2. Connect your GitHub repo
3. Settings:
   - **Name**: `omegabetaeta` (or whatever you want)
   - **Region**: Oregon (or closest to you)
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 3 -b 0.0.0.0:$PORT obhapp:app`
   - **Plan**: Starter ($7/mo)

### Step 4: Add a persistent disk
1. In your service settings, go to **Disks**
2. Click **Add Disk**
3. Settings:
   - **Name**: `obh-data`
   - **Mount Path**: `/var/data`
   - **Size**: 1 GB (plenty for photos + database)

### Step 5: Set environment variables
In the Render dashboard → **Environment** tab, add these:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | (generate one — run `python3 -c "import secrets; print(secrets.token_hex(32))"`) |
| `FLASK_ENV` | `production` |
| `RENDER_DISK_PATH` | `/var/data` |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | (paste the entire contents of your `omegabetaeta-*.json` service account file) |
| `PORTAL_CALENDAR_ID` | (your portal calendar ID from .env) |
| `PUBLIC_CALENDAR_ID` | (your public calendar ID from .env) |
| `EMAIL_ADDRESS` | `omegabetaeta@umich.edu` |
| `EMAIL_PASSWORD` | (your app password) |
| `SITE_URL` | `https://omegabetaeta.onrender.com` (or your custom domain) |

### Step 6: Initialize the database (first deploy only)
After the first deploy, open the **Shell** tab in Render and run:
```bash
./bin/obhdb fill
```
This creates the database and populates it with brothers/roles. You only do this once — the persistent disk keeps it alive across deploys.

### Step 7: Custom domain (optional)
1. In Render → **Settings → Custom Domains**, add `omegabetaeta.org`
2. In your domain registrar's DNS settings, add the CNAME record Render gives you
3. Render auto-provisions an SSL certificate

---

## Maintenance Guide (for future board members)

### To update the website:
1. Edit code locally
2. `git add . && git commit -m "description" && git push`
3. Render auto-deploys. Done.

### To add brothers:
Use the portal — Board page → manage members. No code needed.

### To rebuild the database (nuclear option):
Open Render **Shell** tab:
```bash
./bin/obhdb fill
```
**Warning**: this resets ALL data (brothers, gallery, messages, etc.) to defaults.

### To check logs:
Render dashboard → **Logs** tab. Shows live server output and errors.

### To restart:
Render dashboard → **Manual Deploy → Clear build cache & deploy**.

### Environment variables:
If email stops working (password expired) or calendar IDs change, update them in Render **Environment** tab. No code changes needed.

---

## Code changes already made

Three files were modified to support Render deployment:

1. **`obhapp/config.py`** — `SECRET_KEY` reads from env var (falls back to dev key). `UPLOAD_FOLDER` and `DATABASE_FILENAME` use `RENDER_DISK_PATH` when set (persistent disk). `DEBUG` mode off in production.

2. **`obhapp/__init__.py`** — Accepts `GOOGLE_SERVICE_ACCOUNT_JSON` env var as alternative to a file on disk (writes it to a temp file at startup). No more need to manually place the JSON file on the server.

3. **`render.yaml`** — Blueprint file so Render can auto-configure the service. Optional but convenient.