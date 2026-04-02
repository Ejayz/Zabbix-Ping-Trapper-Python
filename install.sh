#!/bin/bash

set -e

REPO_URL="https://github.com/Ejayz/Zabbix-Ping-Trapper-Python.git"
APP_DIR="/opt/Zabbix-Ping-Trapper-Python"
SERVICE_NAME="zabbix-ping-trapper-py"

echo "======================================"
echo " Installing Zabbix Ping Trapper"
echo "======================================"


echo "[1/6] Updating system packages..."
apt update -y


echo "[2/6] Installing Python and tools..."
apt install -y python3 python3-pip python3-venv git


echo "[3/6] Cloning repository..."
if [ -d "$APP_DIR" ]; then
    echo "Directory exists. Removing old version..."
    rm -rf "$APP_DIR"
fi

git clone "$REPO_URL" "$APP_DIR"
pip install zabbix_utils
pip install icmplib
cd "$APP_DIR"


echo "[4/6] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate


echo "[5/6] Installing Python dependencies..."
pip install --upgrade pip


if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "No requirements.txt found, installing core dependencies..."
    pip install zabbix-utils icmplib apscheduler
fi

# --- Create systemd service ---
echo "[6/6] Creating systemd service..."

cat <<EOF > /etc/systemd/system/${SERVICE_NAME}.service
[Unit]
Description=Zabbix Ping Trapper Python Service
After=network.target

[Service]
Type=simple
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/venv/bin/python ${APP_DIR}/main.py
Restart=always
RestartSec=3
User=root

[Install]
WantedBy=multi-user.target
EOF

# --- Enable and start service ---
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl start ${SERVICE_NAME}

echo "======================================"
echo " INSTALLATION COMPLETE"
echo "======================================"
echo "Service: ${SERVICE_NAME}"
echo "Status:"
systemctl status ${SERVICE_NAME} --no-pager