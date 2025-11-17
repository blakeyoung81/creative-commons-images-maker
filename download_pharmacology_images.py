#!/usr/bin/env python3
"""
Script to download Creative Commons licensed images for pharmacology medical education questions.
Uses Wikimedia Commons API to find and download CC-licensed images with citation overlays.
Downloads 2 image options per question using provided search queries.
"""

import re
import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import time

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: Pillow not installed. Citation overlays will be skipped.")
    print("Install with: pip3 install --break-system-packages Pillow")

# Import functions from the main script
import sys
sys.path.insert(0, str(Path(__file__).parent))
from download_cc_images import (
    search_wikimedia_commons,
    get_image_url,
    get_image_metadata,
    download_image,
    add_citation_overlay,
    extract_topic
)

# Pharmacology questions with their search queries
PHARMACOLOGY_QUESTIONS = [
    {
        'number': 1,
        'topic': 'Cirrhosis & Protein Binding',
        'queries': [
            'effect of hypoalbuminemia on volume of distribution',
            'pharmacokinetics of highly protein bound drugs in liver disease'
        ]
    },
    {
        'number': 2,
        'topic': 'Heart Failure & Drug Distribution',
        'queries': [
            'how edema affects volume of distribution for hydrophilic drugs',
            'pharmacokinetics in heart failure fluid overload'
        ]
    },
    {
        'number': 3,
        'topic': 'Sudden Drug Toxicity & Kinetics',
        'queries': [
            'zero-order vs first-order elimination kinetics',
            'drugs with zero-order kinetics examples'
        ]
    },
    {
        'number': 4,
        'topic': 'Aspirin Overdose Kinetics',
        'queries': [
            'aspirin overdose shifts from first-order to zero-order kinetics',
            'salicylate metabolism saturation'
        ]
    },
    {
        'number': 5,
        'topic': 'Cyanide Poisoning Mechanism',
        'queries': [
            'cyanide poisoning mechanism cytochrome oxidase',
            'noncompetitive vs competitive inhibition Vmax Km'
        ]
    },
    {
        'number': 6,
        'topic': 'Antifreeze & Ethanol Treatment',
        'queries': [
            'ethanol for ethylene glycol poisoning mechanism',
            'competitive inhibition alcohol dehydrogenase fomepizole'
        ]
    },
    {
        'number': 7,
        'topic': 'Buprenorphine & Withdrawal',
        'queries': [
            'buprenorphine precipitated withdrawal mechanism',
            'buprenorphine high affinity partial agonist'
        ]
    },
    {
        'number': 8,
        'topic': 'Potency vs. Efficacy',
        'queries': [
            'pharmacology potency vs efficacy graph',
            'EC50 and Emax definition pharmacology'
        ]
    },
    {
        'number': 9,
        'topic': 'Aspirin Overdose & Bicarbonate',
        'queries': [
            'sodium bicarbonate for aspirin overdose mechanism',
            'ion trapping weak acid excretion'
        ]
    },
    {
        'number': 10,
        'topic': 'Amphetamine Overdose & Urine pH',
        'queries': [
            'acidification of urine for amphetamine overdose',
            'ion trapping weak base excretion'
        ]
    },
    {
        'number': 11,
        'topic': 'pKa and Drug Ionization',
        'queries': [
            'henderson hasselbalch equation for weak base',
            'drug absorption pKa vs pH'
        ]
    },
    {
        'number': 12,
        'topic': 'Malignant Hyperthermia',
        'queries': [
            'malignant hyperthermia triggers and mechanism',
            'dantrolene mechanism of action malignant hyperthermia'
        ]
    },
    {
        'number': 13,
        'topic': 'Inhaled Anesthetics & Solubility',
        'queries': [
            'inhaled anesthetic blood gas partition coefficient explained',
            'desflurane fast onset low solubility'
        ]
    },
    {
        'number': 14,
        'topic': 'Cirrhosis & Warfarin',
        'queries': [
            'warfarin metabolism in liver cirrhosis',
            'effect of hepatic dysfunction on CYP450 metabolism'
        ]
    },
    {
        'number': 15,
        'topic': 'Vancomycin & Obesity',
        'queries': [
            'vancomycin loading dose in obesity',
            'loading dose vs maintenance dose Vd clearance'
        ]
    },
    {
        'number': 16,
        'topic': 'Digoxin & Kidney Disease',
        'queries': [
            'digoxin toxicity in chronic kidney disease',
            'digoxin renal clearance and pharmacokinetics'
        ]
    },
    {
        'number': 17,
        'topic': 'Warfarin & Rifampin',
        'queries': [
            'rifampin warfarin interaction mechanism',
            'rifampin as a CYP450 inducer'
        ]
    },
    {
        'number': 18,
        'topic': 'Elderly & Diazepam',
        'queries': [
            'Phase 1 vs Phase 2 metabolism in elderly',
            'why avoid diazepam in elderly LOT benzodiazepines'
        ]
    },
    {
        'number': 19,
        'topic': 'Warfarin & Ciprofloxacin',
        'queries': [
            'ciprofloxacin warfarin interaction CYP',
            'common CYP450 inhibitors'
        ]
    },
    {
        'number': 20,
        'topic': 'Theophylline & Ciprofloxacin',
        'queries': [
            'theophylline ciprofloxacin interaction mechanism',
            'theophylline narrow therapeutic index CYP1A2'
        ]
    },
    {
        'number': 21,
        'topic': 'Isoniazid & Lupus',
        'queries': [
            'slow acetylators isoniazid drug induced lupus',
            'N-acetyltransferase polymorphism isoniazid'
        ]
    },
    {
        'number': 22,
        'topic': 'Sweating Neurotransmitter',
        'queries': [
            'neurotransmitter for sweat glands sympathetic cholinergic',
            'anticholinergic drugs for hyperhidrosis'
        ]
    },
    {
        'number': 23,
        'topic': 'Tamsulosin & Dizziness',
        'queries': [
            'tamsulosin orthostatic hypotension mechanism',
            'alpha-1 blocker first dose effect'
        ]
    },
    {
        'number': 24,
        'topic': 'Asthma Rescue Inhaler',
        'queries': [
            'albuterol mechanism of action asthma',
            'beta 2 receptor function lungs'
        ]
    },
    {
        'number': 25,
        'topic': 'Anaphylaxis Treatment',
        'queries': [
            'epinephrine for anaphylaxis IM vs subcutaneous',
            'alpha-1 and beta-2 effects of epinephrine in anaphylaxis'
        ]
    },
    {
        'number': 26,
        'topic': 'Post-op Urinary Retention',
        'queries': [
            'bethanechol mechanism for urinary retention',
            'muscarinic agonists vs antagonists bladder'
        ]
    },
    {
        'number': 27,
        'topic': 'Organophosphate Poisoning',
        'queries': [
            'atropine for organophosphate poisoning mechanism',
            'atropine vs pralidoxime for organophosphate poisoning'
        ]
    },
    {
        'number': 28,
        'topic': 'Fenoldopam Mechanism',
        'queries': [
            'fenoldopam mechanism of action hypertensive emergency',
            'D1 receptor agonists effects renal blood flow'
        ]
    },
    {
        'number': 29,
        'topic': 'Famotidine Mechanism',
        'queries': [
            'famotidine H2 blocker mechanism of action',
            'H2 blockers vs proton pump inhibitors mechanism'
        ]
    },
    {
        'number': 30,
        'topic': 'Donepezil Mechanism',
        'queries': [
            'donepezil mechanism of action Alzheimer\'s',
            'acetylcholinesterase inhibitors side effects'
        ]
    },
    {
        'number': 31,
        'topic': 'Dobutamine in Heart Failure',
        'queries': [
            'dobutamine mechanism of action heart failure',
            'beta 1 agonist effects contractility'
        ]
    },
    {
        'number': 32,
        'topic': 'Metoclopramide Mechanism',
        'queries': [
            'metoclopramide mechanism of action gastroparesis',
            'metoclopramide D2 antagonist extrapyramidal side effects'
        ]
    },
    {
        'number': 33,
        'topic': 'Methylphenidate Mechanism',
        'queries': [
            'methylphenidate mechanism of action ADHD',
            'DAT and NET reuptake inhibitors'
        ]
    },
    {
        'number': 34,
        'topic': 'MAOI & Cocaine Interaction',
        'queries': [
            'MAOI and cocaine interaction hypertensive crisis',
            'cocaine vs MAOI effect on norepinephrine'
        ]
    },
    {
        'number': 35,
        'topic': 'Septic Shock Vasopressor',
        'queries': [
            'norepinephrine for septic shock mechanism',
            'first line vasopressor septic shock'
        ]
    },
    {
        'number': 36,
        'topic': 'Botulinum Toxin Mechanism',
        'queries': [
            'botulinum toxin mechanism of action neuromuscular junction',
            'SNARE proteins and acetylcholine release'
        ]
    },
    {
        'number': 37,
        'topic': 'Pheochromocytoma Pre-op',
        'queries': [
            'pheochromocytoma preoperative management alpha blockade',
            'why alpha blockade before beta blockade pheochromocytoma'
        ]
    },
    {
        'number': 38,
        'topic': 'Digoxin in Elderly',
        'queries': [
            'digoxin volume of distribution in elderly',
            'age related changes in drug distribution'
        ]
    },
    {
        'number': 39,
        'topic': 'NSAID & GI Bleed',
        'queries': [
            'NSAID mechanism of GI bleed',
            'prostaglandins gastric protection COX-1'
        ]
    },
    {
        'number': 40,
        'topic': 'Diphenhydramine in Elderly',
        'queries': [
            'diphenhydramine anticholinergic effects elderly',
            'Beers criteria anticholinergic drugs'
        ]
    },
    {
        'number': 41,
        'topic': 'Cirrhosis & Free Drug',
        'queries': [
            'effect of hypoalbuminemia on highly protein bound drugs',
            'free drug concentration vs bound drug in liver disease'
        ]
    },
    {
        'number': 42,
        'topic': 'Diazepam in Elderly',
        'queries': [
            'diazepam active metabolites and aging',
            'Phase 1 metabolism decline in elderly'
        ]
    },
    {
        'number': 43,
        'topic': 'Amitriptyline & Orthostasis',
        'queries': [
            'amitriptyline orthostatic hypotension mechanism',
            'tricyclic antidepressant side effects alpha 1 blockade'
        ]
    },
    {
        'number': 44,
        'topic': 'Varenicline Mechanism',
        'queries': [
            'varenicline mechanism of action smoking cessation',
            'nicotinic partial agonist mechanism'
        ]
    },
]


def main():
    """Main function to process questions and download images."""
    print("Processing pharmacology questions...")
    print(f"Found {len(PHARMACOLOGY_QUESTIONS)} questions")
    
    # Create output directory
    output_dir = Path("pharmacology_images")
    output_dir.mkdir(exist_ok=True)
    
    # Create a log file
    log_file = output_dir / "download_log.txt"
    
    downloaded_count = 0
    failed_count = 0
    
    print(f"Starting download process for {len(PHARMACOLOGY_QUESTIONS)} questions...")
    print(f"Output directory: {output_dir.absolute()}\n")
    
    with open(log_file, 'w', encoding='utf-8') as log:
        log.write("Pharmacology Question Image Download Log\n")
        log.write("=" * 50 + "\n\n")
        
        for idx, q in enumerate(PHARMACOLOGY_QUESTIONS, 1):
            q_num = q['number']
            topic = q['topic']
            queries = q['queries']
            
            print(f"\n[{idx}/{len(PHARMACOLOGY_QUESTIONS)}] Processing Question {q_num}: {topic}")
            log.write(f"Question {q_num}: {topic}\n")
            log.write(f"  Search queries: {queries}\n")
            
            # Process each query to get one image (2 queries = 2 images)
            images_downloaded = 0
            
            for query_idx, query in enumerate(queries):
                if images_downloaded >= 2:  # Stop after 2 images
                    break
                
                option_letter = 'a' if query_idx == 0 else 'b'
                print(f"  Searching for option {option_letter.upper()}: {query}")
                
                # Search for images using this query
                search_results = search_wikimedia_commons(query, limit=10)
                
                if not search_results:
                    # Try alternative search terms
                    alt_terms = [
                        query.replace(' ', '_'),
                        query.lower(),
                        ' '.join(query.split()[:3])  # First 3 words
                    ]
                    for alt_term in alt_terms:
                        search_results = search_wikimedia_commons(alt_term, limit=10)
                        if search_results:
                            break
                
                # Try to find a suitable image
                image_found = False
                
                if search_results:
                    for result in search_results:
                        filename = result.get('title', '')
                        
                        if not filename.startswith('File:'):
                            continue
                        
                        # Skip PDFs and other non-image files
                        filename_lower = filename.lower()
                        if any(ext in filename_lower for ext in ['.pdf', '.doc', '.docx', '.txt', '.zip', '.tar', '.gz']):
                            continue
                        
                        # Only accept image file extensions
                        if not any(ext in filename_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp', '.tiff', '.tif']):
                            continue
                        
                        # Try to get image URL directly
                        image_url = get_image_url(filename)
                        
                        if image_url:
                            # Determine file extension
                            ext = '.jpg'
                            if '.png' in image_url.lower() or '.png' in filename.lower():
                                ext = '.png'
                            elif '.gif' in image_url.lower() or '.gif' in filename.lower():
                                ext = '.gif'
                            elif '.svg' in image_url.lower() or '.svg' in filename.lower():
                                ext = '.svg'
                            
                            # Create option filename
                            output_path = output_dir / f"question_{q_num:02d}_option_{option_letter}{ext}"
                            
                            print(f"    Downloading: {filename}")
                            log.write(f"  Option {option_letter.upper()}: {filename}\n")
                            log.write(f"    Query: {query}\n")
                            log.write(f"    URL: {image_url}\n")
                            
                            if download_image(image_url, output_path):
                                # Get metadata and add citation overlay
                                metadata = get_image_metadata(filename)
                                if metadata:
                                    if add_citation_overlay(output_path, metadata):
                                        print(f"    ✓ Saved with citation to {output_path}")
                                        log.write(f"    ✓ Successfully saved with citation\n")
                                        log.write(f"    Citation: \"{metadata['title']}\" by {metadata['author']} {metadata['license']}\n")
                                    else:
                                        print(f"    ✓ Saved to {output_path} (citation overlay failed)")
                                        log.write(f"    ✓ Saved (citation overlay failed)\n")
                                else:
                                    print(f"    ✓ Saved to {output_path} (metadata not available)")
                                    log.write(f"    ✓ Saved (metadata not available)\n")
                                downloaded_count += 1
                                images_downloaded += 1
                                image_found = True
                                break
                            else:
                                log.write(f"    ✗ Download failed\n")
                
                if not image_found:
                    print(f"    ✗ No image found for query: {query}")
                    log.write(f"    ✗ No image found for query: {query}\n")
            
            if images_downloaded == 0:
                print(f"  ✗ No CC-licensed images found for Question {q_num}")
                log.write(f"  ERROR: No CC-licensed images found\n\n")
                failed_count += 1
            elif images_downloaded < 2:
                print(f"  Note: Only {images_downloaded} image(s) downloaded (wanted 2 options)")
                log.write(f"  Note: Only {images_downloaded} image(s) downloaded\n\n")
            else:
                log.write(f"  ✓ Successfully downloaded 2 images\n\n")
            
            # Be polite to the API
            time.sleep(0.5)
            
            # Progress update every 10 questions
            if idx % 10 == 0:
                print(f"\nProgress: {idx}/{len(PHARMACOLOGY_QUESTIONS)} questions processed ({downloaded_count} downloaded, {failed_count} failed)")
    
    print(f"\n{'='*50}")
    print(f"Download complete!")
    print(f"Successfully downloaded: {downloaded_count}/{len(PHARMACOLOGY_QUESTIONS) * 2} images (target: 2 per question)")
    print(f"Failed: {failed_count}/{len(PHARMACOLOGY_QUESTIONS)}")
    print(f"\nImages saved to: {output_dir.absolute()}")
    print(f"Log file: {log_file.absolute()}")


if __name__ == "__main__":
    main()

