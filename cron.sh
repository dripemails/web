#!/bin/bash
# Wrapper script to run cron.py in a loop for supervisord
# This script replicates the cron jobs:
# - SPF check: Daily at 2 AM
# - Scheduled emails: Every 5 minutes
#
# Based on cron jobs:
# 0 2 * * * cd /home/dripemails/web && /home/dripemails/dripemails/bin/python3 cron.py check_spf --settings=dripemails.live --all-users >> /var/log/dripemails.log 2>&1
# */5 * * * * cd /home/dripemails/web && /home/dripemails/dripemails/bin/python3 cron.py send_scheduled_emails --settings=dripemails.live >> /var/log/dripemails.log 2>&1

# Set paths
PROJECT_DIR="/home/dripemails/web"
PYTHON_BIN="/home/dripemails/dripemails/bin/python3"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Track last SPF check date to ensure it only runs once per day
LAST_SPF_CHECK_FILE="/tmp/dripemails_last_spf_check"
LAST_SPF_CHECK_DATE=""

# Load last check date if file exists
if [ -f "$LAST_SPF_CHECK_FILE" ]; then
    LAST_SPF_CHECK_DATE=$(cat "$LAST_SPF_CHECK_FILE")
fi

# Run send_scheduled_emails every 5 minutes
# Run check_spf --all-users daily at 2 AM
while true; do
    # Get current date and hour
    CURRENT_DATE=$(date +%Y-%m-%d)
    CURRENT_HOUR=$(date +%H)
    
    # Check if it's 2 AM and we haven't run SPF check today
    if [ "$CURRENT_HOUR" = "02" ] && [ "$LAST_SPF_CHECK_DATE" != "$CURRENT_DATE" ]; then
        # Run SPF check (only once per day at 2 AM)
        echo "$(date): Running SPF check for all users..."
        "$PYTHON_BIN" cron.py check_spf --settings=dripemails.live --all-users || true
        # Update last check date
        echo "$CURRENT_DATE" > "$LAST_SPF_CHECK_FILE"
        LAST_SPF_CHECK_DATE="$CURRENT_DATE"
        echo "$(date): SPF check completed."
    fi
    
    # Always run scheduled email processing (every 5 minutes)
    "$PYTHON_BIN" cron.py send_scheduled_emails --settings=dripemails.live || true
    
    # Sleep for 5 minutes (300 seconds)
    sleep 300
done

