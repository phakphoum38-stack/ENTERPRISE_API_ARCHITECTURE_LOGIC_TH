Research OS — development scaffold

Overview
--------
This folder contains a minimal scaffold for Research OS: a small Python service,
an installer script, a systemd unit, basic tests, and runbooks for installation
and release gating. Use these as a starting point to integrate into the main
repository workflows.

Quick start
-----------
1. Install dependencies: `pip install -r requirements.txt`
2. Run locally: `python -m research_os.app.main`
3. Install systemd service: run `installer/install.sh` as root.
