#!/usr/bin/env python3
"""
Script to check and fix cover image paths in news_prod.csv
- Checks if cover files exist in media folder
- If jpg doesn't exist, checks for png version
- Updates CSV with correct paths
- Detects and fixes encoding issues (UTF-8 mojibake)
"""

import csv
import os
import re
from pathlib import Path
import chardet

def fix_encoding_issues(text):
    """
    Attempt to fix encoding issues (UTF-8 mojibake)
    
    Common pattern: UTF-8 bytes interpreted as Latin-1
    Example: "dellâ€™Innovazione" -> "dell'Innovazione"
    
    Args:
        text: String that may have encoding issues
        
    Returns:
        Fixed string if encoding issues detected, otherwise original
    """
    if not isinstance(text, str) or not text:
        return text
    
    # Check if text contains mojibake patterns (high-bit characters)
    if not any(ord(c) > 127 for c in text):
        return text  # No encoding issues
    
    try:
        # Try to fix by encoding as latin1 then decoding as utf-8
        # This reverses the common UTF-8 -> Latin-1 misinterpretation
        fixed = text.encode('latin1').decode('utf-8', errors='ignore')
        
        # Verify the fix made sense (reduced mojibake patterns)
        original_mojibake = sum(1 for c in text if ord(c) > 127)
        fixed_mojibake = sum(1 for c in fixed if ord(c) > 127)
        
        if fixed_mojibake < original_mojibake:
            return fixed
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    
    # If the above didn't work, try other common encoding fixes
    try:
        # Check if it's a specific UTF-8 mojibake pattern
        # â€™ is ' (apostrophe) in mojibake
        # â€" is – (en-dash)
        # â€œ is " (left quote)
        # â€ is " (right quote)
        
        mojibake_map = {
            'â€™': "'",      # apostrophe
            'â€œ': '"',      # left double quote
            'â€\x9d': '"',   # right double quote
            'â€"': '–',      # en-dash
            'â€"': '—',      # em-dash
            'â€¢': '•',      # bullet
            'â€¦': '…',      # ellipsis
        }
        
        result = text
        for mojibake, correct in mojibake_map.items():
            result = result.replace(mojibake, correct)
        
        if result != text:
            return result
    except Exception:
        pass
    
    return text


def check_and_fix_covers(csv_file, media_root='docker-site/media', fix_encoding=True):
    """
    Check cover paths in CSV and fix them if needed
    
    Args:
        csv_file: Path to the CSV file
        media_root: Path to the media directory
    """
    
    # Get absolute paths
    csv_path = Path(csv_file).resolve()
    media_path = Path(media_root).resolve()
    
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    if not media_path.exists():
        print(f"❌ Media directory not found: {media_path}")
        return
    
    print(f"📖 Reading CSV: {csv_path}")
    print(f"📁 Media directory: {media_path}\n")
    
    # Read CSV
    rows = []
    new_rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Process rows
    updated = 0
    not_found = 0
    already_ok = 0
    encoding_fixed = 0
    
    for i, row in enumerate(rows):
        # Fix encoding issues in title if enabled
        if fix_encoding and 'title' in row:
            original_title = row['title']
            fixed_title = fix_encoding_issues(original_title)
            if fixed_title != original_title:
                row['title'] = fixed_title
                encoding_fixed += 1
        
        cover = row.get('cover', '').strip()
        
        if cover:
            # Build full path
            full_path = media_path / cover.lstrip('/')
            
            if full_path.exists():
                print(f"✓ [{i+1}] {row['slug'][:40]:<40} → {cover}")
                already_ok += 1
            else:
                # Try PNG version if original is JPG
                if cover.lower().endswith(('.jpg', '.jpeg')):
                    png_cover = cover.rsplit('.', 1)[0] + '.png'
                    png_path = media_path / png_cover.lstrip('/')
                    
                    if png_path.exists():
                        print(f"🔄 [{i+1}] {row['slug'][:40]:<40}")
                        print(f"   ❌ Not found: {cover}")
                        print(f"   ✓ Found PNG: {png_cover}")
                        row['cover'] = png_cover
                        updated += 1
                    else:
                        print(f"✗ [{i+1}] {row['slug'][:40]:<40}")
                        print(f"   ❌ Not found: {cover}")
                        print(f"   ❌ No PNG found: {png_cover}")
                        row['cover'] = ''
                        not_found += 1
                else:
                    print(f"✗ [{i+1}] {row['slug'][:40]:<40} → {cover} (not found)")
                    row['cover'] = ''
                    not_found += 1
        
        new_rows.append(row)
    
    # Write back if there are any changes (cover updates, encoding fixes, or missing covers cleared)
    if updated > 0 or not_found > 0 or encoding_fixed > 0:
        print(f"\n💾 Writing updated CSV...")
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(new_rows)
        print(f"✓ CSV updated successfully")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"  ✓ Already OK: {already_ok}")
    print(f"  🔄 Updated to PNG: {updated}")
    print(f"  ✗ Not found: {not_found}")
    if fix_encoding:
        print(f"  🔧 Encoding fixed: {encoding_fixed}")
    print(f"  Total rows: {len(rows)}")

if __name__ == '__main__':
    check_and_fix_covers('news_prod.csv')
