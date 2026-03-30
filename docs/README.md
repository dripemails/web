# DripEmails.org — server documentation

This folder holds deployment scripts and guides. For **Postfix + Let’s Encrypt TLS**, use [`setup-postfix-tls-certbot.sh`](setup-postfix-tls-certbot.sh) and the section below.

**Related:** [SMTP production setup](smtp_server_production_setup.md) · [SMTP server setup](smtp_server_setup.md) · [SASL / port 587](sasl/setup_port_587.sh) · [Legacy Postfix SSL scripts](postfix_config/README_postfix_ssl.md)

---

## Postfix + Let’s Encrypt TLS (Certbot)

Use this on **Debian/Ubuntu** after Postfix is installed so SMTP uses a real certificate (not the default snakeoil) and **renewals reload Postfix** automatically.

Script: **`docs/setup-postfix-tls-certbot.sh`** (default `DOMAIN=dripemails.org`; override with `DOMAIN=...`).

### Before you start

1. **DNS** — Your **`DOMAIN`** (e.g. `dripemails.org` or `mail.dripemails.org`) **A/AAAA** records must point at this server.
2. **Run as root** — `sudo -i` or prefix commands with `sudo`.
3. **Certbot HTTP-01** needs **port 80** for the default challenge. Common pattern with **nginx**: stop nginx → run **standalone** → start nginx. Alternatively use **webroot** (nginx serves `/.well-known/acme-challenge/`) or **`obtain-nginx`**.

Adjust paths if the repo lives somewhere other than `/home/dripemails/web`.

### 1) Install packages

```bash
sudo apt-get update
sudo apt-get install -y postfix certbot
```

For **`obtain-nginx`**, also:

```bash
sudo apt-get install -y python3-certbot-nginx
```

During the Postfix installer, choose **Internet Site** (or your preferred option) and set the **system mail name** to your hostname (e.g. `dripemails.org`).

### 2) Start / enable Postfix

```bash
sudo systemctl enable postfix
sudo systemctl start postfix
sudo systemctl status postfix --no-pager
```

### 3) Get a certificate and point Postfix at it

From the **project** directory (example: clone at `/home/dripemails/web`):

```bash
cd /home/dripemails/web/docs
```

#### Recommended — Standalone (stop nginx briefly)

Certbot listens on **port 80**. Stop nginx, run the script, start nginx.

```bash
sudo systemctl stop nginx

sudo DOMAIN=dripemails.org CERTBOT_EMAIL=founders@dripemails.org bash setup-postfix-tls-certbot.sh obtain-standalone

sudo systemctl start nginx
sudo systemctl status nginx --no-pager
```

If something else uses port 80, stop that service instead during issuance. Check: `sudo ss -tlnp | grep ':80 '`.

The script will: request the cert, set **`smtpd_tls_cert_file`** / **`smtpd_tls_key_file`** to the **newest** matching directory under `/etc/letsencrypt/live/` (e.g. `dripemails.org` or `dripemails.org-0001` if Certbot created a second lineage), install **`/etc/letsencrypt/renewal-hooks/deploy/99-reload-postfix`**, and **reload Postfix**.

**Multiple names on one cert:** pass extra domains to Certbot, e.g.:

```bash
sudo DOMAIN=dripemails.org CERTBOT_EMAIL=you@dripemails.org \
  CERTBOT_EXTRA_ARGS='-d mail.dripemails.org' \
  bash setup-postfix-tls-certbot.sh obtain-standalone
```

(Use the same `CERTBOT_EXTRA_ARGS` consistently for renewals, or expand the Certbot renewal config.)

#### Right after Certbot succeeds

1. **Start nginx** (if you stopped it): `sudo systemctl start nginx`
2. **Duplicate lineage (`-0001`):** If Certbot saved files under `.../live/dripemails.org-0001/` but Postfix still pointed at `dripemails.org`, run:

   ```bash
   cd /home/dripemails/web/docs
   sudo DOMAIN=dripemails.org bash setup-postfix-tls-certbot.sh apply-postfix-only
   ```

3. **Confirm TLS files:**

   ```bash
   sudo postconf -n | grep -E '^smtpd_tls_(cert_file|key_file)='
   sudo openssl x509 -noout -subject -dates -in "$(postconf -h smtpd_tls_cert_file)"
   ```

#### Auto-renewal with standalone + nginx

`certbot renew` also needs port 80 free for standalone. After the first success, add hooks in the **correct** renewal file:

```bash
ls /etc/letsencrypt/renewal/
sudo nano /etc/letsencrypt/renewal/dripemails.org.conf
# or: dripemails.org-0001.conf — match the lineage under live/
```

Under `[renewalparams]`:

```ini
pre_hook = systemctl stop nginx
post_hook = systemctl start nginx
```

Test:

```bash
sudo certbot renew --dry-run
```

#### Option — Webroot (nginx stays up)

Requires nginx (or another server) on port 80 to serve `/.well-known/acme-challenge/`. Then:

```bash
cd /home/dripemails/web/docs
sudo DOMAIN=dripemails.org \
  CERTBOT_EMAIL=you@dripemails.org \
  WEBROOT=/var/www/html \
  bash setup-postfix-tls-certbot.sh obtain-webroot
```

#### Option — Nginx Certbot plugin

```bash
cd /home/dripemails/web/docs
sudo DOMAIN=dripemails.org CERTBOT_EMAIL=you@dripemails.org bash setup-postfix-tls-certbot.sh obtain-nginx
```

### 4) Certificate already exists (wire Postfix + hook only)

```bash
cd /home/dripemails/web/docs
sudo DOMAIN=dripemails.org bash setup-postfix-tls-certbot.sh apply-postfix-only
sudo DOMAIN=dripemails.org bash setup-postfix-tls-certbot.sh install-renewal-hook
```

### 5) Certbot timer

```bash
sudo systemctl enable --now certbot.timer
sudo systemctl status certbot.timer --no-pager
```

Dry-run (no real renewal):

```bash
cd /home/dripemails/web/docs
sudo bash setup-postfix-tls-certbot.sh dry-run-renew
```

### 6) Verification

```bash
sudo postconf -n | grep -E '^smtpd_tls_(cert_file|key_file|security_level)='
sudo ls -la /etc/letsencrypt/live/dripemails.org/ 2>/dev/null || sudo ls -la /etc/letsencrypt/live/
```

**STARTTLS on port 25 (SMTP):**

```bash
openssl s_client -connect dripemails.org:25 -starttls smtp -servername dripemails.org </dev/null 2>/dev/null | openssl x509 -noout -subject -dates
```

**Submission port 587** only works if **`submission`** is enabled in **`/etc/postfix/master.cf`** (not commented). See [docs/sasl/](sasl/) (e.g. `setup_port_587.sh`, `enable_port_587.sh`). Then:

```bash
openssl s_client -connect dripemails.org:587 -starttls smtp -servername dripemails.org -brief </dev/null
```

If you see **connection refused**, nothing is listening on 587 — uncomment the **`submission inet ... smtpd`** block in **`master.cf`** (use the public **`submission`** line, not **`127.0.0.1:submission`** only), then `sudo postfix check && sudo systemctl reload postfix`.

### 7) DNS and mail hostname

- **MX** must point to a **hostname** that resolves (A/AAAA) to your mail server. That hostname does not have to be `mail.*`; it must match what you use and what your **TLS certificate** covers.
- If clients use **`mail.dripemails.org`**, that name needs an **A** record (or CNAME chain to an A) **and** should be on the certificate (SAN) or clients will see hostname mismatches.

### 8) Django / app email over localhost

If the app sends via **127.0.0.1:25** and Postfix offers STARTTLS with a cert for **`dripemails.org`**, hostname verification against **`127.0.0.1`** can fail. Typical mitigations: relax TLS verify for that trusted local hop only in app settings, or connect using a hostname that matches the certificate. Align **`EMAIL_HOST`**, **`EMAIL_USE_TLS`**, and any “verify certificate” flags with your Postfix setup.

### Help

```bash
cd /home/dripemails/web/docs
sudo bash setup-postfix-tls-certbot.sh help
```

Always use **`bash setup-postfix-tls-certbot.sh …`** (not plain **`sh`**, unless you rely on the script’s automatic re-exec to bash).

---

## Other docs (index)

| Area | Location |
|------|----------|
| Deployment | [deployment_guide.md](deployment_guide.md) |
| Nginx | [nginx_dripemails.conf](nginx_dripemails.conf) |
| Supervisord | [supervisord_setup.md](supervisord_setup.md), [supervisord_quick_reference.md](supervisord_quick_reference.md) |
| Gmail OAuth | [gmail_oauth/](gmail_oauth/) |
| AI / Ollama | [ai/](ai/) |
| PostgreSQL | [sql/POSTGRES.md](sql/POSTGRES.md) |
