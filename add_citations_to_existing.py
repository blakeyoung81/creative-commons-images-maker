#!/usr/bin/env python3
"""
Script to add Creative Commons citations to already downloaded images.
Reads the download log and adds citation overlays to all images.
"""

import re
from pathlib import Path
from download_cc_images import get_image_metadata, add_citation_overlay

def extract_filenames_from_log(log_file: Path):
    """Extract image filenames and their Wikimedia Commons file names from the log."""
    images = []
    
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match: Downloading: File:filename
    pattern = r'Question (\d+):.*?Downloading: (File:[^\n]+)\n.*?URL: ([^\n]+)'
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        q_num = int(match.group(1))
        filename = match.group(2).strip()
        url = match.group(3).strip()
        
        # Determine the local file path
        image_dir = log_file.parent
        # Try different extensions
        for ext in ['.jpg', '.png', '.svg', '.gif']:
            image_path = image_dir / f"question_{q_num:02d}{ext}"
            if image_path.exists():
                images.append({
                    'q_num': q_num,
                    'wikimedia_filename': filename,
                    'local_path': image_path,
                    'url': url
                })
                break
    
    return images

def main():
    """Add citations to all existing images."""
    image_dir = Path("downloaded_images")
    log_file = image_dir / "download_log.txt"
    
    if not log_file.exists():
        print(f"Error: Log file not found at {log_file}")
        return
    
    print("Extracting image information from log file...")
    images = extract_filenames_from_log(log_file)
    
    print(f"Found {len(images)} images to process\n")
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for img_info in images:
        q_num = img_info['q_num']
        wikimedia_filename = img_info['wikimedia_filename']
        local_path = img_info['local_path']
        
        print(f"[{q_num}/68] Processing {local_path.name}...")
        
        # Skip SVG files
        if local_path.suffix.lower() == '.svg':
            print(f"  Skipping SVG file\n")
            skip_count += 1
            continue
        
        # Get metadata
        metadata = get_image_metadata(wikimedia_filename)
        
        if metadata:
            if add_citation_overlay(local_path, metadata):
                print(f"  ✓ Added citation: \"{metadata['title']}\" by {metadata['author']} {metadata['license']}\n")
                success_count += 1
            else:
                print(f"  ✗ Failed to add citation overlay\n")
                fail_count += 1
        else:
            print(f"  ✗ Could not retrieve metadata\n")
            fail_count += 1
    
    print("=" * 50)
    print(f"Citation overlay complete!")
    print(f"Successfully added citations: {success_count}")
    print(f"Skipped (SVG): {skip_count}")
    print(f"Failed: {fail_count}")

if __name__ == "__main__":
    main()

