#!/bin/bash
# ──────────────────────────────────────────────────────────────
# OBH Server Setup Script — run this ONCE on a fresh Amazon Linux EC2
# Usage (from your laptop):
#   scp -i "Jawad.pem" deploy/server-setup.sh ec2-user@YOUR_EC2_IP:~
#   ssh -i "Jawad.pem" ec2-user@YOUR_EC2_IP
#   chmod +x server-setup.sh && sudo ./server-setup.sh
# ──────────────────────────────────────────────────────────────

set -Eeuo pipefail

if [[ "$EUID" -ne 0 ]]; then
  echo "Error: Run with sudo."
  exit 1
fi

APP_USER="obh"
APP_DIR="/home/$APP_USER/omegabetaeta"

echo "=== 1/6 System packages ==="
dnf install -y python3 python3-pip nginx git sqlite 2>/dev/null \
  || yum install -y python3 python3-pip nginx git sqlite

# Install certbot via pip (Amazon Linux doesn't have it in repos)
pip3 install certbot certbot-nginx 2>/dev/null || true

echo "=== 2/6 Create app user ==="
if ! id "$APP_USER" &>/dev/null; then
  useradd -m -s /bin/bash "$APP_USER"
fi
# Let ec2-user deploy as obh
echo "ec2-user ALL=($APP_USER) NOPASSWD: ALL" > /etc/sudoers.d/obh-deploy

echo "=== 3/6 Create app directory ==="
sudo -u "$APP_USER" mkdir -p "$APP_DIR"

echo "=== 4/6 Install nginx config ==="
# Amazon Linux uses conf.d/ instead of sites-available/
cat > /etc/nginx/conf.d/omegabetaeta.conf <<'NGINX'
server {
    listen 80;
    server_name omegabetaeta.org www.omegabetaeta.org _;

    client_max_body_size 20M;

    location /static/ {
        alias /home/obh/omegabetaeta/obhapp/static/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    location /uploads/ {
        alias /home/obh/omegabetaeta/var/uploads/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
NGINX

# Remove the default server block that conflicts on port 80
if grep -q 'listen.*80' /etc/nginx/nginx.conf; then
  sed -i '/server {/,/}/d' /etc/nginx/nginx.conf 2>/dev/null || true
fi

nginx -t && systemctl enable nginx && systemctl start nginx

echo "=== 5/6 Install systemd service ==="
cat > /etc/systemd/system/obhapp.service <<SERVICE
[Unit]
Description=Omega Beta Eta Flask App
After=network.target

[Service]
User=obh
Group=obh
WorkingDirectory=/home/obh/omegabetaeta
EnvironmentFile=/home/obh/omegabetaeta/.env
ExecStart=/home/obh/omegabetaeta/env/bin/gunicorn -w 3 -b 127.0.0.1:8000 obhapp:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable obhapp

echo "=== 6/6 Sudoers for deploy ==="
# Let obh restart its own service
echo "obh ALL=(root) NOPASSWD: /bin/systemctl restart obhapp" > /etc/sudoers.d/obh-restart

echo ""
echo "✅ Server setup complete."
echo ""
echo "Next steps:"
echo "  1. Deploy the code (push to GitHub — Actions will handle it)"
echo "  2. Or manually: sudo -u obh -i, cd omegabetaeta, git clone ..."
echo "  3. Create .env file at /home/obh/omegabetaeta/.env"
echo "  4. Run: ./bin/obhdb fill"
echo "  5. Start: sudo systemctl start obhapp"
echo "  6. SSL: sudo certbot --nginx -d omegabetaeta.org -d www.omegabetaeta.org"
