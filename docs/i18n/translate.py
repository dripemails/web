#!/usr/bin/env python3
"""
Script to automatically translate .po files using online translation services.

This script:
1. Reads .po files from locale directories
2. Uses Google Translate (free, no API key required) to translate empty msgstr entries
3. Preserves placeholders, formatting, and special characters
4. Handles plural forms correctly
5. Provides safe, reversible translation with backup and dry-run modes

Usage:
    # Dry run (preview what would be translated)
    python docs/i18n/translate.py --dry-run

    # Translate all languages
    python docs/i18n/translate.py

    # Translate specific languages
    python docs/i18n/translate.py --languages es fr de

    # Skip languages that already have translations
    python docs/i18n/translate.py --skip-translated

    # Use a different translation service
    python docs/i18n/translate.py --service deepl --api-key YOUR_KEY
"""

import os
import sys
import re
import time
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
import argparse
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue

try:
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False
    print("Warning: googletrans not installed. Install with: pip install googletrans==4.0.0rc1")

try:
    import polib
    POLIB_AVAILABLE = True
except ImportError:
    POLIB_AVAILABLE = False
    print("Warning: polib not installed. Install with: pip install polib")


# Add project root to path
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dripemails.settings')

import django
django.setup()

from django.conf import settings


class POTranslator:
    """Handles translation of .po files."""
    
    def __init__(self, service='google', api_key=None, dry_run=False, num_threads=1):
        self.service = service
        self.api_key = api_key
        self.dry_run = dry_run
        self.num_threads = num_threads
        self.translator = None
        self.current_file = None
        self.current_file_path = None
        self.stats = {
            'translated': 0,
            'skipped': 0,
            'errors': 0,
            'languages': {}
        }
        self.lock = Lock()  # For thread-safe stats updates
        
        if service == 'google' and GOOGLETRANS_AVAILABLE:
            self.translator = Translator()
        elif service == 'google' and not GOOGLETRANS_AVAILABLE:
            raise ImportError("googletrans is required for Google Translate. Install with: pip install googletrans==4.0.0rc1")
        else:
            raise ValueError(f"Translation service '{service}' not yet supported. Use 'google'.")
    
    def preserve_placeholders(self, text: str):
        """Preserve placeholders like {name}, %s, {{variable}}, etc."""
        if not text:
            return text, {}
        
        # Store placeholders
        placeholder_map = {}
        counter = 0
        
        # Pattern for Django template variables: {{variable}}, {% tag %}, {variable}
        # Order matters - match more specific patterns first
        patterns = [
            (r'\{\{[^}]+\}\}', 'DJANGO_VAR'),  # {{variable}}
            (r'\{%[^%]+%\}', 'DJANGO_TAG'),    # {% tag %}
            (r'%\([^)]+\)[sd]', 'NAMED_FORMAT'),  # %(name)s
            (r'%[sd]', 'FORMAT_SPEC'),         # %s, %d
            (r'\{[^}]+\}', 'BRACE_VAR'),       # {variable}
        ]
        
        for pattern, prefix in patterns:
            def replacer(match):
                nonlocal counter
                placeholder = f"__PLACEHOLDER_{prefix}_{counter}__"
                placeholder_map[placeholder] = match.group(0)
                counter += 1
                return placeholder
            text = re.sub(pattern, replacer, text)
        
        return text, placeholder_map
    
    def restore_placeholders(self, text: str, placeholder_map: dict) -> str:
        """Restore placeholders after translation."""
        for placeholder, original in placeholder_map.items():
            text = text.replace(placeholder, original)
        return text
    
    def translate_text(self, text: str, target_lang: str, source_lang: str = 'en') -> Optional[str]:
        """Translate a single text string."""
        if not text or not text.strip():
            return text
        
        try:
            # Preserve placeholders
            text_with_placeholders, placeholder_map = self.preserve_placeholders(text)
            
            # Skip translation if text is empty after placeholder preservation
            if not text_with_placeholders or not text_with_placeholders.strip():
                return text
            
            # Translate
            if self.service == 'google':
                result = self.translator.translate(
                    text_with_placeholders,
                    src=source_lang,
                    dest=target_lang
                )
                
                # Handle result - it might be a string or an object
                if hasattr(result, 'text'):
                    translated = result.text
                elif isinstance(result, str):
                    translated = result
                else:
                    # Try to get text from result
                    translated = str(result)
                    
            else:
                raise ValueError(f"Unsupported service: {self.service}")
            
            # Restore placeholders
            if placeholder_map:
                translated = self.restore_placeholders(translated, placeholder_map)
            
            # Rate limiting - be nice to the API
            # With threading, we can reduce the delay since requests are distributed across threads
            if self.num_threads > 1:
                time.sleep(0.005)  # Very minimal delay with threading (5ms per thread)
            else:
                time.sleep(0.1)  # Original delay for single-threaded (100ms)
            
            return translated
            
        except (IndexError, AttributeError) as e:
            # Handle list/attribute errors more gracefully
            print(f"  ⚠ Index/Attribute error translating '{text[:50]}...': {e}")
            # Return original text if translation fails to avoid breaking the flow
            return text
        except Exception as e:
            print(f"  ⚠ Error translating '{text[:50]}...': {e}")
            import traceback
            if self.dry_run or hasattr(self, 'verbose'):
                traceback.print_exc()
            # Return original text instead of None to avoid breaking the flow
            return text
    
    def _translate_text_with_translator(self, translator, text: str, target_lang: str, source_lang: str = 'en') -> Optional[str]:
        """Internal method to translate using a specific translator instance (for threading)."""
        if not text or not text.strip():
            return text
        
        try:
            # Preserve placeholders
            text_with_placeholders, placeholder_map = self.preserve_placeholders(text)
            
            if not text_with_placeholders or not text_with_placeholders.strip():
                return text
            
            # Translate
            result = translator.translate(
                text_with_placeholders,
                src=source_lang,
                dest=target_lang
            )
            
            # Handle result - log if result is unexpected
            if result is None:
                return text
            
            if hasattr(result, 'text'):
                translated = result.text
            elif isinstance(result, str):
                translated = result
            else:
                # Unexpected result type - log it
                translated = str(result)
            
            # Restore placeholders
            if placeholder_map:
                translated = self.restore_placeholders(translated, placeholder_map)
            
            # Very minimal delay for threading - let the API handle rate limiting
            # With multiple threads, we can reduce delay significantly
            # Google Translate can handle concurrent requests, so minimal delay is fine
            if self.num_threads > 1:
                time.sleep(0.001)  # 1ms - very fast with threading (allows ~1000 req/sec across all threads)
            else:
                time.sleep(0.1)  # 100ms for single-threaded
            
            return translated
            
        except Exception as e:
            # Log the actual exception for debugging
            # Return original text on error to avoid breaking the flow
            return text
    
    def get_language_code(self, locale_code: str) -> str:
        """Convert Django locale code to Google Translate language code."""
        # Map Django locale codes to Google Translate codes
        # Some languages need special mapping or aren't supported
        lang_map = {
            'pt_br': 'pt',
            'zh_hans': 'zh-cn',
            'zh_hant': 'zh-tw',
            # Languages that Google Translate doesn't support well
            've': 'en',  # Venda - not well supported, fallback to English
            'xh': 'en',  # Xhosa - not well supported, fallback to English
            'yo': 'en',  # Yoruba - not well supported, fallback to English
            'zu': 'en',  # Zulu - not well supported, fallback to English
            'st': 'en',  # Sotho - not well supported, fallback to English
            'tn': 'en',  # Tswana - not well supported, fallback to English
            'sn': 'en',  # Shona - not well supported, fallback to English
            'nso': 'en',  # Northern Sotho - not well supported, fallback to English
            'nr': 'en',  # Ndebele - not well supported, fallback to English
            'ss': 'en',  # Swati - not well supported, fallback to English
            'ts': 'en',  # Tsonga - not well supported, fallback to English
        }
        
        # Handle variants
        locale_lower = locale_code.lower().replace('-', '_')
        if locale_lower in lang_map:
            mapped_code = lang_map[locale_lower]
            if mapped_code == 'en':
                print(f"  ⚠ Language {locale_code} not well supported by Google Translate, using English fallback")
            return mapped_code
        
        base_code = locale_code.split('_')[0].split('-')[0].lower()
        return base_code
    
    def _translate_entry(self, entry, target_lang_code, entry_index, total_entries):
        """Helper function to translate a single entry. Thread-safe."""
        results = {
            'translated': 0,
            'errors': 0,
            'entry': entry,
            'entry_index': entry_index
        }
        
        if self.dry_run:
            if entry.msgid and (not entry.msgstr or not entry.msgstr.strip()):
                with self.lock:
                    print(f"    [DRY RUN] Would translate: '{entry.msgid[:60]}...'")
            return results
        
        # Translate singular form
        if entry.msgid and (not entry.msgstr or not entry.msgstr.strip()):
            translated = self.translate_text(entry.msgid, target_lang_code)
            if translated and translated != entry.msgid:
                entry.msgstr = translated
                results['translated'] += 1
                with self.lock:
                    if results['translated'] <= 3:
                        print(f"    ✓ Translated: '{entry.msgid[:40]}...' -> '{translated[:40]}...'")
            else:
                results['errors'] += 1
        
        # Translate plural forms
        if entry.msgid_plural:
            for key, msgstr in entry.msgstr_plural.items():
                if not msgstr or not msgstr.strip():
                    translated = self.translate_text(entry.msgid_plural, target_lang_code)
                    if translated and translated != entry.msgid_plural:
                        entry.msgstr_plural[key] = translated
                        results['translated'] += 1
                    else:
                        results['errors'] += 1
        
        return results
    
    def translate_po_file(self, po_file_path: Path, target_lang: str, skip_translated: bool = False) -> bool:
        """Translate a single .po file."""
        if not POLIB_AVAILABLE:
            print("Error: polib is required. Install with: pip install polib")
            return False
        
        if not po_file_path.exists():
            print(f"  ⚠ File not found: {po_file_path}")
            return False
        
        # Store file info for progress messages
        self.current_file = po_file_path.name
        self.current_file_path = po_file_path.absolute()
        
        # Get language name from settings if available
        try:
            from django.conf import settings
            lang_name = dict(getattr(settings, 'LANGUAGES', [])).get(target_lang, target_lang)
        except:
            lang_name = target_lang
        
        print(f"\n📄 Processing file: {po_file_path.name}")
        print(f"   Language: {target_lang.upper()} ({lang_name})")
        print(f"   Full path: {po_file_path.absolute()}")
        
        try:
            po = polib.pofile(str(po_file_path))
        except Exception as e:
            print(f"  ✗ Error reading .po file: {e}")
            self.stats['errors'] += 1
            return False
        
        # Count entries with more detail
        total_entries = len(po)
        empty_entries = sum(1 for entry in po if not entry.translated() and not entry.fuzzy)
        translated_entries = sum(1 for entry in po if entry.translated())
        fuzzy_entries = sum(1 for entry in po if entry.fuzzy)
        
        print(f"  Total entries: {total_entries}")
        print(f"  Already translated (will be preserved): {translated_entries}")
        print(f"  Fuzzy (needs review, will be skipped): {fuzzy_entries}")
        print(f"  Need translation: {empty_entries}")
        
        if translated_entries > 0:
            print(f"  ✓ {translated_entries} existing translations will be preserved")
        
        # Show sample of untranslated entries
        if empty_entries > 0 and not self.dry_run:
            print(f"\n  📝 Sample of entries to translate ({empty_entries} total):")
            sample_count = 0
            for entry in po:
                if not entry.translated() and not entry.fuzzy and entry.msgid:
                    print(f"    - '{entry.msgid[:60]}...'")
                    sample_count += 1
                    if sample_count >= 3:
                        break
        
        if skip_translated and empty_entries == 0:
            print(f"  ⏭ Skipping (all entries already translated)")
            self.stats['skipped'] += 1
            return True
        
        if empty_entries == 0:
            print(f"  ✓ All entries already translated")
            return True
        
        # Get target language code for translation service
        target_lang_code = self.get_language_code(target_lang)
        is_fallback_to_english = target_lang_code == 'en' and target_lang.lower() != 'en'
        
        if is_fallback_to_english:
            print(f"\n  ⚠ Language {target_lang.upper()} not well supported - using English fallback")
            print(f"  ℹ️  Entries will be kept in English (better than no translation)")
        
        print(f"\n  🔄 Starting translation: {target_lang.upper()} -> {target_lang_code.upper()}")
        print(f"  📊 Will translate {empty_entries} entries using {self.num_threads} thread(s)...")
        
        # Store fallback flag for use in worker threads
        self._current_fallback_to_english = is_fallback_to_english
        
        # Collect entries that need translation
        entries_to_translate = []
        skipped_count = 0
        
        for i, entry in enumerate(po, 1):
            # Skip fuzzy entries
            if entry.fuzzy:
                skipped_count += 1
                continue
            
            # ALWAYS skip entries that are already translated
            if entry.translated():
                skipped_count += 1
                continue
            
            # Check if this entry needs translation
            needs_translation = False
            
            # Check singular form
            if entry.msgid and (not entry.msgstr or not entry.msgstr.strip()):
                needs_translation = True
            
            # Check plural forms
            if entry.msgid_plural:
                if any(not msgstr or not msgstr.strip() for msgstr in entry.msgstr_plural.values()):
                    needs_translation = True
            
            if needs_translation:
                entries_to_translate.append((i, entry))
        
        if not entries_to_translate:
            print(f"  ✓ No entries need translation")
            return True
        
        print(f"  📝 Translating {len(entries_to_translate)} entries using {self.num_threads} thread(s)...")
        
        # Translate entries (with or without threading)
        translated_count = 0
        error_count = 0
        processed_count = 0
        
        if self.num_threads > 1 and not self.dry_run:
            # Use queue-based threading: each thread pulls the next entry from a queue
            # This ensures even distribution and no idle threads
            from queue import Queue
            
            entry_queue = Queue()
            for entry_data in entries_to_translate:
                entry_queue.put(entry_data)
            
            # Add sentinel values to signal threads to stop
            for _ in range(self.num_threads):
                entry_queue.put(None)
            
            print(f"  🚀 Using {self.num_threads} threads with queue-based distribution for {target_lang.upper()}")
            
            def translate_worker(worker_id):
                """Worker thread that processes entries from the queue."""
                worker_translated = 0
                worker_errors = 0
                worker_processed = 0
                
                # Create a translator instance for this thread
                if self.service == 'google' and GOOGLETRANS_AVAILABLE:
                    thread_translator = Translator()
                else:
                    thread_translator = self.translator
                
                while True:
                    entry_data = entry_queue.get()
                    if entry_data is None:  # Sentinel - stop processing
                        entry_queue.task_done()
                        break
                    
                    entry_idx, entry = entry_data
                    
                    try:
                        # Translate singular form
                        if entry.msgid and (not entry.msgstr or not entry.msgstr.strip()):
                            try:
                                # Log first few translation attempts for debugging
                                if worker_processed < 3:
                                    with self.lock:
                                        print(f"  🔍 [{target_lang.upper()}] Thread {worker_id} translating: '{entry.msgid[:60]}...' -> {target_lang_code}")
                                
                                translated = self._translate_text_with_translator(
                                    thread_translator, entry.msgid, target_lang_code
                                )
                                
                                # Check if this is a fallback to English (use stored flag)
                                is_fallback_to_english = getattr(self, '_current_fallback_to_english', False)
                                
                                if translated and translated != entry.msgid:
                                    entry.msgstr = translated
                                    worker_translated += 1
                                    if worker_translated <= 3:
                                        with self.lock:
                                            print(f"  ✓ Thread {worker_id} success: '{entry.msgid[:40]}...' -> '{translated[:40]}...'")
                                elif is_fallback_to_english and translated == entry.msgid:
                                    # For fallback languages, accept English as valid translation
                                    entry.msgstr = translated
                                    worker_translated += 1
                                    # Only log first few to avoid spam
                                    if worker_translated <= 5:
                                        with self.lock:
                                            print(f"  ℹ️  [{target_lang.upper()}] Thread {worker_id} using English (fallback): '{entry.msgid[:60]}...'")
                                else:
                                    worker_errors += 1
                                    with self.lock:
                                        if translated == entry.msgid:
                                            print(f"  ⚠ [{target_lang.upper()}] Thread {worker_id} returned same text (no translation): '{entry.msgid[:60]}...'")
                                        elif not translated:
                                            print(f"  ⚠ [{target_lang.upper()}] Thread {worker_id} returned None/empty for: '{entry.msgid[:60]}...'")
                                        else:
                                            print(f"  ⚠ [{target_lang.upper()}] Thread {worker_id} translation failed (unknown reason) for: '{entry.msgid[:60]}...'")
                            except Exception as e:
                                # Continue on error, don't stop the thread
                                worker_errors += 1
                                with self.lock:
                                    # Always log errors with more detail
                                    error_msg = f"  ⚠ [{target_lang.upper()}] Thread {worker_id} translation exception for '{entry.msgid[:50]}...': {type(e).__name__}: {str(e)}"
                                    print(error_msg)
                                    # Print full traceback for first 3 errors per thread
                                    if worker_errors <= 3:
                                        import traceback
                                        print(f"  📋 [{target_lang.upper()}] Thread {worker_id} error #{worker_errors} traceback:")
                                        traceback.print_exc()
                        
                        # Translate plural forms
                        if entry.msgid_plural:
                            for key, msgstr in entry.msgstr_plural.items():
                                if not msgstr or not msgstr.strip():
                                    try:
                                        translated = self._translate_text_with_translator(
                                            thread_translator, entry.msgid_plural, target_lang_code
                                        )
                                        if translated and translated != entry.msgid_plural:
                                            entry.msgstr_plural[key] = translated
                                            worker_translated += 1
                                        else:
                                            worker_errors += 1
                                            with self.lock:
                                                print(f"  ⚠ [{target_lang.upper()}] Thread {worker_id} plural translation failed for: '{entry.msgid_plural[:60]}...'")
                                    except Exception as e:
                                        # Continue on error, don't stop the thread
                                        worker_errors += 1
                                        with self.lock:
                                            # Always log plural errors
                                            error_msg = f"  ⚠ [{target_lang.upper()}] Thread {worker_id} plural translation exception for '{entry.msgid_plural[:50]}...': {type(e).__name__}: {str(e)}"
                                            print(error_msg)
                                            # Print full traceback for first 3 errors per thread
                                            if worker_errors <= 3:
                                                import traceback
                                                print(f"  📋 [{target_lang.upper()}] Thread {worker_id} plural error #{worker_errors} traceback:")
                                                traceback.print_exc()
                        
                        worker_processed += 1
                        entry_queue.task_done()
                        
                        # Progress updates every 25 entries per thread
                        if worker_processed % 25 == 0:
                            with self.lock:
                                global_processed = processed_count + worker_processed
                                global_translated = translated_count + worker_translated
                                global_errors = error_count + worker_errors
                                lang_display = f"[{target_lang.upper()}]" if target_lang else ""
                                print(f"  {lang_display} Thread {worker_id}: {global_processed}/{len(entries_to_translate)} entries ({global_translated} translated, {global_errors} errors)...")
                                
                                # Save progress periodically
                                if global_processed % 100 == 0:
                                    try:
                                        po.save()
                                    except Exception as e:
                                        print(f"    ⚠ [{target_lang.upper()}] Error saving progress: {type(e).__name__}: {str(e)}")
                                        import traceback
                                        traceback.print_exc()
                    
                    except Exception as e:
                        worker_errors += 1
                        entry_queue.task_done()
                        with self.lock:
                            error_msg = f"  ⚠ [{target_lang.upper()}] Thread {worker_id} error on entry {entry_idx}: {type(e).__name__}: {str(e)}"
                            print(error_msg)
                            # Print traceback for entry processing errors
                            import traceback
                            print(f"  📋 [{target_lang.upper()}] Thread {worker_id} entry error traceback:")
                            traceback.print_exc()
                
                return worker_id, worker_translated, worker_errors, worker_processed
            
            # Start worker threads
            with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
                futures = [executor.submit(translate_worker, i+1) for i in range(self.num_threads)]
                
                # Collect results as threads complete
                for future in as_completed(futures):
                    try:
                        worker_id, worker_translated, worker_errors, worker_processed = future.result()
                        with self.lock:
                            translated_count += worker_translated
                            error_count += worker_errors
                            processed_count += worker_processed
                            if worker_errors > 0:
                                print(f"  ⚠ [{target_lang.upper()}] Thread {worker_id} completed: {worker_processed} entries, {worker_translated} translated, {worker_errors} ERRORS")
                            else:
                                print(f"  ✓ [{target_lang.upper()}] Thread {worker_id} completed: {worker_processed} entries, {worker_translated} translated, {worker_errors} errors")
                    except Exception as e:
                        with self.lock:
                            error_count += 1
                            print(f"  ⚠ [{target_lang.upper()}] Error in worker thread: {type(e).__name__}: {str(e)}")
                            import traceback
                            print(f"  📋 [{target_lang.upper()}] Worker thread error traceback:")
                            traceback.print_exc()
            
            # Final save
            try:
                po.save()
                if po_file_path.exists():
                    verify_po = polib.pofile(str(po_file_path))
                    verified_count = sum(1 for e in verify_po if e.translated())
                    print(f"    💾 Final save: {verified_count} entries now translated")
            except Exception as e:
                print(f"    ⚠ Error saving: {e}")
        else:
            # Single-threaded translation (original logic)
            for idx, entry in entries_to_translate:
                result = self._translate_entry(entry, target_lang_code, idx, len(entries_to_translate))
                translated_count += result['translated']
                error_count += result['errors']
                processed_count += 1
                
                # Progress updates
                if processed_count % 50 == 0:
                    lang_display = f"[{target_lang.upper()}]" if target_lang else ""
                    print(f"  {lang_display} Progress: {processed_count}/{len(entries_to_translate)} entries processed ({translated_count} translated, {error_count} errors)...")
                    if not self.dry_run:
                        try:
                            po.save()
                            if po_file_path.exists():
                                verify_po = polib.pofile(str(po_file_path))
                                verified_count = sum(1 for e in verify_po if e.translated())
                                print(f"    ✓ Saved! {verified_count} entries now translated")
                        except Exception as e:
                            print(f"    ⚠ [{target_lang.upper()}] Error saving progress: {type(e).__name__}: {str(e)}")
                            import traceback
                            traceback.print_exc()
        
        # Save the file
        if not self.dry_run:
            try:
                print(f"\n  💾 [{target_lang.upper()}] Saving translations to: {po_file_path}")
                print(f"     Absolute path: {po_file_path.absolute()}")
                po.save()
                print(f"  ✓ [{target_lang.upper()}] File saved successfully!")
                print(f"  ✓ [{target_lang.upper()}] Summary: {translated_count} entries translated, {error_count} errors, {skipped_count} skipped")
                
                # Print error summary if there were errors
                if error_count > 0:
                    print(f"\n  ⚠ [{target_lang.upper()}] ERROR SUMMARY: {error_count} errors occurred during translation")
                    print(f"     Check the error messages above for details.")
                
                # Verify the save by checking file size
                if po_file_path.exists():
                    file_size = po_file_path.stat().st_size
                    print(f"  ✓ File size: {file_size:,} bytes")
                    
                    # Quick verification - check a few entries
                    try:
                        verify_po = polib.pofile(str(po_file_path))
                        verified_translated = sum(1 for e in verify_po if e.translated())
                        print(f"  ✓ Verification: {verified_translated}/{len(verify_po)} entries are translated in saved file")
                    except Exception as e:
                        print(f"  ⚠ [{target_lang.upper()}] Could not verify saved file: {type(e).__name__}: {str(e)}")
                        import traceback
                        traceback.print_exc()
            except Exception as e:
                print(f"  ✗ [{target_lang.upper()}] Error saving file: {type(e).__name__}: {str(e)}")
                import traceback
                print(f"  📋 [{target_lang.upper()}] Save error traceback:")
                traceback.print_exc()
                self.stats['errors'] += error_count
                return False
        else:
            print(f"  [DRY RUN] Would translate: {translated_count} entries, {error_count} errors, {skipped_count} skipped")
        
        self.stats['translated'] += translated_count
        self.stats['errors'] += error_count
        self.stats['skipped'] += skipped_count
        self.stats['languages'][target_lang] = {
            'translated': translated_count,
            'errors': error_count,
            'skipped': skipped_count,
            'total': total_entries,
            'preserved': translated_entries
        }
        
        return True
    
    def translate_all(self, locale_path: Path, languages: Optional[List[str]] = None, 
                     skip_translated: bool = False) -> None:
        """Translate all .po files in locale directory."""
        if not locale_path.exists():
            print(f"Error: Locale directory not found: {locale_path}")
            return
        
        # Get list of languages to process
        if languages is None:
            # Get all languages from locale directory
            languages = [d.name for d in locale_path.iterdir() if d.is_dir()]
        else:
            # Normalize language codes (pt-br -> pt_br)
            languages = [lang.replace('-', '_') for lang in languages]
        
        print("=" * 70)
        print("PO File Translation Script")
        print("=" * 70)
        print(f"Service: {self.service}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print(f"Languages to process: {len(languages)}")
        print(f"Skip already translated: {skip_translated}")
        print("=" * 70)
        
        total_languages = len(languages)
        current_lang_index = 0
        
        for lang_code in sorted(languages):
            current_lang_index += 1
            po_file = locale_path / lang_code / 'LC_MESSAGES' / 'django.po'
            
            # Get language name from settings if available
            try:
                from django.conf import settings
                lang_name = dict(getattr(settings, 'LANGUAGES', [])).get(lang_code, lang_code)
            except:
                lang_name = lang_code
            
            # Big banner for new language
            print("\n" + "=" * 70)
            print(f"🌍 LANGUAGE {current_lang_index}/{total_languages}: {lang_code.upper()} ({lang_name})")
            print("=" * 70)
            print(f"📁 Locale directory: locale/{lang_code}/LC_MESSAGES/")
            
            if not po_file.exists():
                print(f"⚠ Skipping {lang_code}: django.po not found at {po_file}")
                continue
            
            # Create backup if not dry run
            if not self.dry_run:
                backup_file = po_file.with_suffix('.po.bak')
                if not backup_file.exists():
                    shutil.copy2(po_file, backup_file)
                    print(f"💾 Created backup: {backup_file.name}")
            
            self.translate_po_file(po_file, lang_code, skip_translated)
            
            # Separator after each language
            print(f"\n✅ Completed: {lang_code.upper()} ({lang_name})")
            print("=" * 70)
        
        # Print summary
        print("\n" + "=" * 70)
        print("Translation Summary")
        print("=" * 70)
        print(f"Total entries translated: {self.stats['translated']}")
        print(f"Total errors: {self.stats['errors']}")
        print(f"Languages processed: {len(self.stats['languages'])}")
        print("\nPer-language breakdown:")
        for lang, stats in sorted(self.stats['languages'].items()):
            preserved = stats.get('preserved', 0)
            skipped = stats.get('skipped', 0)
            print(f"  {lang:10} - New: {stats['translated']:4}, Preserved: {preserved:4}, Skipped: {skipped:4}, Errors: {stats['errors']:2}, Total: {stats['total']:4}")
        print("=" * 70)
        
        if self.dry_run:
            print("\n⚠ DRY RUN MODE - No files were modified")
            print("Run without --dry-run to apply translations")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Automatically translate .po files using online translation services',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (preview)
  python docs/i18n/translate.py --dry-run

  # Translate all languages
  python docs/i18n/translate.py

  # Translate specific languages
  python docs/i18n/translate.py --languages es fr de

  # Skip languages that already have translations
  python docs/i18n/translate.py --skip-translated

Notes:
  - Backups are automatically created (.po.bak files)
  - Placeholders like {name}, %s, {{variable}} are preserved
  - Rate limiting is applied to be respectful to the API
  - Always review translations before committing
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview translations without modifying files'
    )
    
    parser.add_argument(
        '--languages',
        nargs='+',
        help='Specific languages to translate (e.g., es fr de)'
    )
    
    parser.add_argument(
        '--skip-translated',
        action='store_true',
        help='Skip entries that already have translations'
    )
    
    parser.add_argument(
        '--service',
        default='google',
        choices=['google'],
        help='Translation service to use (default: google)'
    )
    
    parser.add_argument(
        '--api-key',
        help='API key for translation service (not needed for Google Translate)'
    )

    parser.add_argument(
        '--threads',
        type=int,
        default=1,
        help='Number of threads to use for parallel translation (default: 1, recommended: 5-10)'
    )

    parser.add_argument(
        '--locale-path',
        type=Path,
        help='Path to locale directory (default: auto-detect from settings)'
    )
    
    args = parser.parse_args()
    
    # Check dependencies
    if not GOOGLETRANS_AVAILABLE and args.service == 'google':
        print("Error: googletrans is required for Google Translate")
        print("Install with: pip install googletrans==4.0.0rc1")
        sys.exit(1)
    
    if not POLIB_AVAILABLE:
        print("Error: polib is required")
        print("Install with: pip install polib")
        sys.exit(1)
    
    # Get locale path
    if args.locale_path:
        locale_path = args.locale_path
    else:
        locale_paths = getattr(settings, 'LOCALE_PATHS', [])
        if locale_paths:
            locale_path = Path(locale_paths[0])
        else:
            locale_path = PROJECT_ROOT / 'locale'
    
    # Create translator and run
    try:
        translator = POTranslator(
            service=args.service,
            api_key=args.api_key,
            dry_run=args.dry_run,
            num_threads=args.threads
        )
        
        translator.translate_all(
            locale_path=locale_path,
            languages=args.languages,
            skip_translated=args.skip_translated
        )
        
    except KeyboardInterrupt:
        print("\n\n⚠ Translation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

