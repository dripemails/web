#!/usr/bin/env python3
"""
Add ?agent={{ agent }} to all internal links (and form actions) in Django templates.

Run from the project root (dripemails.org) or with --templates pointing at
the templates directory. Modifies files in place. Idempotent (safe to run twice).

Usage:
  cd dripemails.org
  python docs/scripts/add_agent_to_links.py
  python docs/scripts/add_agent_to_links.py --templates /path/to/templates
  python docs/scripts/add_agent_to_links.py --dry-run
"""
import argparse
import os
import re
import sys


AGENT_SUFFIX = '{% if agent %}?agent={{ agent }}{% endif %}'
AGENT_SUFFIX_WITH_AMP = '{% if agent %}&agent={{ agent }}{% endif %}'


def should_skip_href(href: str) -> bool:
    """Skip external, anchor, and special links."""
    href = href.strip()
    if not href:
        return True
    # Already has agent param (idempotent)
    if 'agent={{ agent }}' in href or '?agent=' in href or '&agent=' in href:
        return True
    # Don't add agent inside {% static %} - would break tag syntax. {% url %} is fine: we append after it.
    if '{% static' in href:
        return True
    # Anchors and scripts
    if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
        return True
    if href.startswith('tel:') or href.startswith('data:'):
        return True
    # External URLs
    if href.startswith('http://') or href.startswith('https://') or href.startswith('//'):
        return True
    return False


def add_agent_to_href_content(content: str):
    """Append agent query to an href/action value; return new value or None if no change."""
    if should_skip_href(content):
        return None
    if AGENT_SUFFIX in content or AGENT_SUFFIX_WITH_AMP in content:
        return None
    stripped = content.rstrip()
    if '?' in stripped:
        return stripped + AGENT_SUFFIX_WITH_AMP
    return stripped + AGENT_SUFFIX


def _truncate(s: str, max_len: int = 72) -> str:
    s = s.replace('\n', ' ').strip()
    return (s[: max_len] + '...') if len(s) > max_len else s


def process_file(filepath: str, rel_path: str, dry_run: bool, include_forms: bool) -> bool:
    """Process one template file; return True if changed."""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # Match href="...", href='...', with optional whitespace around =
    # Also match action="..." for forms when include_forms is True
    # re.DOTALL so content can span lines (multiline attribute values)
    patterns = [
        (re.compile(r'href\s*=\s*(["\'])(.*?)\1', re.DOTALL), 'href'),
    ]
    if include_forms:
        patterns.append((re.compile(r'action\s*=\s*(["\'])(.*?)\1', re.DOTALL), 'action'))

    changed = False
    new_text = text

    for pattern, attr in patterns:
        for m in pattern.finditer(text):
            quote = m.group(1)
            content = m.group(2)
            new_content = add_agent_to_href_content(content)
            if new_content is not None:
                old_full = m.group(0)
                new_full = '{attr}={quote}{new_content}{quote}'.format(
                    attr=attr, quote=quote, new_content=new_content
                )
                if new_full != old_full and old_full in new_text:
                    new_text = new_text.replace(old_full, new_full, 1)
                    changed = True
                    print(f"  {rel_path}: {attr} {_truncate(content)}")
                    print(f"    → {_truncate(new_content)}")

    if changed and not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_text)
    return changed


def main():
    parser = argparse.ArgumentParser(
        description='Add ?agent={{ agent }} to template links (and optionally form actions).'
    )
    parser.add_argument(
        '--templates', '-t', default=None,
        help='Path to templates directory (default: project templates/)',
    )
    parser.add_argument(
        '--dry-run', '-n', action='store_true',
        help='Only print what would be changed',
    )
    parser.add_argument(
        '--forms', '-f', action='store_true',
        help='Also add agent to form action= attributes',
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
        for name in sorted(files):
            if not name.endswith('.html'):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, templates_dir)
            if process_file(path, rel, args.dry_run, args.forms):
                count += 1
                print(f'Updated: {rel}')

    if args.dry_run and count:
        print(f'\nDry run: would update {count} file(s). Run without -n to apply.')
    elif count:
        print(f'Updated {count} file(s).')
    else:
        print('No files needed updates.')


if __name__ == '__main__':
    main()
