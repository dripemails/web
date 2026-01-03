# i18n (Internationalization) Tools

This directory contains tools and documentation for adding internationalization support to Django templates.

## Documentation

- **[MAKEMESSAGES.md](MAKEMESSAGES.md)**: Complete guide to using Django's `makemessages` command to extract translatable strings and create translation files.

## translate.py

An automated translation script that uses Google Translate (free, no API key) to translate `.po` files.

### Features

- **Safe translation**: Automatically creates backups before modifying files
- **Preserves placeholders**: Keeps `{name}`, `%s`, `{{variable}}`, etc. intact
- **Handles plural forms**: Correctly translates plural message strings
- **Dry-run mode**: Preview translations without modifying files
- **Resume support**: Skip already-translated entries (never retranslates existing translations)
- **Multi-threading**: Parallel translation for faster processing
- **Rate limiting**: Respectful API usage with automatic delays
- **Progress tracking**: Shows detailed progress and statistics

### Installation

Install required dependencies:

```bash
pip install googletrans==4.0.0rc1 polib
```

### Usage

```bash
# Basic usage - translate all languages (single-threaded)
python docs/i18n/translate.py

# Use multiple threads for faster translation (recommended: 5-10 threads)
python docs/i18n/translate.py --threads 10

# Dry run (preview what would be translated)
python docs/i18n/translate.py --dry-run

# Dry run with threading
python docs/i18n/translate.py --dry-run --threads 10

# Translate specific languages
python docs/i18n/translate.py --languages es fr de

# Translate with threading
python docs/i18n/translate.py --threads 10 --languages es fr de

# Skip entries that already have translations (skips entire files if all translated)
python docs/i18n/translate.py --skip-translated

# Combine options
python docs/i18n/translate.py --threads 10 --languages es fr --skip-translated
```

### Threading Performance

The `--threads` option allows parallel translation for much faster processing:

- **Default (1 thread)**: Safe, sequential translation
- **5-10 threads**: Recommended for most use cases (5-10x faster)
- **10-20 threads**: For very large files (may hit API rate limits)

**Example performance:**
- Single-threaded: ~3000 entries in ~30 minutes
- 10 threads: ~3000 entries in ~3-5 minutes

**Note**: The script automatically preserves existing translations, so you can safely run it multiple times with different thread counts.

### Safety Features

- **Automatic backups**: Creates `.po.bak` files before modification
- **Placeholder preservation**: URLs, variables, and formatting are preserved
- **Error handling**: Continues on errors and reports them
- **Dry-run mode**: Test without making changes

### Important Notes

⚠️ **Always review translations!** Machine translation is not perfect:
- Review all translations before committing
- Check for context-specific terms
- Verify placeholders are preserved correctly
- Test the application after translation

The script uses Google Translate's free tier, which:
- Doesn't require an API key
- Has rate limits (handled automatically)
- May have usage restrictions for very large files

## makemessages.py

A convenience script that automatically creates locale files for all languages defined in `settings.py`.

### Features

- Automatically reads `LANGUAGES` from Django settings
- Creates locale directory structure if needed
- Runs `makemessages` for all configured languages
- Handles language code variants (e.g., `pt-br` → `pt_BR`)
- Provides helpful output and next steps

### Usage

```bash
# Create locale files for all languages in settings.py
python docs/i18n/makemessages.py

# Remove obsolete entries
python docs/i18n/makemessages.py --no-obsolete

# Show verbose output
python docs/i18n/makemessages.py --verbose

# List all languages without creating files
python docs/i18n/makemessages.py --list-languages
```

### Example Output

```
============================================================
Django makemessages - Batch Processing
============================================================

Processing 80+ language(s):
  - en         (English)
  - es         (Spanish)
  - fr         (French)
  ...

Running: python manage.py makemessages -l en -l es -l fr ...

✓ Successfully created/updated locale files!

Locale files are located in: C:\Users\...\locale

Created language directories:
  - en/LC_MESSAGES/django.po (45,234 bytes)
  - es/LC_MESSAGES/django.po (45,234 bytes)
  ...
```

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

