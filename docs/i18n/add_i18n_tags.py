#!/usr/bin/env python3
"""
Safe script to add i18n tags to Django templates.
This script is conservative and only wraps obvious user-facing strings.

Usage:
    # Dry run (preview changes without modifying files)
    python docs/i18n/add_i18n_tags.py --dry-run
    
    # Apply changes (creates .bak backup files by default)
    python docs/i18n/add_i18n_tags.py
    
    # Apply changes without creating backup files
    python docs/i18n/add_i18n_tags.py --no-backup
    
    # Remove all existing .bak backup files
    python docs/i18n/add_i18n_tags.py --remove-backups
    
    # Verbose output
    python docs/i18n/add_i18n_tags.py --verbose
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple
import shutil
from datetime import datetime

# Get the project root directory (two levels up from this script)
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent.absolute()

# Directories to process (relative to project root)
TEMPLATE_DIRS = [
    'templates/core',
    'templates/campaigns',
    'templates/subscribers',
    'templates/blog',
    'templates/account',
    'templates/analytics',
    'templates/emails',
]

# Patterns to skip (don't translate these)
SKIP_PATTERNS = [
    r'\{%.*?%\}',  # Django template tags
    r'\{\{.*?\}\}',  # Django template variables
    r'https?://[^\s<>"]+',  # URLs
    r'[a-zA-Z_][a-zA-Z0-9_]*\s*\(',  # Function calls
    r'class=["\']',  # CSS classes
    r'id=["\']',  # IDs
    r'#[0-9a-fA-F]{3,6}',  # Hex colors
    r'^\s*[a-z-]+:\s*',  # CSS properties
    r'^\s*<!--.*?-->\s*$',  # HTML comments
    r'<[a-zA-Z][^>]*>',  # HTML tags
    r'{%\s*(load|extends|include|block|endblock|if|endif|for|endfor|trans|blocktrans)',  # Template tags
    r'\{[a-zA-Z_]+\}',  # Merge tags like {first_name}
]

# Strings that should definitely be translated
TRANSLATABLE_PATTERNS = [
    r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*',  # Title Case strings (but conservative)
]

# Minimum length for translation (too short might be code)
MIN_TRANSLATION_LENGTH = 3

# Strings that are commonly in templates and should be skipped
SKIP_STRINGS = {
    'href', 'src', 'alt', 'title', 'class', 'id', 'type', 'name', 'value',
    'method', 'action', 'enctype', 'placeholder', 'required', 'disabled',
    'checked', 'selected', 'readonly', 'hidden', 'target', '_blank',
    'px-4', 'py-2', 'bg-', 'text-', 'rounded', 'hover:', 'focus:',
    'Dashboard', 'Campaigns', 'Subscribers', 'Analytics', 'Settings',
    'email', 'password', 'username', 'first_name', 'last_name',
    'submit', 'button', 'form', 'input', 'div', 'span', 'a', 'p',
    'text-gray-', 'bg-gray-', 'text-indigo-', 'bg-indigo-',
}

def is_skip_string(text: str) -> bool:
    """Check if a string should be skipped."""
    text_clean = text.strip().lower()
    
    # Skip if too short
    if len(text_clean) < MIN_TRANSLATION_LENGTH:
        return True
    
    # Skip common HTML/CSS/JS terms
    if text_clean in SKIP_STRINGS:
        return True
    
    # Skip if matches any skip pattern
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, text):
            return True
    
    # Skip if it's all uppercase (likely code/constant)
    if text.isupper() and len(text) > 2:
        return True
    
    # Skip if it contains only symbols/numbers
    if not re.search(r'[a-zA-Z]', text):
        return True
    
    return False

def already_translated(text: str) -> bool:
    """Check if text is already wrapped in trans tags."""
    return '{% trans' in text or '{% blocktrans' in text or '{% translate' in text

def needs_i18n_load(content: str) -> bool:
    """Check if file needs {% load i18n %}."""
    return '{% load i18n %}' not in content and '{% load static i18n %}' not in content

def find_translatable_strings(content: str) -> List[Tuple[int, str, str]]:
    """
    Find strings that should be translated.
    Returns list of (line_number, original_text, context)
    """
    lines = content.split('\n')
    results = []
    
    for i, line in enumerate(lines, 1):
        # Skip lines that are mostly code
        if any(tag in line for tag in ['{%', '{{', '<script', '<style', 'function', 'var ', 'const ', 'let ']):
            continue
        
        # Find text in HTML tags (like <h1>Text</h1>, <p>Text</p>, <button>Text</button>)
        # But skip if it's already translated or is a skip string
        patterns = [
            # Text between HTML tags: <tag>Text</tag>
            (r'<[a-zA-Z][^>]*>([^<>{]+)</[a-zA-Z]>', 'html_tag_content'),
            # Text after > but before <
            (r'>([^<>{%]+)<', 'between_tags'),
            # Text in attributes like placeholder="Text", title="Text", alt="Text"
            (r'(?:placeholder|title|alt|aria-label)="([^"]+)"', 'attr'),
        ]
        
        for pattern, context_type in patterns:
            matches = re.finditer(pattern, line)
            for match in matches:
                text = match.group(1).strip()
                if text and not is_skip_string(text) and not already_translated(line):
                    # Only add if it's substantial text (not just symbols)
                    if len(text) >= MIN_TRANSLATION_LENGTH and re.search(r'[a-zA-Z]{3,}', text):
                        results.append((i, text, context_type))
    
    return results

def wrap_string_in_trans(text: str, original_line: str) -> str:
    """Wrap a string in {% trans %} tags, preserving formatting."""
    # Escape any existing quotes in the text for the trans tag
    # But preserve the original line structure
    
    # Find the exact position in the line
    if text in original_line:
        # Simple replacement
        return original_line.replace(text, f'{{% trans "{text}" %}}', 1)
    else:
        # Try to find a close match (handles whitespace variations)
        pattern = re.escape(text)
        replacement = f'{{% trans "{text}" %}}'
        return re.sub(pattern, replacement, original_line, count=1)

def process_template_file(file_path: Path, dry_run: bool = True, create_backup: bool = True) -> Tuple[bool, List[str]]:
    """
    Process a single template file.
    Returns (modified, changes_list)
    
    Args:
        file_path: Path to the template file
        dry_run: If True, don't modify files
        create_backup: If True, create .bak backup files
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, [f"Error reading file: {e}"]
    
    original_content = content
    changes = []
    lines = content.split('\n')
    
    # Step 1: Add {% load i18n %} if needed
    if needs_i18n_load(content):
        # Find the first {% load %} or {% extends %}
        for i, line in enumerate(lines):
            if '{% load' in line and 'i18n' not in line:
                # Add i18n to existing load tag
                lines[i] = line.replace('{% load', '{% load i18n', 1).replace('load i18n i18n', 'load i18n')
                changes.append(f"Line {i+1}: Added i18n to load tag")
                break
            elif '{% extends' in line and '{% load i18n %}' not in content:
                # Insert load i18n after extends
                lines.insert(i+1, '{% load i18n %}')
                changes.append(f"Line {i+1}: Added {{% load i18n %}}")
                break
    
    # Step 2: Find and wrap translatable strings (conservative approach)
    # Only wrap obvious user-facing text in specific contexts
    translatable = find_translatable_strings('\n'.join(lines))
    
    # Group by line number and process from bottom to top to preserve line numbers
    line_changes = {}
    for line_num, text, context in translatable:
        if line_num not in line_changes:
            line_changes[line_num] = []
        line_changes[line_num].append((text, context))
    
    # Apply changes from bottom to top
    for line_num in sorted(line_changes.keys(), reverse=True):
        line_idx = line_num - 1
        if line_idx < len(lines):
            original_line = lines[line_idx]
            modified_line = original_line
            
            # Only wrap the first substantial string per line (to be safe)
            for text, context in line_changes[line_num][:1]:  # Only first match per line
                if not already_translated(original_line):
                    # Only wrap if it's in a safe context (HTML content, not attributes)
                    if context in ['html_tag_content', 'between_tags']:
                        # Simple wrapping - wrap the text content
                        wrapped = wrap_string_in_trans(text, original_line)
                        if wrapped != original_line:
                            modified_line = wrapped
                            changes.append(f"Line {line_num}: Wrapped '{text[:50]}...' in {{% trans %}}")
            
            lines[line_idx] = modified_line
    
    new_content = '\n'.join(lines)
    
    if new_content != original_content:
        if not dry_run:
            # Create backup if requested
            if create_backup:
                backup_path = file_path.with_suffix(file_path.suffix + '.bak')
                shutil.copy2(file_path, backup_path)
                changes.insert(0, f"✓ Modified {file_path.name} (backup: {backup_path.name})")
            else:
                changes.insert(0, f"✓ Modified {file_path.name} (no backup)")
            
            # Write new content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        else:
            changes.insert(0, f"Would modify {file_path.name}")
        return True, changes
    
    return False, ["No changes needed"]

def remove_backup_files(project_root: Path, dry_run: bool = False) -> int:
    """
    Remove all .bak backup files in template directories.
    Returns the number of files removed.
    """
    backup_files = list(project_root.glob('**/*.bak'))
    removed_count = 0
    
    for backup_file in backup_files:
        # Only remove .bak files in template directories
        if 'templates' in str(backup_file):
            if not dry_run:
                try:
                    backup_file.unlink()
                    removed_count += 1
                except Exception as e:
                    print(f"Error removing {backup_file}: {e}")
            else:
                removed_count += 1
    
    return removed_count

def main():
    """Main function."""
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    create_backup = '--no-backup' not in sys.argv  # Default to True, unless --no-backup is specified
    remove_backups = '--remove-backups' in sys.argv
    
    # If only removing backups, do that and exit
    if remove_backups and '--dry-run' not in sys.argv and '-n' not in sys.argv:
        # Change to project root directory
        original_cwd = os.getcwd()
        os.chdir(PROJECT_ROOT)
        try:
            removed = remove_backup_files(PROJECT_ROOT, dry_run=False)
            print(f"✅ Removed {removed} backup file(s)")
        finally:
            os.chdir(original_cwd)
        return 0
    
    # Remove backups in dry-run mode if requested
    if remove_backups and dry_run:
        original_cwd = os.getcwd()
        os.chdir(PROJECT_ROOT)
        try:
            removed = remove_backup_files(PROJECT_ROOT, dry_run=True)
            print(f"Would remove {removed} backup file(s)")
        finally:
            os.chdir(original_cwd)
    
    if dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
        print("=" * 60)
    
    if not create_backup and not dry_run:
        print("⚠️  NO BACKUP MODE - Backup files will NOT be created")
        print("=" * 60)
    
    print("Adding i18n tags to Django templates...")
    print(f"Template directories: {', '.join(TEMPLATE_DIRS)}")
    print()
    
    all_changes = {}
    total_files = 0
    modified_files = 0
    
    # Change to project root directory
    original_cwd = os.getcwd()
    os.chdir(PROJECT_ROOT)
    
    try:
        for template_dir in TEMPLATE_DIRS:
            template_path = Path(template_dir)
            if not template_path.exists():
                if verbose:
                    print(f"⚠ Directory not found: {template_path.absolute()}")
                continue
            
            for html_file in template_path.rglob('*.html'):
                total_files += 1
                was_modified, changes = process_template_file(html_file, dry_run=dry_run, create_backup=create_backup)
                
                if was_modified or verbose:
                    all_changes[str(html_file)] = changes
                    if was_modified:
                        modified_files += 1
                
                if verbose and changes:
                    print(f"\n{html_file}:")
                    for change in changes:
                        print(f"  {change}")
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
    
    print()
    print("=" * 60)
    print(f"Summary:")
    print(f"  Total files scanned: {total_files}")
    print(f"  Files {'that would be' if dry_run else ''} modified: {modified_files}")
    
    if dry_run and modified_files > 0:
        print()
        print("To apply changes, run without --dry-run flag:")
        print("  python docs/i18n/add_i18n_tags.py")
        print()
        print("Options:")
        print("  --no-backup       Don't create .bak backup files")
        print("  --remove-backups  Remove existing .bak backup files")
        print("  --verbose         Show detailed changes for each file")
    elif not dry_run and modified_files > 0:
        print()
        if create_backup:
            print("✅ Changes applied! Backup files (.bak) were created.")
        else:
            print("✅ Changes applied! (No backup files created)")
        print("Please review the changes carefully before committing.")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

