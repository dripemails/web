#!/bin/bash
#
# Configure Postfix on Debian/Ubuntu to use Let's Encrypt TLS certs from Certbot,
# and install a renewal deploy hook so Postfix reloads after auto-renewal.
#
# IMPORTANT: use bash, not sh (dash does not support this script's bash options):
#   sudo bash setup-postfix-tls-certbot.sh obtain-webroot
# If you run `sh setup-postfix-tls-certbot.sh`, we re-exec under /bin/bash automatically.
#
# Prerequisites:
#   - DNS A/AAAA for DOMAIN points to this server
#   - For --webroot: a web server must serve http://DOMAIN/.well-known/acme-challenge/
#   - For --standalone: nothing may listen on port 80 during issuance
#   - For --nginx: certbot's nginx plugin configures the host temporarily
#
# Usage (as root):
#   sudo bash docs/setup-postfix-tls-certbot.sh obtain-webroot
#   sudo bash docs/setup-postfix-tls-certbot.sh obtain-standalone
#   sudo bash docs/setup-postfix-tls-certbot.sh obtain-nginx
#   sudo bash docs/setup-postfix-tls-certbot.sh apply-postfix-only
#   sudo bash docs/setup-postfix-tls-certbot.sh install-renewal-hook
#   sudo bash docs/setup-postfix-tls-certbot.sh dry-run-renew
#

# When invoked as `sh this.sh`, dash runs us — re-exec with bash before any bash-only features.
if [ -z "${BASH_VERSION:-}" ]; then
  echo "[postfix-tls-setup] Re-exec under bash (you used sh/dash; use: bash $0 $*)" >&2
  exec /bin/bash "$0" "$@"
fi

set -euo pipefail

LOG_PREFIX="[postfix-tls-setup]"

log() {
  echo "$LOG_PREFIX $(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$@"
}

log_cmd() {
  log "RUN:" "$@"
  "$@"
}

DOMAIN="${DOMAIN:-dripemails.org}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-admin@${DOMAIN}}"
WEBROOT="${WEBROOT:-/var/www/html}"

LE_LIVE="/etc/letsencrypt/live/${DOMAIN}"
CERT_FILE="${LE_LIVE}/fullchain.pem"
KEY_FILE="${LE_LIVE}/privkey.pem"

# After certbot, the live dir may be DOMAIN, DOMAIN-0001, … — use the newest fullchain.pem.
refresh_le_paths() {
  local base="/etc/letsencrypt/live"
  local best="" best_t=0 d t
  shopt -s nullglob
  for d in "$base/${DOMAIN}" "$base/${DOMAIN}-"*; do
    [ -f "$d/fullchain.pem" ] && [ -f "$d/privkey.pem" ] || continue
    t=$(stat -c %Y "$d/fullchain.pem" 2>/dev/null || echo 0)
    if [ "${t:-0}" -gt "$best_t" ]; then
      best_t=$t
      best=$d
    fi
  done
  shopt -u nullglob
  if [ -n "$best" ]; then
    LE_LIVE="$best"
    CERT_FILE="${LE_LIVE}/fullchain.pem"
    KEY_FILE="${LE_LIVE}/privkey.pem"
    log "Let's Encrypt live dir (newest fullchain):" "$LE_LIVE"
  fi
}

DEPLOY_HOOK_DIR="/etc/letsencrypt/renewal-hooks/deploy"
DEPLOY_HOOK_NAME="99-reload-postfix"
DEPLOY_HOOK_PATH="${DEPLOY_HOOK_DIR}/${DEPLOY_HOOK_NAME}"

die() {
  log "ERROR:" "$@"
  exit 1
}

need_root() {
  uid="$(id -u)"
  log "check root: id -u => $uid"
  [ "$uid" -eq 0 ] || die "Run as root (sudo). Current uid=$uid"
}

have_cert() {
  [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]
}

cmd_obtain_webroot() {
  log "=== obtain-webroot start DOMAIN=$DOMAIN WEBROOT=$WEBROOT ==="
  need_root
  command -v certbot >/dev/null 2>&1 || die "Install certbot: apt-get install -y certbot"
  log "certbot found:" "$(command -v certbot)"
  [ -d "$WEBROOT" ] || die "WEBROOT does not exist: $WEBROOT (set WEBROOT=... or create directory)"
  log "WEBROOT ok:" "$WEBROOT"
  log "invoking certbot certonly (webroot)..."
  log_cmd certbot certonly \
    --non-interactive \
    --agree-tos \
    -m "$CERTBOT_EMAIL" \
    --webroot -w "$WEBROOT" \
    -d "$DOMAIN" \
    ${CERTBOT_EXTRA_ARGS:-}
  log "certbot certonly finished"
  apply_postfix_tls
  install_renewal_hook
  reload_postfix
  log "=== obtain-webroot DONE ==="
}

cmd_obtain_standalone() {
  log "=== obtain-standalone start DOMAIN=$DOMAIN ==="
  need_root
  command -v certbot >/dev/null 2>&1 || die "Install certbot: apt-get install -y certbot"
  log "certbot found:" "$(command -v certbot)"
  log "NOTE: standalone needs TCP port 80 free during issuance"
  log "invoking certbot certonly (standalone)..."
  log_cmd certbot certonly \
    --non-interactive \
    --agree-tos \
    -m "$CERTBOT_EMAIL" \
    --standalone \
    -d "$DOMAIN" \
    ${CERTBOT_EXTRA_ARGS:-}
  log "certbot certonly finished"
  apply_postfix_tls
  install_renewal_hook
  reload_postfix
  log "=== obtain-standalone DONE ==="
}

cmd_obtain_nginx() {
  log "=== obtain-nginx start DOMAIN=$DOMAIN ==="
  need_root
  command -v certbot >/dev/null 2>&1 || die "Install certbot: apt-get install -y certbot python3-certbot-nginx"
  log "certbot found:" "$(command -v certbot)"
  log "invoking certbot certonly (nginx plugin)..."
  log_cmd certbot certonly \
    --non-interactive \
    --agree-tos \
    -m "$CERTBOT_EMAIL" \
    --nginx \
    -d "$DOMAIN" \
    ${CERTBOT_EXTRA_ARGS:-}
  log "certbot certonly finished"
  apply_postfix_tls
  install_renewal_hook
  reload_postfix
  log "=== obtain-nginx DONE ==="
}

apply_postfix_tls() {
  log "=== apply_postfix_tls ==="
  need_root
  refresh_le_paths
  if have_cert; then
    log "cert files present:" "$CERT_FILE" "$KEY_FILE"
  else
    log "missing cert under $LE_LIVE"
    ls -la "$LE_LIVE" 2>&1 || log "(directory list failed)"
    die "Missing cert files — run an obtain-* command first."
  fi
  command -v postconf >/dev/null 2>&1 || die "postconf not found — is Postfix installed?"
  log "postconf:" "$(command -v postconf)"

  log "postconf -e smtpd_tls_cert_file=$CERT_FILE"
  postconf -e "smtpd_tls_cert_file=${CERT_FILE}"
  log "postconf -e smtpd_tls_key_file=$KEY_FILE"
  postconf -e "smtpd_tls_key_file=${KEY_FILE}"
  log "postconf -e smtpd_tls_security_level=may"
  postconf -e "smtpd_tls_security_level=may"

  log "verify postconf -n (TLS lines):"
  postconf -n | grep -E '^smtpd_tls_(cert_file|key_file|security_level)=' || true
  log "=== apply_postfix_tls DONE ==="
}

cmd_apply_postfix_only() {
  log "=== apply-postfix-only ==="
  apply_postfix_tls
  reload_postfix
  log "=== apply-postfix-only DONE ==="
}

install_renewal_hook() {
  log "=== install_renewal_hook path=$DEPLOY_HOOK_PATH ==="
  need_root
  log "mkdir -p $DEPLOY_HOOK_DIR"
  mkdir -p "$DEPLOY_HOOK_DIR"
  cat >"$DEPLOY_HOOK_PATH" <<'HOOK'
#!/usr/bin/env bash
# Deployed by DripEmails.org docs/setup-postfix-tls-certbot.sh — runs after each successful renewal.
set -e
echo "[postfix-tls-deploy-hook] $(date -u '+%Y-%m-%dT%H:%M:%SZ') reloading postfix after cert renew"
if command -v systemctl >/dev/null 2>&1; then
  systemctl reload postfix
elif command -v service >/dev/null 2>&1; then
  service postfix reload
else
  postfix reload
fi
HOOK
  chmod +x "$DEPLOY_HOOK_PATH"
  log "hook installed, mode:" "$(ls -l "$DEPLOY_HOOK_PATH")"
  log "=== install_renewal_hook DONE ==="
}

cmd_install_renewal_hook() {
  log "=== command install-renewal-hook ==="
  need_root
  install_renewal_hook
}

reload_postfix() {
  log "=== reload_postfix ==="
  if command -v systemctl >/dev/null 2>&1; then
    log "systemctl reload postfix"
    systemctl reload postfix
  elif command -v service >/dev/null 2>&1; then
    log "service postfix reload"
    service postfix reload
  else
    log "postfix reload"
    postfix reload
  fi
  log "postfix reload returned $?"
  log "=== reload_postfix DONE ==="
}

cmd_dry_run_renew() {
  log "=== dry-run-renew ==="
  need_root
  command -v certbot >/dev/null 2>&1 || die "certbot not installed"
  log_cmd certbot renew --dry-run
  log "Dry-run OK. Enable timer: systemctl enable --now certbot.timer"
  log "=== dry-run-renew DONE ==="
}

cmd_help() {
  cat <<EOF
$LOG_PREFIX Domain: $DOMAIN  (override: DOMAIN=other.com sudo -E bash ...)

Use BASH (not plain sh):
  sudo bash $0 obtain-webroot

Commands:
  obtain-webroot       certbot --webroot -w $WEBROOT
  obtain-standalone    certbot --standalone (needs free :80)
  obtain-nginx         certbot --nginx
  apply-postfix-only   point Postfix at newest /etc/letsencrypt/live/${DOMAIN}* (fullchain.pem mtime)
  install-renewal-hook deploy hook for postfix reload on renew
  dry-run-renew        certbot renew --dry-run

Auto-renewal:
  systemctl enable --now certbot.timer

Env: CERTBOT_EMAIL, WEBROOT, CERTBOT_EXTRA_ARGS
EOF
}

main() {
  log "script start argv=$* shell=$0 bash=$BASH_VERSION"
  log "DOMAIN=$DOMAIN CERTBOT_EMAIL=$CERTBOT_EMAIL LE_LIVE=$LE_LIVE"
  case "${1:-help}" in
    obtain-webroot)       cmd_obtain_webroot ;;
    obtain-standalone)    cmd_obtain_standalone ;;
    obtain-nginx)         cmd_obtain_nginx ;;
    apply-postfix-only)   cmd_apply_postfix_only ;;
    install-renewal-hook) cmd_install_renewal_hook ;;
    dry-run-renew)        cmd_dry_run_renew ;;
    help|-h|--help)       cmd_help ;;
    *)
      cmd_help
      die "Unknown command: ${1:-} — pass help for usage"
      ;;
  esac
  log "script exit ok"
}

main "$@"
