# Django makemessages Command Guide

This guide explains how to use Django's `makemessages` command to extract translatable strings and create translation files for internationalization (i18n).

## Overview

The `makemessages` command scans your Django project for translatable strings and creates `.po` (Portable Object) files that translators can edit. These files contain all the strings that need translation.

## Prerequisites

### Install gettext

The `makemessages` command requires the `gettext` utilities to be installed on your system.

#### Windows
1. Download gettext from: https://mlocati.github.io/articles/gettext-iconv-windows.html
2. Extract and add to your PATH, or
3. Install via Chocolatey: `choco install gettext`

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get install gettext
```

#### macOS
```bash
brew install gettext
```

#### Verify Installation
```bash
xgettext --version
```

## Basic Usage

### Create Translation Files for All Languages

To create `.po` files for all languages defined in your `LANGUAGES` setting:

```bash
python3 manage.py makemessages -a
```

This will create translation files in:
```
locale/
├── en/
│   └── LC_MESSAGES/
│       └── django.po
├── es/
│   └── LC_MESSAGES/
│       └── django.po
├── fr/
│   └── LC_MESSAGES/
│       └── django.po
└── ...
```

### Create Translation Files for Specific Languages

To create translation files for only specific languages:

```bash
# Single language
python3 manage.py makemessages -l es

# Multiple languages
python3 manage.py makemessages -l es -l fr -l de

# Or use --locale flag
python3 manage.py makemessages --locale=es --locale=fr
```

## Command Options

### Common Flags

- **`-a` or `--all`**: Process all languages from `LANGUAGES` setting
- **`-l <lang>` or `--locale <lang>`**: Process specific language(s)
- **`--no-obsolete`**: Remove obsolete entries (strings no longer in code)
- **`--no-wrap`**: Don't wrap long lines in the `.po` file
- **`--no-location`**: Don't write `#: filename:line` location comments
- **`--ignore <pattern>`**: Ignore files/directories matching pattern
- **`--extension <ext>`**: Process files with specific extension (default: `html,txt,py`)
- **`--domain <domain>`**: Domain of the message files (default: `django`)

### Ignoring Files/Directories

To exclude certain directories from scanning:

```bash
python3 manage.py makemessages -a --ignore=venv --ignore=node_modules --ignore=.git
```

Or create a `.gitignore`-style file and use:

```bash
python3 manage.py makemessages -a --ignore=venv
```

## Typical Workflow

### 1. Initial Setup

First time creating translation files:

```bash
# Create .po files for all languages
python3 manage.py makemessages -a
```

This creates empty `.po` files with all translatable strings marked as needing translation.

### 2. Edit Translation Files

Open the `.po` files in `locale/<lang>/LC_MESSAGES/django.po` and add translations:

```po
#: templates/base.html:15
#: templates/core/dashboard.html:42
msgid "Dashboard"
msgstr ""  # Add translation here, e.g., "Tablero" for Spanish
```

For strings with variables:

```po
#: templates/core/home.html:120
msgid "Welcome, {name}!"
msgstr "¡Bienvenido, {name}!"  # Keep {name} as-is
```

### 3. Compile Translations

After editing `.po` files, compile them to `.mo` (Machine Object) files:

```bash
python3 manage.py compilemessages
```

Django uses `.mo` files at runtime, so you must compile after every change.

### 4. Update Translations

When you add new translatable strings to your code:

```bash
# Update all .po files with new strings
python3 manage.py makemessages -a --no-obsolete

# Compile the updated translations
python3 manage.py compilemessages
```

The `--no-obsolete` flag removes strings that are no longer in your code.

## Working with Specific Languages

### Start with Priority Languages

If you have many languages configured, start with the most important ones:

```bash
# Create translations for top 5 languages
python3 manage.py makemessages -l en -l es -l fr -l de -l it
```

### Add More Languages Later

You can add more languages later:

```bash
# Add Portuguese translations
python3 manage.py makemessages -l pt

# Add Brazilian Portuguese
python3 manage.py makemessages -l pt_BR
```

## File Structure

After running `makemessages`, your `locale/` directory will look like:

```
locale/
├── en/
│   └── LC_MESSAGES/
│       ├── django.po      # Source file (edit this)
│       └── django.mo       # Compiled file (auto-generated)
├── es/
│   └── LC_MESSAGES/
│       ├── django.po
│       └── django.mo
└── ...
```

## Understanding .po Files

### File Header

Each `.po` file starts with metadata:

```po
# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER
# This file is distributed under the same license as the PACKAGE package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\n"
"Report-Msgid-Bugs-To: \n"
"POT-Creation-Date: 2024-01-01 12:00+0000\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"Language: es\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
```

### Translation Entries

Each translatable string has an entry:

```po
#: templates/base.html:15
msgid "Dashboard"
msgstr "Tablero"
```

- `#:` shows where the string appears in your code
- `msgid` is the original string (English)
- `msgstr` is the translation (leave empty if not translated)

### Plural Forms

For strings with pluralization:

```po
#: templates/core/dashboard.html:120
msgid "You have {count} email"
msgid_plural "You have {count} emails"
msgstr[0] "Tienes {count} correo"
msgstr[1] "Tienes {count} correos"
```

## Best Practices

### 1. Regular Updates

Update translation files regularly, especially after:
- Adding new features
- Changing user-facing text
- Updating templates

```bash
# Quick update workflow
python3 manage.py makemessages -a --no-obsolete
python3 manage.py compilemessages
```

### 2. Use Meaningful Context

Use context comments in your code:

```python
# In Python
from django.utils.translation import gettext as _

_("Dashboard")  # Translators: Main navigation item
```

```django
{# In templates #}
{% trans "Dashboard" %}  {# Translators: Main navigation item #}
```

### 3. Keep Translations in Sync

Always run `makemessages` before `compilemessages`:

```bash
# Correct order
python3 manage.py makemessages -a
python3 manage.py compilemessages

# Don't skip makemessages if you've changed code
```

### 4. Version Control

Commit both `.po` and `.mo` files to version control:
- `.po` files: Human-readable, editable
- `.mo` files: Compiled, used by Django

Or add to `.gitignore` if using a translation service:
```
locale/*/LC_MESSAGES/*.mo
```

## Troubleshooting

### Error: "xgettext not found"

**Solution**: Install gettext (see Prerequisites section)

### Error: "No translation files found"

**Solution**: Make sure `LOCALE_PATHS` is configured in `settings.py`:

```python
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]
```

### Translations Not Appearing

**Solution**: 
1. Make sure you've compiled: `python3 manage.py compilemessages`
2. Check that `LocaleMiddleware` is in `MIDDLEWARE`
3. Verify language is in `LANGUAGES` setting
4. Restart your development server

### Obsolete Strings Cluttering Files

**Solution**: Use `--no-obsolete` flag:

```bash
python3 manage.py makemessages -a --no-obsolete
```

## Advanced Usage

### Custom Domain

For JavaScript translations or custom domains:

```bash
python3 manage.py makemessages -d djangojs -l es
```

### Processing Specific Extensions

```bash
python3 manage.py makemessages -a --extension=html,js
```

### Excluding Specific Patterns

```bash
python3 manage.py makemessages -a --ignore=venv --ignore=node_modules
```

## Integration with Translation Services

Many projects use translation services like:
- **Transifex**: https://www.transifex.com/
- **Crowdin**: https://crowdin.com/
- **Weblate**: https://weblate.org/

These services can automatically sync with your `.po` files.

## Quick Reference

```bash
# Create all translation files
python3 manage.py makemessages -a

# Create for specific language
python3 manage.py makemessages -l es

# Update existing files (remove obsolete)
python3 manage.py makemessages -a --no-obsolete

# Compile translations
python3 manage.py compilemessages

# Full workflow
python3 manage.py makemessages -a --no-obsolete && python3 manage.py compilemessages
```

## Related Commands

- **`compilemessages`**: Compiles `.po` files to `.mo` files
- **`makemessages -d djangojs`**: Extract JavaScript translations
- **`gettext`**: The underlying tool that `makemessages` uses

## Additional Resources

- [Django i18n Documentation](https://docs.djangoproject.com/en/stable/topics/i18n/)
- [GNU gettext Manual](https://www.gnu.org/software/gettext/manual/)
- [Translation Best Practices](https://docs.djangoproject.com/en/stable/topics/i18n/translation/#internationalization-in-python-code)

