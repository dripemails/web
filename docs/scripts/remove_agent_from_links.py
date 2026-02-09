#!/usr/bin/env python3
"""
Remove {% if agent %}?agent={{ agent }}{% endif %} and
{% if agent %}&agent={{ agent }}{% endif %} from Django templates.

Also repairs broken {% static %} tags where the agent snippet was incorrectly
inserted (e.g. {% static"path" %} -> {% static "path" %}).

Run from the project root (dripemails.org) or with --templates pointing at
the templates directory. Modifies files in place. Safe to run multiple times
(idempotent).

Usage:
  cd dripemails.org
  python docs/scripts/remove_agent_from_links.py

  # or
  python docs/scripts/remove_agent_from_links.py --templates /path/to/templates
"""
import argparse
import os
import re
import sys


# Exact strings added by add_agent_to_links.py
AGENT_SUFFIX = '{% if agent %}?agent={{ agent }}{% endif %}'
AGENT_SUFFIX_WITH_AMP = '{% if agent %}&agent={{ agent }}{% endif %}'

# Optional: allow optional whitespace between { % and if (in case of reformatting)
AGENT_SUFFIX_RE = re.compile(
    r'\{%\s*if\s+agent\s*%\}\s*\?\s*agent=\{\{\s*agent\s*\}\}\s*\{%\s*endif\s*%\}',
    re.IGNORECASE
)
AGENT_SUFFIX_AMP_RE = re.compile(
    r'\{%\s*if\s+agent\s*%\}\s*&\s*agent=\{\{\s*agent\s*\}\}\s*\{%\s*endif\s*%\}',
    re.IGNORECASE
)


def process_file(filepath: str, dry_run: bool) -> bool:
    """Remove agent suffixes from one template file; return True if changed."""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    original = text
    # Remove exact strings first
    text = text.replace(AGENT_SUFFIX, '')
    text = text.replace(AGENT_SUFFIX_WITH_AMP, '')
    # Then any whitespace variants
    text = AGENT_SUFFIX_RE.sub('', text)
    text = AGENT_SUFFIX_AMP_RE.sub('', text)

    # Repair broken {% static %} tags: {% static"path" %} or {% static'path' %} -> valid
    text = text.replace('{% static"', '{% static "')
    text = text.replace("{% static'", "{% static '")

    changed = text != original
    if changed and not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
    return changed


def main():
    parser = argparse.ArgumentParser(
        description='Remove {% if agent %}?agent={{ agent }}{% endif %} from template links.'
    )
    parser.add_argument(
        '--templates', '-t', default=None,
        help='Path to templates directory (default: project templates/)'
    )
    parser.add_argument(
        '--dry-run', '-n', action='store_true',
        help='Only print what would be changed'
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.normpath(os.path.join(script_dir, '..', '..'))
    templates_dir = args.templates or os.path.join(project_root, 'templates')

    if not os.path.isdir(templates_dir):
        print(f'Error: templates directory not found: {templates_dir}', file=sys.stderr)
        sys.exit(1)

    count = 0
    for root, _dirs, files in os.walk(templates_dir):
        for name in files:
            if not name.endswith('.html'):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, templates_dir)
            if process_file(path, args.dry_run):
                count += 1
                print(f'Updated: {rel}')

    if args.dry_run and count:
        print(f'\nDry run: would update {count} file(s). Run without -n to apply.')
    elif count:
        print(f'Removed agent suffix from {count} file(s).')
    else:
        print('No files needed updates.')


if __name__ == '__main__':
    main()
