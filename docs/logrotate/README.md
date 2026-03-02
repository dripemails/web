# Cron Log Rotation Guide

This project writes cron logs to a command-specific file in the repository `logs/` folder, based on the command you run:

- `check_spf.log`
- `send_scheduled_emails.log`
- `process_gmail_emails.log`
- `crawl_imap.log`
- `garbage_collect.log`
- fallback: `cron.log`

The log directory is derived in code from the project root using `Path(__file__).resolve().parent / "logs"`.

## Files in this directory

- `dripemails.conf` - Canonical config for rotating all project log files
- `README.md` - Setup and operational instructions

## 1) Confirm current log files

From project root (`dripemails.org/`):

```bash
ls -lah logs/
```

## 2) Install the provided config (recommended on Linux)

Copy `docs/logrotate/dripemails.conf` to `/etc/logrotate.d/dripemails-cron` and replace `PROJECT_ROOT` with your absolute project path.

Example install:

```bash
sudo cp docs/logrotate/dripemails.conf /etc/logrotate.d/dripemails-cron
sudo chmod 644 /etc/logrotate.d/dripemails-cron
sudo chown root:root /etc/logrotate.d/dripemails-cron
```

Core rule inside the config:

```conf
# Replace PROJECT_ROOT with your absolute project path (directory containing cron.py)
PROJECT_ROOT/logs/*.log {
    daily
    rotate 30
    missingok
    notifempty
    compress
    delaycompress
    copytruncate
    create 0640 www-data www-data
}
```

Notes:
- Replace `PROJECT_ROOT` with your real deployment path.
- The provided config also includes `PROJECT_ROOT/*.log` and `PROJECT_ROOT/*.jsonl` to cover top-level project logs.
- Adjust owner/group in `create` for your runtime user.

Test config safely:

```bash
sudo logrotate -d /etc/logrotate.d/dripemails-cron
```

Force one rotation run:

```bash
sudo logrotate -f /etc/logrotate.d/dripemails-cron
```

## 3) Comprehensive rotation script (manual fallback)

Create `scripts/rotate_cron_logs.sh` in the repo:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs"
ARCHIVE_DIR="${LOG_DIR}/archive"
TS="$(date +%Y%m%d-%H%M%S)"

mkdir -p "${ARCHIVE_DIR}"

shopt -s nullglob
for file in "${LOG_DIR}"/*.log; do
  base="$(basename "${file}")"
  gz_target="${ARCHIVE_DIR}/${base}.${TS}.gz"

  cp "${file}" "${ARCHIVE_DIR}/${base}.${TS}"
  : > "${file}"
  gzip -f "${ARCHIVE_DIR}/${base}.${TS}"

  echo "Rotated ${file} -> ${gz_target}"
done

# Keep only 30 days of archived logs
find "${ARCHIVE_DIR}" -type f -name "*.gz" -mtime +30 -delete
```

Make executable:

```bash
chmod +x scripts/rotate_cron_logs.sh
```

Run manually:

```bash
./scripts/rotate_cron_logs.sh
```

Optional cron entry (daily at 2:15 AM):

```cron
15 2 * * * /path/to/project/scripts/rotate_cron_logs.sh >> /path/to/project/logs/logrotate-script.log 2>&1
```

## 4) Operational checks

After rotation:

- `logs/*.log` still exists and is writable
- old files are in `logs/archive/*.gz`
- cron commands continue appending to command-specific files

## 5) Windows note

`logrotate` is Linux-native. On Windows, use Task Scheduler with a PowerShell equivalent script, or rotate logs in application code.

