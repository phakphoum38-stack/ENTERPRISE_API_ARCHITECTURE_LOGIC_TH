# Install Research OS

Steps
1. Review `research-os/installer/install.sh`.
2. Run `bash research-os/installer/install.sh` as a user with `sudo` privileges.
3. Verify service status: `systemctl status research-os.service`.

Notes
- Installer copies the unit to `/etc/systemd/system/research-os.service` and enables it.
- Modify `WorkingDirectory` in the unit file to your installed location (default `/opt/research-os`).
