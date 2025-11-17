#!/usr/bin/env python3
"""
Script to convert existing SVG files to JPG and add citations.
Processes SVG files in neurology_images folder.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from download_cc_images import get_image_metadata, add_citation_overlay, convert_svg_to_jpg

def process_svg_files(image_dir: Path):
    """Convert all SVG files to JPG and add citations."""
    svg_files = list(image_dir.glob("*.svg"))
    
    if not svg_files:
        print("No SVG files found.")
        return
    
    print(f"Found {len(svg_files)} SVG files to process\n")
    
    success_count = 0
    fail_count = 0
    
    for svg_path in svg_files:
        print(f"Processing {svg_path.name}...")
        
        # Try to get metadata from log file
        log_file = image_dir / "download_log.txt"
        metadata = None
        
        if log_file.exists():
            # Try to extract filename from log
            with open(log_file, 'r') as f:
                content = f.read()
                # Look for the filename in the log
                import re
                pattern = rf'{svg_path.stem}.*?Downloading: (File:[^\n]+)'
                match = re.search(pattern, content)
                if match:
                    wikimedia_filename = match.group(1)
                    metadata = get_image_metadata(wikimedia_filename)
        
        # Convert SVG to JPG
        jpg_path = svg_path.with_suffix('.jpg')
        if convert_svg_to_jpg(svg_path, jpg_path):
            print(f"  ✓ Converted to {jpg_path.name}")
            
            # Add citation if metadata available
            if metadata:
                if add_citation_overlay(jpg_path, metadata):
                    print(f"  ✓ Added citation")
                    success_count += 1
                else:
                    print(f"  ⚠ Citation overlay failed")
                    success_count += 1  # Still count as success since conversion worked
            else:
                print(f"  ⚠ No metadata found, skipping citation")
                success_count += 1
            
            # Remove original SVG
            svg_path.unlink()
        else:
            print(f"  ✗ Conversion failed")
            fail_count += 1
    
    print(f"\n{'='*50}")
    print(f"Processing complete!")
    print(f"Successfully converted: {success_count}")
    print(f"Failed: {fail_count}")

if __name__ == "__main__":
    image_dir = Path("neurology_images")
    if not image_dir.exists():
        print(f"Error: Directory {image_dir} not found")
        sys.exit(1)
    
    process_svg_files(image_dir)

