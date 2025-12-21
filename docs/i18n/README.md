# i18n (Internationalization) Tools

This directory contains tools for adding internationalization support to Django templates.

## add_i18n_tags.py

A safe, conservative script to automatically add `{% load i18n %}` and `{% trans %}` tags to Django templates.

### Safety Features

- **Conservative approach**: Only wraps obvious user-facing strings
- **Dry-run mode**: Preview changes before applying them
- **Backup files**: Automatically creates `.bak` backups before modifying files
- **Skip patterns**: Automatically skips code, URLs, CSS classes, template variables, etc.
- **Already translated**: Skips strings that are already wrapped in trans tags

### Usage

#### Preview changes (recommended first step):
```bash
python docs/i18n/add_i18n_tags.py --dry-run
```

#### Apply changes (with backups):
```bash
python docs/i18n/add_i18n_tags.py
```

#### Apply changes (without backups):
```bash
python docs/i18n/add_i18n_tags.py --no-backup
```

#### Remove existing backup files:
```bash
python docs/i18n/add_i18n_tags.py --remove-backups
```

#### Verbose output (see all changes):
```bash
python docs/i18n/add_i18n_tags.py --verbose
```

### What it does

1. **Adds `{% load i18n %}`**: Adds to files that don't have it yet
2. **Wraps translatable strings**: Wraps user-facing text in `{% trans %}` tags
3. **Creates backups**: Creates `.bak` files before modifying (optional, use `--no-backup` to disable)

### What it skips

- Django template tags (`{% %}` and `{{ }}`)
- URLs and links
- CSS classes and IDs
- JavaScript code
- Function calls
- Merge tags like `{first_name}`
- Already translated strings
- Short strings (less than 3 characters)

### Manual Review Required

After running the script, you should:

1. Review all changes carefully
2. Test the templates to ensure they still work
3. Check that translations appear correctly
4. Consider using `{% blocktrans %}` for multi-line content or content with variables
5. Remove `.bak` backup files after confirming everything works:
   ```bash
   python docs/i18n/add_i18n_tags.py --remove-backups
   ```

### Notes

- The script is conservative by design - it may not catch all translatable strings
- Some strings may need manual wrapping in `{% blocktrans %}` for better translation handling
- Always test your templates after running the script
- The script processes templates in these directories:
  - `templates/core`
  - `templates/campaigns`
  - `templates/subscribers`
  - `templates/blog`
  - `templates/account`
  - `templates/analytics`
  - `templates/emails`

