#!/bin/bash
set -euo pipefail

# Deployment script for the Taj Elite site (static HTML).
# Runs on the remote server via SSH, same setup as Turathna:
# files in $WEB_ROOT, served by `serve` as a systemd service on $APP_PORT.
# It does not touch Turathna's service (port 8004) or its nginx config.

WEB_ROOT="${WEB_ROOT:-/var/www/taj-elite-demo}"
SERVER_USER="${SERVER_USER:?SERVER_USER is required}"
BUILD_DIR="${BUILD_DIR:-/tmp/taj-elite-demo-dist}"
APP_PORT="${APP_PORT:-8020}"
SERVICE_NAME="taj-elite-demo.service"

echo "Starting deployment..."
echo "Web Root: $WEB_ROOT"
echo "App Port: $APP_PORT"

# Refuse to run with an unsafe web root (protects the rm -rf below)
case "$WEB_ROOT" in
  /var/www/?*) ;;
  *) echo "Refusing to deploy: WEB_ROOT must be under /var/www/ (got '$WEB_ROOT')"; exit 1 ;;
esac

# Node.js + serve (already present on the server for Turathna; installed only if missing)
if ! command -v node &> /dev/null; then
  echo "Installing Node.js 20.x..."
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi
if ! command -v serve &> /dev/null; then
  sudo npm install -g serve
fi
SERVE_BIN="$(command -v serve)"

# Make sure the port is not already taken by something else
if sudo ss -ltnp | grep -q ":$APP_PORT " && ! sudo ss -ltnp | grep ":$APP_PORT " | grep -q serve; then
  echo "Port $APP_PORT is used by another process. Pick another APP_PORT."; exit 1
fi

if [ ! -d "$BUILD_DIR" ]; then
  echo "Error: Build directory $BUILD_DIR not found!"; exit 1
fi

echo "Deploying files..."
sudo mkdir -p "$WEB_ROOT"
sudo rm -rf "${WEB_ROOT:?}"/*
sudo cp -r "$BUILD_DIR"/* "$WEB_ROOT"/
sudo chown -R "$SERVER_USER:$SERVER_USER" "$WEB_ROOT"
sudo chmod -R 755 "$WEB_ROOT"
rm -rf "$BUILD_DIR"

echo "Writing systemd service..."
sudo tee "/etc/systemd/system/$SERVICE_NAME" > /dev/null <<EOF
[Unit]
Description=Taj Elite Website (demo)
After=network.target

[Service]
Type=simple
User=$SERVER_USER
WorkingDirectory=$WEB_ROOT
ExecStart=$SERVE_BIN $WEB_ROOT -l $APP_PORT --no-clipboard
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"
sleep 2
sudo systemctl is-active "$SERVICE_NAME"
curl -fsS -o /dev/null -w "Local check: HTTP %{http_code}\n" "http://127.0.0.1:$APP_PORT/"

echo "Deployment complete!"
