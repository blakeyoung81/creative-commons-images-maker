#!/usr/bin/env python3
"""
Convert existing SVG files to JPG and add citations.
Uses cairosvg for conversion.
"""

import sys
from pathlib import Path
import cairosvg

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Pillow not available")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))
from download_cc_images import get_image_metadata, add_citation_overlay

def convert_svg_to_jpg(svg_path: Path, jpg_path: Path) -> bool:
    """Convert SVG to JPG using cairosvg."""
    try:
        # Convert SVG to PNG first
        png_path = jpg_path.with_suffix('.png')
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path))
        
        # Convert PNG to JPG
        img = Image.open(png_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(jpg_path, quality=95)
        png_path.unlink()  # Remove temporary PNG
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

def main():
    image_dir = Path("neurology_images")
    log_file = image_dir / "download_log.txt"
    
    svg_files = list(image_dir.glob("*.svg"))
    
    if not svg_files:
        print("No SVG files found.")
        return
    
    print(f"Found {len(svg_files)} SVG files to process\n")
    
    # Read log to get metadata
    log_content = ""
    if log_file.exists():
        with open(log_file, 'r') as f:
            log_content = f.read()
    
    success = 0
    failed = 0
    
    for svg_path in svg_files:
        print(f"Processing {svg_path.name}...")
        
        # Extract question number
        q_num = svg_path.stem.replace('question_', '').replace('.svg', '')
        
        # Try to find metadata from log
        metadata = None
        import re
        pattern = rf'Question {q_num}:.*?Downloading: (File:[^\n]+)'
        match = re.search(pattern, log_content, re.DOTALL)
        if match:
            wikimedia_filename = match.group(1)
            metadata = get_image_metadata(wikimedia_filename)
        
        # Convert to JPG
        jpg_path = svg_path.with_suffix('.jpg')
        if convert_svg_to_jpg(svg_path, jpg_path):
            print(f"  ✓ Converted to {jpg_path.name}")
            
            # Add citation
            if metadata:
                if add_citation_overlay(jpg_path, metadata):
                    print(f"  ✓ Added citation")
                else:
                    print(f"  ⚠ Citation overlay failed")
            else:
                print(f"  ⚠ No metadata found")
            
            svg_path.unlink()
            success += 1
        else:
            print(f"  ✗ Conversion failed")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Successfully converted: {success}")
    print(f"Failed: {failed}")

if __name__ == "__main__":
    main()

