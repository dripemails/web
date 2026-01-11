#!/usr/bin/env python3
"""
Script to automatically create locale files for all languages defined in settings.py

This script:
1. Reads LANGUAGES from Django settings
2. Creates the locale directory structure
3. Runs makemessages for each language

Usage:
    python docs/i18n/makemessages.py
    python docs/i18n/makemessages.py --no-obsolete
    python docs/i18n/makemessages.py --verbose
"""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to path so we can import Django settings
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dripemails.settings')

import django
django.setup()

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError


def get_language_codes():
    """Extract language codes from LANGUAGES setting."""
    languages = getattr(settings, 'LANGUAGES', [])
    if not languages:
        print("Warning: No languages found in LANGUAGES setting.")
        return []
    
    # Extract language codes, handling both simple codes and codes with variants
    language_codes = []
    for lang_code, lang_name in languages:
        # Handle language variants like 'pt-br' -> 'pt_BR' for makemessages
        # makemessages uses underscore, not hyphen
        normalized_code = lang_code.replace('-', '_')
        language_codes.append((lang_code, normalized_code))
    
    return language_codes


def ensure_locale_directory():
    """Ensure the locale directory exists."""
    locale_path = Path(settings.LOCALE_PATHS[0]) if settings.LOCALE_PATHS else PROJECT_ROOT / 'locale'
    locale_path.mkdir(exist_ok=True)
    return locale_path


def run_makemessages(language_codes, no_obsolete=False, verbose=False):
    """Run makemessages for each language."""
    locale_path = ensure_locale_directory()
    
    print(f"Locale directory: {locale_path}")
    print(f"Found {len(language_codes)} language(s) in settings.py\n")
    
    if not language_codes:
        print("No languages to process. Exiting.")
        return
    
    # Build command arguments
    # Note: We use individual -l flags instead of -a to have more control
    cmd_args = ['makemessages']
    
    if no_obsolete:
        cmd_args.append('--no-obsolete')
    
    if verbose:
        cmd_args.append('--verbosity=2')
    
    # Add language codes (makemessages requires -l for each language)
    for original_code, normalized_code in language_codes:
        cmd_args.extend(['-l', normalized_code])
    
    print(f"Running: python manage.py {' '.join(cmd_args)}\n")
    
    try:
        # Change to project root directory
        original_cwd = os.getcwd()
        os.chdir(PROJECT_ROOT)
        
        # Run the command
        call_command(*cmd_args)
        
        print("\n✓ Successfully created/updated locale files!")
        print(f"\nLocale files are located in: {locale_path}")
        
        # Show created directories
        if locale_path.exists():
            print("\nCreated language directories:")
            for lang_dir in sorted(locale_path.iterdir()):
                if lang_dir.is_dir():
                    po_file = lang_dir / 'LC_MESSAGES' / 'django.po'
                    if po_file.exists():
                        size = po_file.stat().st_size
                        print(f"  - {lang_dir.name}/LC_MESSAGES/django.po ({size:,} bytes)")
        
    except CommandError as e:
        print(f"\n✗ Error running makemessages: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        os.chdir(original_cwd)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Create locale files for all languages in settings.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python docs/i18n/makemessages.py
  python docs/i18n/makemessages.py --no-obsolete
  python docs/i18n/makemessages.py --verbose
  python docs/i18n/makemessages.py --no-obsolete --verbose
        """
    )
    
    parser.add_argument(
        '--no-obsolete',
        action='store_true',
        help='Remove obsolete entries (strings no longer in code)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show verbose output'
    )
    
    parser.add_argument(
        '--list-languages',
        action='store_true',
        help='List all languages from settings and exit'
    )
    
    args = parser.parse_args()
    
    # Get language codes
    language_codes = get_language_codes()
    
    if args.list_languages:
        print("Languages found in settings.py:")
        for original_code, normalized_code in language_codes:
            lang_name = dict(settings.LANGUAGES).get(original_code, 'Unknown')
            print(f"  {original_code:10} -> {normalized_code:10} ({lang_name})")
        return
    
    if not language_codes:
        print("No languages found in LANGUAGES setting.")
        print("Please check your settings.py file.")
        sys.exit(1)
    
    # Show what will be processed
    print("=" * 60)
    print("Django makemessages - Batch Processing")
    print("=" * 60)
    print(f"\nProcessing {len(language_codes)} language(s):")
    for original_code, normalized_code in language_codes:
        lang_name = dict(settings.LANGUAGES).get(original_code, 'Unknown')
        print(f"  - {normalized_code:10} ({lang_name})")
    print()
    
    # Run makemessages
    run_makemessages(language_codes, args.no_obsolete, args.verbose)
    
    print("\n" + "=" * 60)
    print("Next steps:")
    print("=" * 60)
    print("1. Edit the .po files in locale/<lang>/LC_MESSAGES/django.po")
    print("2. Add translations for each msgid")
    print("3. Compile translations: python manage.py compilemessages")
    print("=" * 60)


if __name__ == '__main__':
    main()

