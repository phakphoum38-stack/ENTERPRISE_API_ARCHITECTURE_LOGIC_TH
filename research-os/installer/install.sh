#!/usr/bin/env bash
set -euo pipefail

# Simple installer: installs dependencies and copies systemd unit
ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
echo "Installing Research OS from $ROOT_DIR"

if command -v pip >/dev/null 2>&1; then
  pip install -r "$ROOT_DIR/requirements.txt"
fi

SERVICE_DEST=/etc/systemd/system/research-os.service
echo "Installing systemd unit to $SERVICE_DEST (requires sudo)"
sudo cp "$ROOT_DIR/service/research-os.service" "$SERVICE_DEST"
sudo systemctl daemon-reload
sudo systemctl enable --now research-os.service
echo "Research OS installed and service started."
