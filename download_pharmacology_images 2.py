#!/usr/bin/env python3
"""
Script to download Creative Commons licensed images for pharmacology medical education questions.
Uses Wikimedia Commons API to find and download CC-licensed images with citation overlays.
Downloads 2 image options per question.
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

# Pharmacology content with all questions
PHARMACOLOGY_CONTENT = """IvyTutoring

*Be sure to watch the recorded session along with this document to make sure you get the full explanations. 

IvyTutoring

PHARMACOLOGY HIGH-YIELD NOTES

Question 1: A 62-year-old man with long-standing alcoholic cirrhosis is brought to the clinic because of several days of worsening confusion and tremor. He recently started a highly protein bound antiarrhythmic after an episode of atrial fibrillation. His exam shows mild jaundice and asterixis. Labs reveal low serum albumin.

 Which change in this medication's pharmacokinetics is expected in this patient?

Answer: Increased volume of distribution

Explanation: Hypoalbuminemia from cirrhosis reduces protein binding, which increases the free fraction of highly protein bound drugs. More unbound drug allows wider tissue distribution, increasing the apparent volume of distribution.

Question 2:A 71-year-old man with chronic systolic heart failure presents for evaluation of worsening leg swelling and dyspnea over the past week. He is prescribed a hydrophilic loop diuretic to manage his volume overload. Exam shows bilateral pitting edema up to the knees and elevated jugular venous pressure.

 How does his current fluid status affect the pharmacokinetics of this medication?

Answer: Increased volume of distribution, requiring a higher loading dose

Explanation: Hydrophilic drugs distribute primarily within extracellular fluid. In conditions such as CHF with edema, the extracellular compartment is expanded, increasing the drug's volume of distribution and diluting its concentration.

PHARMACOKINETICS & PHARMACODYNAMICS

Question 3: A 34-year-old woman is started on a new anticonvulsant for partial seizures. Two weeks later her dose is increased because of persistent breakthrough symptoms. Within days she develops ataxia, vomiting, and nystagmus. Serum drug levels are markedly elevated despite only a modest dose increase.

 Which type of elimination kinetics best explains this sudden toxicity?

Answer: Zero-order elimination

Explanation: Zero-order elimination occurs when metabolic pathways become saturated, causing a constant amount of drug to be removed per unit time. This means small dose increases can produce disproportionate rises in drug levels and toxicity.

Question 4: A 45-year-old man presents with tinnitus, nausea, and rapid breathing after intentionally ingesting a large quantity of aspirin. Labs show mixed respiratory alkalosis and metabolic acidosis. Providers note that despite supportive care, his serum salicylate concentration continues to rise.

 Why does aspirin begin to accumulate at toxic doses?

Answer: Enzyme saturation producing zero-order elimination

Explanation: At therapeutic levels, aspirin is cleared by first-order kinetics. In overdose, metabolic pathways saturate, shifting elimination to zero-order where a fixed amount is cleared per time regardless of concentration.

Question 5:A 38-year-old factory worker collapses after inhaling fumes during a chemical spill. He is noted to have bright red skin and severe lactic acidosis. High-flow oxygen therapy fails to improve his mental status.

 Which mechanism best explains this patient's condition?

Answer: Noncompetitive inhibition of cytochrome oxidase decreasing Vmax

Explanation: Cyanide binds allosterically to Complex IV (cytochrome oxidase), producing noncompetitive inhibition that reduces Vmax and halts oxidative phosphorylation.

Question 6: A 45-year-old man presents after ingesting antifreeze and is found to have severe metabolic acidosis and flank pain. He is started on intravenous ethanol in the emergency department.

 What is the mechanism by which ethanol provides benefit in this scenario?

Answer: Competitive inhibition of alcohol dehydrogenase

Explanation: Ethanol has a higher affinity than methanol or ethylene glycol for alcohol dehydrogenase, competitively inhibiting formation of toxic metabolites.

Question 7: A 29-year-old man with long-standing heroin dependence begins outpatient treatment for opioid use disorder. Shortly after his first dose of buprenorphine, he develops diaphoresis, abdominal cramping, and severe agitation. He reports last using heroin earlier the same morning.

 Which pharmacologic property of buprenorphine explains these symptoms?

Answer: Partial agonism with high receptor affinity

Explanation: Buprenorphine is a high-affinity partial μ-opioid agonist. It displaces full agonists like heroin from the receptor but provides weaker activation, precipitating withdrawal in dependent individuals.

Question 8: Two new antihypertensive medications are being tested. Drug X produces a therapeutic effect at very low doses but reaches a modest maximum reduction in blood pressure. Drug Y requires higher doses to begin lowering blood pressure but can achieve a substantially larger maximal reduction.

 Which statement correctly describes the relative potency and efficacy of these drugs?

Answer: Drug X is more potent; Drug Y is more efficacious

Explanation: Potency refers to the dose needed to achieve an effect. Drug X achieves its effect at a low dose, so it is more potent. Efficacy refers to the maximal possible effect. Drug Y reaches a higher maximal effect, so it is more efficacious.

Question 9: A 24-year-old woman arrives after ingesting an unknown quantity of aspirin. She is tachypneic and nauseated. Laboratory studies reveal mixed respiratory alkalosis and metabolic acidosis. She is started on an IV sodium bicarbonate infusion.

 What is the primary purpose of administering this treatment?

Answer: Enhance renal excretion by alkalinizing urine

Explanation: Aspirin is a weak acid. Increasing urine pH promotes ionization of salicylate, reducing its tubular reabsorption and increasing renal elimination.

Question 10: A patient with suspected amphetamine toxicity presents with agitation, hypertension, and tachycardia. To hasten drug elimination, ammonium chloride is administered.

 What is the physiological rationale for this therapy?

Answer: Acidifies urine, increasing ionized drug fraction

Explanation: Amphetamines are weak bases. Acidic urine promotes ionization, which traps the drug in the renal tubules and enhances excretion.

Question 11: A patient ingests an unknown substance with a reported pKa of 8.2. You need to predict its absorption and distribution properties at physiologic pH (7.4).

 At this pH, will the drug be mostly ionized or non-ionized?

Answer: Mostly ionized, reducing membrane permeability

Explanation: A substance with a pKa of 8.2 behaves as a weak base. When pH is below pKa, weak bases become protonated and thus ionized. At physiologic pH (7.4), the drug will be mainly ionized.

Question 12: A patient receiving general anesthesia suddenly develops severe muscle rigidity, rising end tidal CO₂, tachycardia, and a rapidly increasing core temperature.

 Which anesthetic agent is most likely responsible for triggering this reaction?

Answer: Isoflurane

Explanation: Malignant hyperthermia is triggered by volatile anesthetics such as isoflurane and by succinylcholine.

Question 13: A patient requires an inhaled anesthetic that allows for extremely rapid induction and recovery during a short procedure. The clinician wants an agent with very low blood solubility.

 Which anesthetic is the best choice?

Answer: Desflurane

Explanation: Desflurane has very low blood solubility, producing rapid induction and rapid emergence from anesthesia.

PHARMACOKINETICS AND DRUG INTERACTIONS

Question 14: A 65-year-old woman with advanced liver cirrhosis arrives for evaluation after routine labs show an elevated INR. She has been on a stable dose of warfarin for several years. She denies dietary changes or missed doses. Physical exam shows jaundice and mild ascites.

 Which pharmacokinetic change explains her elevated INR?

Answer: Reduced hepatic metabolism causing drug accumulation

Explanation: Warfarin is primarily metabolized by the liver. Cirrhosis reduces hepatic metabolic capacity, prolonging warfarin half-life and increasing plasma levels.

Question 15: A 68-year-old man with sepsis is started on IV vancomycin. Due to obesity, his distribution volume is significantly increased. The team must determine an appropriate loading dose to achieve target trough levels.

 How should the loading dose be adjusted?

Answer: Increase the loading dose to fill the expanded distribution space

Explanation: Vancomycin distributes widely in total body water. Obesity expands this compartment and increases Vd, requiring a higher loading dose to achieve therapeutic concentrations.

Question 16: A 72-year-old woman with chronic kidney disease presents with nausea, blurred yellow vision, and bradycardia. She has been taking digoxin for atrial fibrillation. Labs show elevated digoxin levels and reduced GFR.

 What explains her toxicity?

Answer: Reduced renal clearance causing accumulation

Explanation: Digoxin is primarily renally eliminated. CKD prolongs clearance and half-life, leading to elevated levels and the characteristic toxicity.

DRUG METABOLISM AND INTERACTIONS

Question 17: A 60-year-old man with atrial fibrillation is stable on warfarin therapy. He begins rifampin for tuberculosis treatment. A week later his INR is subtherapeutic.

 How should his warfarin maintenance dose be adjusted?

Answer: Increase the dose due to increased metabolism

Explanation: Rifampin is a strong inducer of hepatic CYP450 enzymes. This accelerates metabolism of warfarin and reduces its anticoagulant effect, requiring a higher maintenance dose.

Question 18: A 72-year-old woman taking diazepam becomes confused and excessively sedated. She has no hepatic disease and is on no interacting medications.

 Which metabolic pathway is often reduced in elderly patients and likely contributes to her symptoms?

Answer: Phase I (oxidation)

Explanation: Aging reduces Phase I metabolic activity (oxidation, reduction, hydrolysis). Diazepam relies heavily on Phase I metabolism, so its clearance decreases in older adults.

Question 19: A patient on warfarin begins ciprofloxacin for a urinary tract infection. One week later, her INR becomes markedly elevated.

 Which interaction explains this finding?

Answer: CYP450 inhibition raising warfarin levels

Explanation: Ciprofloxacin inhibits CYP450 metabolism of warfarin. This increases warfarin concentration and elevates INR.

Question 20: A 45-year-old man with COPD treated with theophylline develops tremors, tachyarrhythmias, and nausea after starting ciprofloxacin.

 Which mechanism explains the toxicity?

Answer: CYP1A2 inhibition increasing theophylline levels

Explanation: Theophylline is metabolized by CYP1A2. Ciprofloxacin inhibits this enzyme, causing theophylline accumulation and toxicity.

AUTONOMIC PHARMACOLOGY

Question 21: A 55-year-old man taking isoniazid for tuberculosis develops joint pain, fever, and anti-histone antibodies consistent with drug-induced lupus.

 Which genetic trait predisposes him to this reaction?

Answer: Slow acetylation

Explanation: Isoniazid is metabolized by N-acetyltransferase. Slow acetylators accumulate the parent drug and are at higher risk for drug-induced lupus.

Question 22: A 30-year-old man with severe palmar hyperhidrosis is prescribed a topical treatment that reduces sweating.

 Blockade of which neurotransmitter mediates this effect?

Answer: Acetylcholine

Explanation: Sweat glands are innervated by sympathetic cholinergic fibers, which release acetylcholine acting on muscarinic receptors.

Question 23: A 72-year-old man with benign prostatic hyperplasia begins tamsulosin therapy. Soon after, he experiences dizziness when standing.

 Which mechanism explains this side effect?

Answer: α₁ blockade causing peripheral vasodilation

Explanation: Tamsulosin blocks α₁ receptors, relaxing smooth muscle in the prostate and blood vessels. Reduced vascular tone leads to orthostatic hypotension.

Question 24: A patient with asthma develops acute dyspnea and wheezing during exercise. He uses his rescue inhaler and rapidly improves.

 Which receptor does this medication stimulate?

Answer: β₂

Explanation: Albuterol is a selective β₂ agonist that increases cAMP and relaxes bronchial smooth muscle, producing bronchodilation.

Question 25: A 30-year-old man is stung by a bee while hiking. Within minutes he develops rapidly progressive shortness of breath, diffuse wheezing, lightheadedness, and widespread urticaria. His blood pressure on arrival to the emergency department is 78/40 mm Hg, and he is speaking in 1–2 word sentences.

 What is the most appropriate immediate treatment?

Answer: IM epinephrine

Explanation: Anaphylaxis requires rapid intramuscular epinephrine, which activates α receptors to reverse hypotension and β₂ receptors to relieve bronchoconstriction.

Question 26: A 43-year-old man is evaluated for difficulty voiding after undergoing an inguinal hernia repair earlier that day. He reports suprapubic discomfort and inability to urinate despite feeling a full bladder. Bladder scan reveals significant post-void residual volume without obstruction.

 Which medication is most appropriate?

Answer: Bethanechol

Explanation: Bethanechol is a direct muscarinic agonist that stimulates M₃ receptors in the bladder, promoting detrusor contraction and relieving postoperative urinary retention.

Question 27: A 38-year-old woman collapses after working with agricultural pesticides. She arrives confused and diaphoretic, with pinpoint pupils, diffuse wheezing, bradycardia, and profuse oral secretions. Her clothing has a strong chemical odor.

 Which medication should be administered immediately?

Answer: Atropine

Explanation: Organophosphate poisoning causes excess acetylcholine at muscarinic receptors. Atropine competitively blocks these receptors and rapidly improves secretions, bronchospasm, and bradycardia.

Question 28: A 50-year-old man with chronic kidney disease presents with severe headache and chest pressure. His blood pressure is 238/126 mm Hg. IV medication is started to rapidly reduce his blood pressure while preserving renal perfusion. Shortly afterward his blood pressure decreases without signs of worsening renal function.

 Which mechanism of action corresponds to this drug?

Answer: D₁ receptor agonism causing renal vasodilation

Explanation: Fenoldopam is a selective D₁ receptor agonist that produces arteriolar vasodilation, particularly in the renal vasculature.

Question 29: A 60-year-old man with long-standing reflux symptoms reports worsening nocturnal heartburn despite lifestyle modifications. Endoscopy shows mild esophagitis. His physician prescribes famotidine to reduce his gastric acidity.

 What is the target and mechanism of this medication?

Answer: H₂ receptor blockade reducing gastric acid secretion

Explanation: Famotidine blocks H₂ receptors on parietal cells, reducing cAMP-mediated activation of the proton pump and lowering acid production.

Question 30: A 65-year-old woman recently diagnosed with early-stage Alzheimer's disease is started on donepezil due to progressive memory impairment. Over the next few weeks her family notices modest improvement in daily functioning.

 Which receptor pathway is enhanced by this medication?

Answer: Acetylcholinesterase inhibition increasing M₁ signaling

Explanation: Donepezil inhibits acetylcholinesterase, increasing synaptic acetylcholine levels and enhancing M₁ receptor activity.

Question 31: A 62-year-old man presents with acute decompensated heart failure. He has cool extremities, low urine output, and a blood pressure of 86/54 mm Hg. An IV infusion of dobutamine is started to improve perfusion.

 Which receptor and physiologic effect best describe this medication?

Answer: β₁ agonism increasing contractility and heart rate

Explanation: Dobutamine predominantly stimulates β₁ receptors, boosting cardiac output through increased contractility and mild tachycardia.

Question 32: A 47-year-old woman undergoing chemotherapy reports persistent nausea and early satiety. She is prescribed metoclopramide to reduce nausea and improve gastric emptying.

 What is the mechanism of this medication?

Answer: D₂ receptor antagonism enhancing GI motility

Explanation: Metoclopramide blocks D₂ receptors in the chemoreceptor trigger zone and increases acetylcholine activity in the GI tract, improving motility.

Question 33: A 10-year-old boy with difficulty concentrating and hyperactivity is diagnosed with ADHD. He is started on methylphenidate, and his teachers report improved focus and classroom performance after several weeks.

 What is the mechanism of action of this medication?

Answer: Reversal of NET and DAT increasing catecholamines

Explanation: Methylphenidate enhances levels of norepinephrine and dopamine by reversing their reuptake transporters, improving attention and executive function.

Question 34: A 45-year-old woman treated with MAO inhibitors for refractory depression uses cocaine at a party and soon develops severe hypertension with chest pain and agitation. She is brought to the emergency department with a blood pressure of 232/128 mm Hg.

 What mechanism explains the severity of her hypertensive crisis?

Answer: Cocaine blocks norepinephrine reuptake while MAOIs prevent breakdown

Explanation: MAO inhibitors prevent metabolism of norepinephrine, while cocaine blocks its reuptake. The combination causes massive synaptic accumulation.

Question 35: A 70-year-old man presents with fever, rigors, confusion, and marked hypotension. His skin is warm and flushed. Blood cultures are drawn, and broad-spectrum antibiotics are started. He remains hypotensive despite fluid resuscitation and requires a vasopressor.

 Which agent is most appropriate?

Answer: Norepinephrine

Explanation: Norepinephrine is first line for septic shock. It increases mean arterial pressure primarily through α₁-mediated vasoconstriction with limited β₁ activity.

RECEPTOR LOCATIONS AND DRUG EFFECTS

Question 36: A 58-year-old woman presents with uncontrollable blinking and forceful eyelid closure that interfere with reading and driving. She is diagnosed with blepharospasm and receives periodic injections around the eyelids. Over the next several days, she notices marked improvement in eyelid relaxation.

 What is the mechanism by which this treatment works?

Answer: Inhibits acetylcholine release at the neuromuscular junction

Explanation: Botulinum toxin cleaves SNARE proteins and prevents presynaptic release of acetylcholine. Without ACh, the muscle cannot contract.

Question 37: A 52-year-old man with episodic headaches, palpitations, and diaphoresis is diagnosed with a catecholamine-secreting adrenal tumor. He is scheduled for surgical removal and must be stabilized preoperatively due to episodic severe hypertension.

 Which drug class should be started first and why?

Answer: Irreversible alpha-blocker to maintain steady blockade

Explanation: Phenoxybenzamine irreversibly blocks alpha receptors, preventing catecholamine-induced vasoconstriction during tumor manipulation.

Question 38: A 78-year-old man on standard-dose digoxin for atrial fibrillation develops nausea, confusion, and yellow-tinged vision. His renal function is stable. He has lost weight over the past year and has reduced muscle mass.

 Which age-related pharmacokinetic change predisposed him to toxicity?

Answer: Decreased volume of distribution for hydrophilic drugs

Explanation: Elderly patients have reduced total body water and lean mass. Hydrophilic drugs like digoxin have a smaller distribution space, causing higher serum concentrations.

Question 39: A 57-year-old man with chronic back pain begins taking ibuprofen several times a day. He has a history of peptic ulcer disease treated successfully five years ago. Two weeks later he develops epigastric pain and dark stools.

 Which complication is most concerning in this patient?

Answer: Gastrointestinal bleeding

Explanation: NSAIDs inhibit prostaglandin synthesis, decreasing gastric mucus, bicarbonate, and mucosal blood flow, predisposing to ulcer formation and bleeding.

Question 40: A 79-year-old woman takes diphenhydramine nightly for insomnia. Her daughter notices increasing confusion, dry mouth, and a recent fall. She has no underlying dementia and takes no sedatives.

 Why is diphenhydramine problematic in this population?

Answer: It has strong anticholinergic effects

Explanation: Diphenhydramine is a first-generation H₁ blocker with potent anticholinergic activity, causing confusion, urinary retention, dental dryness, and falls in older adults.

Question 41: A 66-year-old woman with decompensated cirrhosis presents with confusion and easy bruising. Lab studies show low albumin levels. She takes several medications that are normally highly protein-bound.

 How does hypoalbuminemia affect these drugs?

Answer: Increased free drug concentration and toxicity risk

Explanation: Low albumin leaves fewer binding sites for highly protein-bound drugs, increasing the free, active fraction. This raises toxicity risk even at standard doses.

Question 42: A 75-year-old man is prescribed diazepam for anxiety. Over weeks he becomes excessively sedated and slow to respond. He has normal liver enzyme levels but low metabolic reserve due to age.

 Which pharmacokinetic property makes diazepam risky for older adults?

Answer: Extensive Phase I metabolism with active metabolites

Explanation: Diazepam requires Phase I oxidation, which declines with age. This slows clearance and increases accumulation of active metabolites, causing prolonged sedation.

COMMON DRUGS TO AVOID IN THE ELDERLY

Question 43: A 70-year-old woman begins amitriptyline for neuropathic pain. After several days she reports dizziness when standing, nearly fainting, and palpitations. Orthostatic vitals show a marked drop in systolic pressure.

 Which mechanism explains her symptoms?

Answer: α₁ receptor blockade

Explanation: Tricyclic antidepressants block α₁ receptors, causing peripheral vasodilation and impaired reflex responses, leading to orthostatic hypotension.

Question 44: A 42-year-old man with a 25 pack-year smoking history presents wanting to quit after developing chronic cough and reduced exercise tolerance. He has tried nicotine gum in the past but relapsed within weeks due to intense cravings and irritability. He asks for the most effective evidence-based medication to support smoking cessation.

 Which therapy is considered first line for smoking cessation?

Answer: Varenicline

Explanation: Varenicline is a partial agonist at α4β2 nicotinic receptors. It reduces cravings by partially stimulating the receptor while simultaneously blocking nicotine from producing its full reinforcing effect.
"""


def extract_questions(content: str) -> List[Dict[str, str]]:
    """Extract questions and their main topics from the content."""
    questions = []
    
    # Pattern to match questions
    question_pattern = r'Question (\d+):\s*(.*?)(?=Answer:|$)'
    
    # Find all questions
    question_matches = re.finditer(question_pattern, content, re.DOTALL)
    
    for match in question_matches:
        q_num = int(match.group(1))
        q_text = match.group(2).strip()
        
        # Find the corresponding answer
        answer_match = re.search(
            rf'Question {q_num}:.*?Answer:\s*(.*?)(?=Explanation:|$)',
            content,
            re.DOTALL
        )
        
        if answer_match:
            answer = answer_match.group(1).strip()
            # Extract main topic from answer (usually the condition/disease name)
            topic = extract_topic(answer, q_text)
            
            questions.append({
                'number': q_num,
                'question': q_text,
                'answer': answer,
                'topic': topic
            })
    
    return questions


def main():
    """Main function to process questions and download images."""
    print("Extracting questions from pharmacology content...")
    questions = extract_questions(PHARMACOLOGY_CONTENT)
    
    print(f"Found {len(questions)} questions")
    
    # Create output directory
    output_dir = Path("pharmacology_images")
    output_dir.mkdir(exist_ok=True)
    
    # Create a log file
    log_file = output_dir / "download_log.txt"
    
    downloaded_count = 0
    failed_count = 0
    
    print(f"Starting download process for {len(questions)} questions...")
    print(f"Output directory: {output_dir.absolute()}\n")
    
    with open(log_file, 'w', encoding='utf-8') as log:
        log.write("Pharmacology Question Image Download Log\n")
        log.write("=" * 50 + "\n\n")
        
        for idx, q in enumerate(questions, 1):
            q_num = q['number']
            topic = q['topic']
            
            print(f"\n[{idx}/{len(questions)}] Processing Question {q_num}: {topic}")
            log.write(f"Question {q_num}: {topic}\n")
            log.write(f"  Question: {q['question'][:100]}...\n")
            log.write(f"  Answer: {q['answer'][:100]}...\n")
            
            # Search for images
            search_results = search_wikimedia_commons(topic, limit=20)  # Get more results for 2 options
            
            if not search_results:
                # Try alternative search terms
                alt_terms = [
                    topic.replace(' ', '_'),
                    topic.lower(),
                    q['answer'].split()[0] if q['answer'] else topic
                ]
                for alt_term in alt_terms:
                    search_results = search_wikimedia_commons(alt_term, limit=20)
                    if search_results:
                        break
            
            # Process Wikimedia Commons results - download 2 options per question
            images_downloaded = 0
            image_found = False
            
            if search_results:
                for result_idx, result in enumerate(search_results):
                    if images_downloaded >= 2:  # Stop after 2 images
                        break
                    
                    filename = result.get('title', '')
                    
                    if not filename.startswith('File:'):
                        continue
                    
                    # Try to get image URL directly (most Wikimedia Commons images are CC)
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
                        
                        # Create option A and B filenames
                        option_letter = 'a' if images_downloaded == 0 else 'b'
                        output_path = output_dir / f"question_{q_num:02d}_option_{option_letter}{ext}"
                        
                        print(f"  Downloading option {option_letter.upper()}: {filename}")
                        log.write(f"  Downloading option {option_letter.upper()}: {filename}\n")
                        log.write(f"  URL: {image_url}\n")
                        
                        if download_image(image_url, output_path):
                            # Get metadata and add citation overlay
                            metadata = get_image_metadata(filename)
                            if metadata:
                                if add_citation_overlay(output_path, metadata):
                                    print(f"  ✓ Saved with citation to {output_path}")
                                    log.write(f"  ✓ Successfully saved with citation\n")
                                    log.write(f"  Citation: \"{metadata['title']}\" by {metadata['author']} {metadata['license']}\n\n")
                                else:
                                    print(f"  ✓ Saved to {output_path} (citation overlay failed)")
                                    log.write(f"  ✓ Saved (citation overlay failed)\n\n")
                            else:
                                print(f"  ✓ Saved to {output_path} (metadata not available)")
                                log.write(f"  ✓ Saved (metadata not available)\n\n")
                            downloaded_count += 1
                            images_downloaded += 1
                            image_found = True
                        else:
                            log.write(f"  ✗ Download failed\n")
            
            if not image_found:
                print(f"  ✗ No CC-licensed image found for Question {q_num}")
                log.write(f"  ERROR: No CC-licensed image found\n\n")
                failed_count += 1
            elif images_downloaded < 2:
                print(f"  Note: Only {images_downloaded} image(s) downloaded (wanted 2 options)")
                log.write(f"  Note: Only {images_downloaded} image(s) downloaded\n\n")
            
            # Be polite to the API
            time.sleep(0.5)
            
            # Progress update every 10 questions
            if idx % 10 == 0:
                print(f"\nProgress: {idx}/{len(questions)} questions processed ({downloaded_count} downloaded, {failed_count} failed)")
    
    print(f"\n{'='*50}")
    print(f"Download complete!")
    print(f"Successfully downloaded: {downloaded_count}/{len(questions) * 2} images (target: 2 per question)")
    print(f"Failed: {failed_count}/{len(questions)}")
    print(f"\nImages saved to: {output_dir.absolute()}")
    print(f"Log file: {log_file.absolute()}")


if __name__ == "__main__":
    main()

