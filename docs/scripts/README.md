# Scripts

## add_agent_to_links.py

Adds `?agent={{ agent }}` (or `&agent={{ agent }}` when the URL already has query params) to internal links and optionally form actions in the `templates/` folder so that with `?agent=mobile`, navigation keeps the agent parameter.

**Coverage:**

- **All `href=`** on `<a>` tags: `href="..."`, `href='...'`, and `href = "..."` (optional spaces). Handles multiline attribute values.
- **Optional `action=`** on `<form>` when run with `--forms`.

**Run from project root (dripemails.org):**

```bash
# Preview changes only
python docs/scripts/add_agent_to_links.py --dry-run

# Apply changes (links only)
python docs/scripts/add_agent_to_links.py

# Also add agent to form action= attributes
python docs/scripts/add_agent_to_links.py --forms
```

**Options:**

- `--templates PATH` / `-t` — Use a different templates directory.
- `--dry-run` / `-n` — Print which files would be changed without writing.
- `--forms` / `-f` — Also add agent to `action=` attributes on forms.

**Skips:** links that already have `agent=`, `#`, `javascript:`, `mailto:`, `tel:`, `data:`, or `http(s)://` / `//` URLs. Idempotent: safe to run multiple times.

---

## remove_agent_from_links.py

Removes `{% if agent %}?agent={{ agent }}{% endif %}` and `{% if agent %}&agent={{ agent }}{% endif %}` from all templates (reverse of `add_agent_to_links.py`). Useful to revert the agent query param from links.

**Run from project root (dripemails.org):**

```bash
# Preview changes only
python docs/scripts/remove_agent_from_links.py --dry-run

# Apply changes
python docs/scripts/remove_agent_from_links.py
```

**Options:** same as `add_agent_to_links.py` (`--templates`, `--dry-run`). Idempotent: safe to run multiple times.
