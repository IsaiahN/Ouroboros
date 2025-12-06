#!/usr/bin/env python3
"""
Remove Unicode emoji characters from Python files to fix Windows cp1252 encoding errors.
"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache
import re
from pathlib import Path

# Emoji to ASCII mapping
EMOJI_MAP = {
    '[OK]': '[OK]',
    '[FAIL]': '[FAIL]',
    '[VIRAL]': '[VIRAL]',
    '[PKG]': '[PKG]',
    '[STOP]': '[STOP]',
    '[WARN]': '[WARN]',
    '[WARN]': '[WARN]',
    '[SKIP]': '[SKIP]',
    '[TIME]': '[TIME]',
    '[TIME]': '[TIME]',
    '[TEST]': '[TEST]',
    '[IDEA]': '[IDEA]',
    '[LOCK]': '[LOCK]',
    '[SYNC]': '[SYNC]',
    '[NOTE]': '[NOTE]',
    '[STATS]': '[STATS]',
    '[END]': '[END]',
    '[TARGET]': '[TARGET]',
    '[HOT]': '[HOT]',
    '[DEAD]': '[DEAD]',
    '[LAUNCH]': '[LAUNCH]',
    '[WIN]': '[WIN]',
    '[NEW]': '[NEW]',
    '[STAR]': '[STAR]',
    '[STAR]': '[STAR]',
    '[STYLE]': '[STYLE]',
    '[BUG]': '[BUG]',
    '[FIX]': '[FIX]',
    '[GIFT]': '[GIFT]',
    '[GAME]': '[GAME]',
    '[TROPHY]': '[TROPHY]',
    '[GOLD]': '[GOLD]',
    '[SKULL]': '[SKULL]',
    '[SKULL]': '[SKULL]',
    '[SHIELD]': '[SHIELD]',
    '[SHIELD]': '[SHIELD]',
}

def remove_emojis_from_file(file_path):
    """Remove emojis from a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        for emoji, replacement in EMOJI_MAP.items():
            content = content.replace(emoji, replacement)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    root = Path('.')
    python_files = list(root.rglob('*.py'))
    
    modified_count = 0
    for py_file in python_files:
        if remove_emojis_from_file(py_file):
            print(f"Modified: {py_file}")
            modified_count += 1
    
    print(f"\nTotal files modified: {modified_count}/{len(python_files)}")

if __name__ == '__main__':
    main()
