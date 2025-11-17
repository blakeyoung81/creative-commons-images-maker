#!/usr/bin/env python3
"""
Script to add Creative Commons citations to already downloaded images.
Run this after download_cc_images.py to add citation overlays.
"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def add_citation_overlay(image_path: Path, citation_text: str) -> bool:
    """Add citation overlay to the bottom of an image."""
    try:
        # Skip SVG files
        if image_path.suffix.lower() == '.svg':
            print(f"  Skipping SVG file: {image_path.name}")
            return False
        
        # Open the image
        img = Image.open(image_path)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calculate font size
        draw = ImageDraw.Draw(img)
        font_size = max(16, min(img.width, img.height) // 40)
        
        # Try to load a nice font
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # Get text dimensions
        bbox = draw.textbbox((0, 0), citation_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Add padding
        padding = 20
        overlay_height = text_height + (padding * 2)
        
        # Create overlay
        overlay = Image.new('RGB', (img.width, img.height + overlay_height), (255, 255, 255))
        overlay.paste(img, (0, 0))
        
        # Draw citation
        draw_overlay = ImageDraw.Draw(overlay)
        text_x = (overlay.width - text_width) // 2
        text_y = img.height + padding
        
        draw_overlay.text((text_x, text_y), citation_text, fill=(0, 0, 0), font=font)
        
        # Save
        overlay.save(image_path, quality=95)
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

if __name__ == "__main__":
    print("This script requires metadata from the download log.")
    print("Please run the updated download_cc_images.py script instead.")
    print("It will automatically add citations during download.")

