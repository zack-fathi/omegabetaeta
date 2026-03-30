# Deployment Guide — AWS EC2 + GitHub Actions

## Architecture
- **EC2 instance** (Amazon Linux) runs the Flask app via Gunicorn
- **Nginx** sits in front as a reverse proxy (serves static files, handles SSL)
- **GitHub Actions** auto-deploys when you push to `main`
- **SQLite** database + uploads live on the EC2 disk

**Cost: ~$3.50/month** (t2.micro or t3.micro with free tier, then ~$8/mo after)


## Step-by-Step (once SSH works)

### Step 1: Move your key to a safe place
```bash
cp Jawad.pem ~/.ssh/obh.pem    # (or whichever key works)
chmod 600 ~/.ssh/obh.pem
```
Then use `./bin/ssh-server` to connect easily.

### Step 2: Set up the server (one time)
```bash
# Copy the setup script to the server
scp -i "Jawad.pem" deploy/server-setup.sh ec2-user@ec2-18-119-117-254.us-east-2.compute.amazonaws.com:~

# SSH in and run it
./bin/ssh-server
sudo chmod +x server-setup.sh && sudo ./server-setup.sh
```
This installs Python, nginx, creates the `obh` user, systemd service, etc.

### Step 3: Clone the repo on the server
```bash
# Still SSH'd in:
sudo -u obh -i
git clone https://github.com/Javv4d/omegabetaeta.git
cd omegabetaeta
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### Step 4: Create the .env file on the server
```bash
# As the obh user, in /home/obh/omegabetaeta:
cp deploy/.env.example .env
nano .env   # fill in real values
```
You need:
- `SECRET_KEY` — generate with `python3 -c "import secrets; print(secrets.token_hex(32))"`
- `PORTAL_CALENDAR_ID` / `PUBLIC_CALENDAR_ID` — from your local `.env`
- `EMAIL_PASSWORD` — your app password
- `SERVICE_ACCOUNT_FILE` — path to the Google service account JSON

### Step 5: Copy the Google service account JSON to the server
```bash
# From your laptop (not SSH'd in):
scp -i "Jawad.pem" omegabetaeta-*.json ec2-user@ec2-18-119-117-254.us-east-2.compute.amazonaws.com:/tmp/sa.json

# Then SSH in and move it:
./bin/ssh-server
sudo mv /tmp/sa.json /home/obh/omegabetaeta/service-account.json
sudo chown obh:obh /home/obh/omegabetaeta/service-account.json
sudo chmod 600 /home/obh/omegabetaeta/service-account.json
```

### Step 6: Initialize the database
```bash
# SSH'd in as obh:
sudo -u obh -i
cd omegabetaeta
source env/bin/activate
./bin/obhdb fill
```

### Step 7: Start the app
```bash
sudo systemctl start obhapp
sudo systemctl status obhapp   # should say "active (running)"
```
Visit `http://YOUR_EC2_IP` — you should see the site.

### Step 8: Set up SSL (optional, when you have a domain)
```bash
sudo certbot --nginx -d omegabetaeta.org -d www.omegabetaeta.org
```
Certbot auto-renews. Point your domain's DNS A record to the EC2 public IP.

### Step 9: Set up GitHub Actions (auto-deploy on push)
1. Go to your GitHub repo → **Settings → Secrets and Variables → Actions**
2. Add these repository secrets:
   - `EC2_HOST` = `ec2-18-119-117-254.us-east-2.compute.amazonaws.com` (your instance DNS)
   - `EC2_SSH_KEY` = paste the **entire contents** of your `.pem` private key file
3. Also give the `obh` user permission to restart the service:
```bash
# SSH into server:
echo "obh ALL=(root) NOPASSWD: /bin/systemctl restart obhapp" | sudo tee /etc/sudoers.d/obh-restart
```
4. Push to `main` — Actions will SSH in and deploy automatically.

---

## Maintenance Guide (for future board members)

### To update the website:
```bash
git add . && git commit -m "description" && git push
```
GitHub Actions auto-deploys. Done.

### To SSH in manually:
```bash
./bin/ssh-server
```

### To check server status:
```bash
./bin/ssh-server "sudo systemctl status obhapp"
```

### To view logs:
```bash
./bin/ssh-server "sudo journalctl -u obhapp -n 50 --no-pager"
```

### To restart the app:
```bash
./bin/ssh-server "sudo systemctl restart obhapp"
```

### To rebuild the database (nuclear — resets ALL data):
```bash
./bin/ssh-server
sudo -u obh -i
cd omegabetaeta && source env/bin/activate
./bin/obhdb fill
sudo systemctl restart obhapp
```

---

## Files created/modified

| File | Purpose |
|------|---------|
| `bin/ssh-server` | SSH convenience script — finds your key and connects |
| `deploy/server-setup.sh` | One-time server config (nginx, systemd, users) |
| `deploy/deploy.sh` | Pulls code + restarts app (called by GitHub Actions) |
| `deploy/.env.example` | Template for server environment variables |
| `.github/workflows/deploy.yml` | GitHub Actions workflow — deploy on push to main |
| `obhapp/config.py` | Updated — reads SECRET_KEY from env var |
| `obhapp/__init__.py` | Updated — debug off in production, JSON env var support |