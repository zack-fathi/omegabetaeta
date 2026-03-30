# Deployment Guide — AWS EC2 + GitHub Actions

## Architecture

```
Your laptop                          AWS EC2 (Amazon Linux)
┌─────────────┐    git push         ┌──────────────────────────────────┐
│  VS Code    │ ──────────────────▶ │  GitHub Actions                  │
│  (edit code)│                     │    ↓ SSH in as ec2-user          │
└─────────────┘                     │    ↓ runs deploy/deploy.sh       │
                                    │                                  │
                                    │  nginx (port 80/443)             │
                                    │    ↓ reverse proxy               │
                                    │  gunicorn (port 8000)            │
                                    │    ↓ runs Flask app              │
                                    │  obhapp (your code)              │
                                    │    ↓ reads                       │
                                    │  SQLite DB + uploads (var/)      │
                                    └──────────────────────────────────┘
```

- **EC2 instance** (Amazon Linux 2023) runs the Flask app via Gunicorn
- **Nginx** sits in front as a reverse proxy (serves static files, handles SSL)
- **GitHub Actions** auto-deploys when you push to `main`
- **SQLite** database + uploads live on the EC2 disk

**Cost: ~$3.50/month** (t2.micro or t3.micro with free tier, then ~$8/mo after)

---

## IMPORTANT: Two Users on the Server

The server has two users. You **must** know which one you're using:

| User | How to become | Can do | Prompt looks like |
|------|---------------|--------|-------------------|
| `ec2-user` | You land here when you SSH in | `sudo` anything (install packages, start/stop services, edit system files) | `[ec2-user@ip-... ~]$` |
| `obh` | Run `sudo -u obh -i` from ec2-user | Run app commands (git pull, pip install, ./bin/obhdb, edit .env) — NO sudo except `sudo systemctl restart obhapp` | `[obh@ip-... ~]$` |

**To switch users:**
- **ec2-user → obh:** `sudo -u obh -i`
- **obh → ec2-user:** `exit` (or press Ctrl+D)

**Rule of thumb:** If a command starts with `sudo`, you probably need to be `ec2-user`. If it's an app command (git, pip, python), you need to be `obh`.

---

## Server Details

| Item | Value |
|------|-------|
| EC2 hostname | `ec2-18-119-117-254.us-east-2.compute.amazonaws.com` |
| SSH key file | `Jawad.pem` (keep this safe — it's the ONLY way to access the server) |
| SSH username | `ec2-user` |
| App user | `obh` |
| App directory | `/home/obh/omegabetaeta` |
| Database | `/home/obh/omegabetaeta/var/obhapp.sqlite3` |
| Uploads | `/home/obh/omegabetaeta/var/uploads/` |
| Environment file | `/home/obh/omegabetaeta/.env` |
| Service account | `/home/obh/omegabetaeta/service-account.json` |
| Nginx config | `/etc/nginx/conf.d/omegabetaeta.conf` |
| Systemd service | `/etc/systemd/system/obhapp.service` |
| Python venv | `/home/obh/omegabetaeta/env/` |
| GitHub repo | `https://github.com/Javv4d/omegabetaeta.git` |

---

## Step-by-Step Setup

### Step 1: SSH into the server

From your laptop, in the `omegabetaeta` project folder:
```bash
./bin/ssh-server
```

This runs: `ssh -i "Jawad.pem" ec2-user@ec2-18-119-117-254.us-east-2.compute.amazonaws.com`

**If it says "Permission denied":**
- Make sure `Jawad.pem` is in the same folder as `bin/ssh-server`
- Run `chmod 600 Jawad.pem` to fix permissions
- Make sure you're using the right key (the one you assigned when creating the EC2 instance)

**You are now: `ec2-user`**

---

### Step 2: Set up the server (one time — already done)

```bash
# FROM YOUR LAPTOP (not SSH'd in) — copy the setup script to the server:
scp -i "Jawad.pem" deploy/server-setup.sh ec2-user@ec2-18-119-117-254.us-east-2.compute.amazonaws.com:~

# Then SSH in:
./bin/ssh-server

# Run the setup script (you should be ec2-user):
sudo chmod +x server-setup.sh && sudo ./server-setup.sh
```

**What this does:**
1. Installs Python 3, pip, nginx, git, sqlite
2. Installs certbot (for SSL later)
3. Creates the `obh` user
4. Creates the nginx config at `/etc/nginx/conf.d/omegabetaeta.conf`
5. Creates the systemd service at `/etc/systemd/system/obhapp.service`
6. Sets up sudoers so ec2-user can run commands as obh
7. Sets up sudoers so obh can run `sudo systemctl restart obhapp`
8. Starts and enables nginx

**✅ This step is already done.**

---

### Step 3: Clone the repo on the server (already done)

```bash
# You should be SSH'd in as ec2-user. Switch to obh:
sudo -u obh -i

# You are now obh. Clone the repo:
cd ~
git clone https://github.com/Javv4d/omegabetaeta.git
cd omegabetaeta

# Create a Python virtual environment:
python3 -m venv env

# Activate it:
source env/bin/activate

# Your prompt should now show (env) at the beginning like:
#   (env) [obh@ip-... omegabetaeta]$

# Install all Python packages:
pip install -r requirements.txt
```

**✅ This step is already done.**

---

### Step 4: Create the .env file on the server (already done)

```bash
# As obh, in /home/obh/omegabetaeta:
nano .env
```

Paste this and fill in real values:
```
FLASK_ENV=production
SECRET_KEY=<paste a 64-character hex string>
SERVICE_ACCOUNT_FILE=/home/obh/omegabetaeta/service-account.json
PORTAL_CALENDAR_ID=<your portal calendar ID from local .env>
PUBLIC_CALENDAR_ID=<your public calendar ID from local .env>
EMAIL_ADDRESS=omegabetaeta@umich.edu
EMAIL_PASSWORD=<your app password>
SITE_URL=https://omegabetaeta.org
```

**To generate a SECRET_KEY**, run this on the server:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
Copy the output and paste it as the SECRET_KEY value.

**To get PORTAL_CALENDAR_ID and PUBLIC_CALENDAR_ID**, look at your local `.env` file on your laptop.

Press `Ctrl+O` then `Enter` to save in nano, then `Ctrl+X` to exit.

**✅ This step is already done.**

---

### Step 5: Copy the Google service account JSON to the server (already done)

```bash
# FROM YOUR LAPTOP (a new terminal, not SSH'd in):
scp -i "Jawad.pem" omegabetaeta-491520-73254a68b583.json ec2-user@ec2-18-119-117-254.us-east-2.compute.amazonaws.com:/tmp/sa.json

# Now SSH in as ec2-user:
./bin/ssh-server

# Move the file to the right place and fix ownership:
sudo mv /tmp/sa.json /home/obh/omegabetaeta/service-account.json
sudo chown obh:obh /home/obh/omegabetaeta/service-account.json
sudo chmod 600 /home/obh/omegabetaeta/service-account.json
```

**✅ This step is already done.**

---

### Step 6: Initialize the database (already done)

```bash
# SSH in and switch to obh:
./bin/ssh-server
sudo -u obh -i

# Go to the app directory and activate the venv:
cd omegabetaeta
source env/bin/activate

# Fill the database:
./bin/obhdb fill
```

You should see output like: `Inserted 77 brothers`.

**✅ This step is already done.**

---

### Step 7: Start the app ← YOU ARE HERE

This is the step that actually makes the website live. There are several things that can go wrong, so follow carefully.

#### 7a. First, make sure gunicorn is installed on the server

The systemd service runs gunicorn from `/home/obh/omegabetaeta/env/bin/gunicorn`. If it's not there, the app won't start.

```bash
# SSH into the server:
./bin/ssh-server

# Switch to obh:
sudo -u obh -i

# Go to the app directory and activate venv:
cd omegabetaeta
source env/bin/activate

# Check if gunicorn is installed:
which gunicorn
```

**If it prints** `/home/obh/omegabetaeta/env/bin/gunicorn` → gunicorn is installed, skip to 7b.

**If it says** `gunicorn not found` → you need to install it:
```bash
pip install gunicorn
```

Then verify:
```bash
which gunicorn
# Should print: /home/obh/omegabetaeta/env/bin/gunicorn
```

#### 7b. Pull the latest code (if you made changes on your laptop)

If you committed and pushed changes from your laptop (like the gunicorn fix), pull them:
```bash
# Still as obh, in /home/obh/omegabetaeta with venv activated:
git pull origin main
pip install -r requirements.txt
```

#### 7c. Test that the app can start manually (optional but recommended)

Before using systemd, test that gunicorn actually works:
```bash
# Still as obh, with venv activated:
cd /home/obh/omegabetaeta
source env/bin/activate
env/bin/gunicorn -w 1 -b 127.0.0.1:8000 obhapp:app
```

**If it works**, you'll see something like:
```
  ✓ PUBLIC calendar OK: ...
  ✓ PORTAL calendar OK: ...
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://127.0.0.1:8000
[INFO] Using worker: sync
[INFO] Booting worker with pid: ...
```
Press `Ctrl+C` to stop it. Proceed to 7d.

**If it says `FATAL: Missing required .env variables: ...`:**
- Your `.env` file is missing or has blank values
- Check it: `cat /home/obh/omegabetaeta/.env`
- Edit it: `nano /home/obh/omegabetaeta/.env`
- Make sure every line has a real value (no `CHANGE_ME` or `your_..._here` left)

**If it says `FATAL: SERVICE_ACCOUNT_FILE not found: ...`:**
- The service account JSON file is missing
- Check: `ls -la /home/obh/omegabetaeta/service-account.json`
- If it's not there, redo Step 5

**If it says `FATAL: Cannot access PUBLIC/PORTAL calendar`:**
- The Google Calendar isn't shared with the service account email
- Open the service account JSON and find the `client_email` field
- Go to Google Calendar → Settings for the calendar → Share → add that email with "See all event details"

**If it says `ModuleNotFoundError: No module named '...'`:**
- A Python package is missing
- Run: `pip install -r requirements.txt`

#### 7d. Start the app with systemd

Now use systemd to run it permanently (survives reboots, auto-restarts on crash):

```bash
# IMPORTANT: You must be ec2-user for this, NOT obh.
# If you're obh, type 'exit' first to go back to ec2-user.
exit

# Now you should see [ec2-user@...] in your prompt.
# Start the service:
sudo systemctl start obhapp

# Check if it's running:
sudo systemctl status obhapp
```

**If status says `active (running)`** → SUCCESS! Go to 7e.

**If status says `failed` or `inactive`**, check the logs:
```bash
sudo journalctl -u obhapp -n 30 --no-pager
```

Common errors in the logs:
- `gunicorn: not found` → gunicorn isn't installed, go back to 7a
- `FATAL: Missing required .env variables` → .env is wrong, go back to 7c
- `FATAL: SERVICE_ACCOUNT_FILE not found` → service account JSON missing, redo Step 5
- `Permission denied` on a file → fix ownership: `sudo chown -R obh:obh /home/obh/omegabetaeta`
- `Address already in use` → something else is using port 8000. Kill it: `sudo fuser -k 8000/tcp` then try again

#### 7e. Check nginx is running

Nginx should already be running (from Step 2). Verify:
```bash
# As ec2-user:
sudo systemctl status nginx
```

If it's not running:
```bash
sudo nginx -t          # test the config for errors
sudo systemctl start nginx
```

#### 7f. Visit the website

Open your browser and go to:
```
http://ec2-18-119-117-254.us-east-2.compute.amazonaws.com
```

**If you see the OBH website** → Step 7 is done!

**If you see "Welcome to nginx"** (the default nginx page):
- The default server block is overriding the OBH config
- Fix it:
```bash
# As ec2-user:
sudo nano /etc/nginx/nginx.conf
```
- Find any `server { ... }` block inside the `http { ... }` block that has `listen 80`
- Delete that entire server block (the lines from `server {` to its matching `}`)
- Save and exit nano (Ctrl+O, Enter, Ctrl+X)
- Test and reload:
```bash
sudo nginx -t && sudo systemctl reload nginx
```
- Refresh the browser

**If you see "502 Bad Gateway":**
- Nginx is running but can't reach gunicorn
- Check that obhapp is running: `sudo systemctl status obhapp`
- If it's not, start it: `sudo systemctl start obhapp`

**If the page won't load at all (connection refused/timeout):**
- Check the EC2 Security Group in AWS Console
- Go to EC2 → Instances → click your instance → Security tab → click the security group
- Make sure there's an inbound rule allowing HTTP (port 80) from 0.0.0.0/0
- Also allow HTTPS (port 443) from 0.0.0.0/0 for later

---

### Step 8: Set up SSL (when you have a domain)

You need a domain name pointed at your server first. If you own `omegabetaeta.org`:

#### 8a. Point DNS to EC2
- Go to your domain registrar (Namecheap, GoDaddy, etc.)
- Add an **A record**: `@` → `18.119.117.254` (your EC2 public IP)
- Add an **A record**: `www` → `18.119.117.254`
- DNS can take up to 48 hours to propagate (usually 5–30 minutes)

#### 8b. Run certbot
```bash
# SSH in as ec2-user:
./bin/ssh-server

# Run certbot (it modifies your nginx config automatically):
sudo certbot --nginx -d omegabetaeta.org -d www.omegabetaeta.org
```
- Enter your email when asked
- Agree to terms
- Choose to redirect HTTP to HTTPS when asked

Certbot auto-renews. Your site is now HTTPS.

---

### Step 9: Set up GitHub Actions (auto-deploy on push)

This makes it so every time you push to `main`, the website updates automatically.

#### 9a. Add GitHub secrets
1. Go to `https://github.com/Javv4d/omegabetaeta` in your browser
2. Click **Settings** (tab at the top)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add these two secrets:

| Name | Value |
|------|-------|
| `EC2_HOST` | `ec2-18-119-117-254.us-east-2.compute.amazonaws.com` |
| `EC2_SSH_KEY` | Open `Jawad.pem` in a text editor, copy the ENTIRE contents (including the `-----BEGIN` and `-----END` lines), paste it here |

#### 9b. Verify the sudoers rule on the server

The deploy script needs `obh` to restart the app. This should already be set up from Step 2, but verify:
```bash
# SSH in:
./bin/ssh-server

# Check the sudoers file exists:
sudo cat /etc/sudoers.d/obh-restart
```

It should say: `obh ALL=(root) NOPASSWD: /bin/systemctl restart obhapp`

If it doesn't exist:
```bash
echo "obh ALL=(root) NOPASSWD: /bin/systemctl restart obhapp" | sudo tee /etc/sudoers.d/obh-restart
```

#### 9c. Push and test

From your laptop:
```bash
# Make a small change to any file, then:
git add .
git commit -m "test auto-deploy"
git push origin main
```

Go to `https://github.com/Javv4d/omegabetaeta/actions` to watch the workflow run. It should complete in about 30 seconds.

---

## Maintenance Guide (for future board members)

### To update the website:
Just push to main and it auto-deploys:
```bash
git add .
git commit -m "description of what you changed"
git push origin main
```
Go to https://github.com/Javv4d/omegabetaeta/actions to confirm it deployed.

### To SSH into the server:
```bash
cd omegabetaeta   # make sure you're in the project folder
./bin/ssh-server
```
You land as `ec2-user`. To run app commands, switch to obh: `sudo -u obh -i`

### To check if the app is running:
```bash
./bin/ssh-server
sudo systemctl status obhapp
```
Should say `active (running)`.

### To view app logs (if something is broken):
```bash
./bin/ssh-server
sudo journalctl -u obhapp -n 50 --no-pager
```
This shows the last 50 log lines. Increase 50 to see more.

### To restart the app:
```bash
./bin/ssh-server
sudo systemctl restart obhapp
```

### To rebuild the database (CAUTION — erases ALL data, resets everything):
```bash
./bin/ssh-server
sudo -u obh -i
cd omegabetaeta
source env/bin/activate
./bin/obhdb fill
exit
sudo systemctl restart obhapp
```

### To manually deploy (if GitHub Actions isn't working):
```bash
./bin/ssh-server
sudo -u obh -i
cd omegabetaeta
source env/bin/activate
git pull origin main
pip install -r requirements.txt
exit
sudo systemctl restart obhapp
```

### To check nginx logs:
```bash
./bin/ssh-server
sudo tail -50 /var/log/nginx/error.log
sudo tail -50 /var/log/nginx/access.log
```

---

## If You Lose Access to the Server

The `Jawad.pem` key file is the ONLY way to SSH into the server. If you lose it:
1. You can NOT recover it — AWS does not store private keys
2. You would need to create a new EC2 instance and redo everything
3. **Back up `Jawad.pem` somewhere safe** (Google Drive, password manager, etc.)

---

## Files created/modified

| File | Purpose |
|------|---------|
| `bin/ssh-server` | SSH convenience script — connects to the server |
| `deploy/server-setup.sh` | One-time server setup (nginx, systemd, users) — already ran |
| `deploy/deploy.sh` | Pulls code + restarts app (called by GitHub Actions) |
| `deploy/.env.example` | Template for server environment variables |
| `.github/workflows/deploy.yml` | GitHub Actions workflow — auto-deploys on push to main |
| `obhapp/config.py` | Updated — reads SECRET_KEY from env var |
| `obhapp/__init__.py` | Updated — debug off in production, validates .env at startup |