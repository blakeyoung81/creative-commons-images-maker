#!/usr/bin/env python3
"""
Script to download Creative Commons licensed images for renal/urology medical education questions.
Downloads 2 image options per question with citation overlays.
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

# Renal/Urology content with all questions
RENAL_CONTENT = """IvyTutoring

IvyTutoring

CONGENITAL RENAL ANOMALIES

Question 1: What anatomical structure prevents the ascent of fused kidneys in a horseshoe kidney?

Answer: Inferior mesenteric artery

Explanation: In horseshoe kidney, the fusion of the kidneys at their lower poles prevents their ascent past the inferior mesenteric artery.

Note: Patients with horseshoe kidney are often asymptomatic but may have an increased risk of urinary tract infections and kidney stones.

Question 2: What is the likely cause of urinary obstruction in a 2-day-old male infant who has not urinated since birth and presents with a lower abdominal mass?

Answer: Posterior urethral valves

Explanation: Posterior urethral valves are a congenital cause of bladder outlet obstruction in male infants, often leading to urinary retention and bladder distension.

Note: This condition can be detected prenatally via ultrasound showing bladder distension or hydronephrosis.

ACUTE AND CHRONIC KIDNEY DISEASES

Question 3: A 5-year-old girl with recurrent fevers and abdominal pain has dilated calyces and cortical atrophy on renal ultrasound. What is the most likely diagnosis?

Answer: Reflux nephropathy

Explanation: Reflux nephropathy results from vesicoureteral reflux, causing recurrent kidney infections and scarring.

Note: Untreated reflux nephropathy can lead to hypertension and chronic kidney disease.

Question 4: An elderly patient with uncontrolled hypertension presents with elevated creatinine and BUN. Renal biopsy shows hyaline deposits in small arterioles. What is the pathology?

Answer: Hyaline arteriolosclerosis

Explanation: Hyaline arteriolosclerosis is characterized by thickening of the vessel walls due to plasma protein leakage, commonly seen in hypertension and diabetes.

Note: This condition can lead to chronic kidney damage and glomerulosclerosis.

Question 5: A patient develops fever, rash, and decreased urine output one week after starting amoxicillin. Urine microscopy shows eosinophils, WBCs, and RBCs. Which part of the kidney is affected?

Answer: Renal interstitium

Explanation: Acute interstitial nephritis is a hypersensitivity reaction affecting the renal interstitium, often triggered by medications like β-lactams.

Note: Symptoms include fever, rash, eosinophilia, and signs of acute kidney injury.

Question 6: A patient develops oliguria two days after CPR. Urine sediment shows muddy brown casts. Which renal structure is involved?

Answer: Proximal tubules

Explanation: Acute tubular necrosis, often due to ischemia, affects the proximal tubules, leading to muddy brown casts in urine.

Note: The proximal tubules and thick ascending limbs are most susceptible to ischemic injury.

Question 7: A patient with gastrointestinal bleeding develops acute kidney injury. After initial oliguria, urine output increases significantly. What electrolyte imbalance is likely during this phase?

Answer: Hypokalemia

Explanation: During the recovery phase of acute tubular necrosis, increased diuresis can lead to electrolyte wasting, including hypokalemia.

Note: Monitoring electrolytes is crucial during the recovery phase to prevent complications.

Question 8: An elderly man with hypertension and bilateral renal artery stenosis is started on an ACE inhibitor. What changes occur in renal hemodynamics?

Answer: Decreased renal perfusion, decreased intraglomerular pressure, and decreased filtration fraction

Explanation: ACE inhibitors reduce angiotensin II levels, leading to decreased efferent arteriolar constriction and reduced glomerular pressure.

Note: In patients with renal artery stenosis, ACE inhibitors can significantly reduce kidney function.

Question 9: After gynecologic surgery, a patient's left ureter is injured and repaired. Postoperative imaging shows mild hydronephrosis. What urodynamic changes are expected?

Answer: Decreased GFR and decreased filtration fraction

Explanation: Acute ureteral obstruction increases hydrostatic pressure in Bowman's space, reducing GFR and filtration fraction.

Note: Persistent obstruction can lead to chronic kidney damage if not addressed.

Question 10: An elderly man with back pain, normocytic anemia, and elevated creatinine has increased serum calcium. Renal biopsy shows eosinophilic tubular casts. What is the diagnosis?

Answer: Multiple myeloma

Explanation: Multiple myeloma is characterized by bone pain, anemia, renal impairment, and hypercalcemia due to monoclonal protein deposition.

Note: Diagnosis is confirmed by detecting monoclonal paraproteinemia (M-spike) on serum electrophoresis.

Question 11: A young trauma patient with massive hemorrhage develops high BUN and low urine output. What lab finding confirms prerenal azotemia?

Answer: Urine sodium < 20 mEq/L

Explanation: Prerenal azotemia is indicated by low urine sodium, reflecting the kidney's attempt to conserve sodium due to decreased perfusion.

Note: Differentiating prerenal azotemia from acute tubular necrosis is crucial for appropriate management.

ELECTROLYTE AND ACID-BASE IMBALANCE

Question 12: A man becomes oliguric after a prolonged seizure. His labs show elevated creatinine and positive urine dipstick for blood, but no red blood cells are present. What is the underlying mechanism?

Answer: Tubular injury due to rhabdomyolysis

Explanation: Rhabdomyolysis leads to the release of myoglobin into the bloodstream, which can cause acute kidney injury. The presence of myoglobin in urine results in a positive dipstick test for blood without actual red blood cells.

Note: Rhabdomyolysis can result from seizures, trauma, or drug use, and is characterized by elevated creatinine, hyperkalemia, hyperphosphatemia, and hypocalcemia.

Question 13: A patient with end-stage renal disease (ESRD) presents with muscle cramps and tingling fingers. His serum calcium is 6.5 mg/dL. What other electrolyte imbalance is likely?

Answer: Hyperphosphatemia

Explanation: In chronic kidney disease, phosphate excretion is reduced, leading to hyperphosphatemia. This binds free calcium, causing hypocalcemia, which can lead to secondary hyperparathyroidism.

Note: Hypocalcemia can cause neuromuscular irritability, prolonged QT interval, and seizures.

Question 14: An elderly man with chronic kidney disease has high serum calcium and elevated parathyroid hormone (PTH) levels. What is the diagnosis?

Answer: Tertiary hyperparathyroidism

Explanation: Tertiary hyperparathyroidism occurs after prolonged secondary hyperparathyroidism, leading to autonomous parathyroid gland hyperplasia and persistent PTH elevation, even after correcting phosphate and calcium levels.

Note: This condition results in very high PTH levels with hypercalcemia and hyperphosphatemia.

Question 15: An elderly patient with heart failure presents with worsening leg swelling and shortness of breath. Which nephron segment does the primary diuretic act on?

Answer: Thick ascending limb of Henle's loop

Explanation: Loop diuretics, such as furosemide, act on the thick ascending limb of Henle's loop to inhibit the Na+/K+/2Cl− transporter, reducing fluid overload in heart failure.

Note: Loop diuretics are effective for treating pulmonary and peripheral edema associated with heart failure.

Question 16: A young man is brought to the emergency department with confusion and lethargy. His arterial blood gas shows a pH of 7.54 and PaCO₂ of 49 mm Hg. What is the next diagnostic step?

Answer: Urine chloride

Explanation: In metabolic alkalosis, assessing urine chloride helps determine the cause. Low urine chloride suggests volume depletion (e.g., vomiting, diuretic use), while high urine chloride indicates mineralocorticoid excess.

Note: Metabolic alkalosis is characterized by elevated bicarbonate and compensatory respiratory acidosis.

Question 17: An elderly man with a history of smoking presents with weakness, hypercalcemia, and a chronic cough. What lab findings are expected?

Answer: Decreased PTH, increased PTHrP, decreased phosphate

Explanation: Squamous cell carcinoma of the lung can produce parathyroid hormone-related peptide (PTHrP), mimicking PTH effects, leading to hypercalcemia and hypophosphatemia.

Note: PTHrP production is common in malignancies and results in hypercalcemia of malignancy.

Question 18: An elderly man with back pain, elevated creatinine, and anemia has a calcium level of 12 mg/dL. What is the mechanism of hypercalcemia?

Answer: Calcium release from bone

Explanation: Hypercalcemia in malignancy, such as multiple myeloma, is often due to osteolytic bone lesions, leading to calcium release into the bloodstream.

Note: Multiple myeloma is associated with bone pain, fractures, and lytic lesions, with lab findings of low PTH and PTHrP.

Question 19: A 59-year-old man with diabetes and hypertension experiences a mild increase in serum creatinine and potassium three weeks after starting a new medication. Which drug is likely responsible?

Answer: Lisinopril

Explanation: ACE inhibitors like lisinopril reduce angiotensin II formation, decreasing efferent arteriole constriction, which can slightly reduce GFR and cause mild creatinine elevation and hyperkalemia.

Note: A creatinine increase of more than 30% may indicate renal artery stenosis.

Question 20: A severely dehydrated patient is evaluated. Where in the nephron does the majority of water reabsorption occur?

Answer: Proximal tubule

Explanation: The proximal tubule reabsorbs the majority of water and electrolytes, independent of serum concentration, while the collecting duct, under ADH influence, regulates urine concentration.

Note: The proximal tubule is responsible for reabsorbing approximately 65% of filtered water.

Question 21: A patient with major depressive disorder presents with altered mental status. Labs show PaCO₂ = 32, HCO₃⁻ = 10, and pH = 7.34. What is the likely acid-base disturbance?

Answer: Metabolic acidosis and respiratory alkalosis

Explanation: Salicylate poisoning can cause a mixed acid-base disorder with respiratory alkalosis due to direct respiratory center stimulation and anion-gap metabolic acidosis from salicylate accumulation.

Note: Salicylate poisoning is indicated by tinnitus and a mixed acid-base disorder.

Question 22: A young woman with asthma uses excessive albuterol and presents with respiratory distress and hypokalemia. What is the mechanism?

Answer: Intracellular shift of potassium

Explanation: Beta-adrenergic stimulation from albuterol causes potassium to shift into cells, leading to hypokalemia.

Note: Other causes of intracellular potassium shift include insulin administration and alkalosis.

Question 23: A 21-year-old woman with weakness has hypokalemia and metabolic acidosis. She is concerned about her weight and has a BMI of 20. What is the cause of hypokalemia?

Answer: Self-induced diarrhea

Explanation: Self-induced diarrhea, often seen in eating disorders, leads to gastrointestinal potassium loss, causing hypokalemia and metabolic acidosis.

Note: Common causes of hypokalemia include gastrointestinal loss, diuretics, and intracellular shifts.

ELECTROLYTE AND ACID-BASE DISORDERS

Question 24: A 6-year-old child presents with vomiting, abdominal pain, and severe high-anion-gap metabolic acidosis. Blood glucose is 300 mg/dL. Which electrolyte requires careful monitoring?

Answer: Potassium

Explanation: In diabetic ketoacidosis (DKA), acidosis and decreased insulin cause potassium to shift out of cells, leading to hyperkalemia despite total body potassium depletion. Insulin therapy can cause hypokalemia by driving potassium back into cells.

Note: Always monitor potassium levels closely when treating DKA with insulin.

Question 25: After chemotherapy for chronic lymphocytic leukemia, a patient shows tall T waves on ECG. What is the immediate treatment?

Answer: Intravenous calcium

Explanation: The patient likely has hyperkalemia due to tumor lysis syndrome. IV calcium stabilizes cardiac myocytes without altering potassium levels.

Note: Hyperkalemia ECG changes include peaked T waves and prolonged QRS complexes.

Question 26: A malnourished man with a history of alcohol use receives dextrose-containing fluids and develops muscle weakness. His phosphate level is 0.4 mg/dL. What explains this hypophosphatemia?

Answer: Redistribution of phosphate into cells

Explanation: Refeeding syndrome occurs when carbohydrate intake increases insulin, driving phosphate into cells for ATP production, leading to hypophosphatemia.

Note: Refeeding syndrome can also cause deficiencies in magnesium and potassium.

Question 27: A patient with persistent vomiting for one week presents with dry mucous membranes and delayed capillary refill. What electrolyte abnormalities are likely?

Answer: Hyponatremia, hypokalemia, hypochloremia, and metabolic alkalosis

Explanation: Vomiting causes loss of hydrogen, potassium, and chloride ions, leading to hypokalemic, hypochloremic metabolic alkalosis. Volume depletion activates the renin-angiotensin-aldosterone system.

Note: Urine chloride is typically low in these patients.

Question 28: A patient with gastroenteritis has had watery diarrhea for three days. What type of acid-base disturbance is expected?

Answer: Normal anion gap (hyperchloremic) metabolic acidosis

Explanation: Diarrhea causes bicarbonate loss from the gastrointestinal tract, resulting in metabolic acidosis with a normal anion gap and increased chloride concentration.

Note: This condition is often referred to as hyperchloremic metabolic acidosis.

Question 29: A young man presents with confusion. Labs show pH 7.25, bicarbonate 12 mEq/L, PaCO₂ 28 mm Hg, sodium 136 mEq/L, and chloride 90 mEq/L. What is the most likely acid-base disorder?

Answer: Anion gap metabolic acidosis

Explanation: The low pH and bicarbonate indicate metabolic acidosis. The anion gap is calculated as Na+ - (HCO₃⁻ + Cl⁻), which is elevated, indicating an unmeasured acid.

Note: High anion gap metabolic acidosis can be due to uremia, lactic acidosis, ketoacidosis, or toxins.

RENAL TUBULAR DISORDERS

Question 30: A 2-year-old boy with poor weight gain and frequent urination has glucosuria, hypophosphatemia, hypokalemia, and normal anion gap metabolic acidosis. Which renal structure is affected?

Answer: Proximal convoluted tubule — impaired bicarbonate reabsorption

Explanation: Proximal renal tubular acidosis (type 2) results from defective bicarbonate reabsorption, leading to metabolic acidosis and features of Fanconi syndrome.

Note: All types of renal tubular acidosis cause non-anion gap metabolic acidosis.

Question 31: A 72-year-old woman with epilepsy presents with confusion, nausea, and headache. Labs show severe hyponatremia and concentrated urine. Which medication is likely responsible?

Answer: Carbamazepine

Explanation: Carbamazepine can cause syndrome of inappropriate antidiuretic hormone secretion (SIADH), leading to hyponatremia with low serum osmolality and concentrated urine.

Note: SIADH is characterized by low serum osmolality, high urine osmolality, and high urine sodium.

Question 32: A patient with constant thirst and excessive urination has low urine osmolality. Water deprivation testing shows minimal increase in urine osmolality, but a sharp rise occurs after desmopressin administration. What is the diagnosis?

Answer: Central diabetes insipidus (insufficient ADH production)

Explanation: Central diabetes insipidus is due to inadequate antidiuretic hormone (ADH) production, leading to polyuria and polydipsia. Desmopressin administration increases urine osmolality.

Note: Nephrogenic diabetes insipidus does not respond to desmopressin.

GLOMERULAR DISEASES

Question 33: A 9-year-old boy presents with cola-colored urine and facial puffiness. Blood pressure is 135/85 mmHg. Urinalysis shows +1 protein, many RBCs, and RBC casts. What is the most likely diagnosis?

Answer: Poststreptococcal glomerulonephritis (PSGN)

Explanation: PSGN occurs 2–4 weeks after a streptococcal infection, presenting with nephritic syndrome, low C3 complement levels, and subepithelial humps on electron microscopy.

Note: Differentiate from IgA nephropathy, which occurs shortly after infections and has normal complement levels.

Question 34: A 17-year-old boy experiences episodes of painless gross hematuria a few days after mild upper respiratory infections. Renal biopsy shows mesangial proliferation. What is the microscopic finding?

Answer: Mesangial deposition of IgA

Explanation: IgA nephropathy (Berger disease) is characterized by mesangial hypercellularity and IgA deposits, often triggered by respiratory infections.

Note: It is the most common cause of recurrent hematuria in young adults.

Question 35: A 25-year-old man with hemoptysis and worsening dyspnea after a flu-like illness has hematuria and proteinuria. Chest CT shows bilateral alveolar infiltrates. Autoantibodies are found against which structure?

Answer: Alpha-3 chain of type IV collagen

Explanation: Goodpasture syndrome involves autoantibodies against the alpha-3 chain of type IV collagen in glomerular and alveolar basement membranes, causing glomerulonephritis and pulmonary hemorrhage.

Note: Immunofluorescence shows linear IgG and C3 deposition along the glomerular basement membrane.

Question 36: A 6-year-old boy with generalized swelling and frothy urine has periorbital and lower extremity edema. Urinalysis reveals 4+ proteinuria without hematuria. Cholesterol is elevated. What is the cause?

Answer: Increased liver lipoprotein synthesis

Explanation: Minimal Change Disease, the most common nephrotic syndrome in children, involves podocyte damage leading to massive proteinuria and hyperlipidemia.

Note: It responds well to corticosteroids.

Question 37: A 64-year-old man with type 2 diabetes has normal creatinine but elevated urinary albumin excretion. What medication should be started to prevent kidney disease progression?

Answer: ACE inhibitor

Explanation: ACE inhibitors reduce intraglomerular pressure and albuminuria, slowing the progression of diabetic nephropathy.

Note: Early detection of diabetic nephropathy involves screening for microalbuminuria.

Question 38: A 25-year-old woman with systemic lupus erythematosus presents with weight gain, facial puffiness, and proteinuria. Kidney biopsy shows thickening of glomerular capillary walls with subepithelial spikes. What is the diagnosis?

Answer: Membranous nephropathy

Explanation: Membranous nephropathy is characterized by thickened capillary walls and subepithelial "spike and dome" appearance, associated with SLE and other conditions.

Note: It is a common cause of nephrotic syndrome in adults.

Question 39: A 56-year-old man develops worsening edema and facial puffiness. Kidney biopsy shows apple-green birefringence under polarized light with Congo red staining. What test confirms the diagnosis?

Answer: Serum protein electrophoresis

Explanation: The biopsy findings suggest amyloidosis, which can be confirmed by detecting monoclonal proteins in serum protein electrophoresis.

Note: Amyloidosis can be associated with chronic inflammatory conditions or multiple myeloma.

Question 40: An adult man with hepatitis C infection has generalized edema and proteinuria. Renal biopsy reveals diffuse glomerular hypercellularity and capillary wall thickening. Immunofluorescence shows granular staining for IgG and C3. What is the diagnosis?

Answer: Membranoproliferative glomerulonephritis (MPGN)

Explanation: MPGN is characterized by diffuse hypercellularity, capillary wall thickening, and granular immune complex deposits, often associated with hepatitis C.

Note: MPGN can present with low complement levels and "tram-track" appearance on microscopy.

URINARY TRACT TUMORS

Question 41: A heavy smoker with painless hematuria has urine cytology showing malignant cells and a bladder mass on cystoscopy. What histologic finding is associated with poor prognosis?

Answer: Involvement of the muscularis propria

Explanation: Penetration into the muscularis propria indicates a higher stage of bladder cancer and is associated with a poor prognosis.

Note: Smoking is a significant risk factor for bladder cancer.

URINARY TRACT TUMORS

Question 42: An elderly man presents with weight loss, fever, and chest pain. Imaging reveals multiple lung nodules. A biopsy of one nodule shows clear cytoplasm and polygonal cells. Which organ is the primary site of the cancer?

Answer: Kidney

Explanation: The biopsy findings are indicative of renal cell carcinoma, which often metastasizes to the lungs. The clear cells are due to lipid and glycogen accumulation.

Note: Renal cell carcinoma is associated with paraneoplastic syndromes and mutations in the VHL gene on chromosome 3.

KIDNEY STONES

Question 43: A young man experiences sudden, severe left-sided flank pain radiating to the groin, accompanied by gross hematuria. Imaging shows a small stone in the mid-ureter. What laboratory finding is most likely?

Answer: Normocalcemia, hypercalciuria

Explanation: The presentation is consistent with a calcium stone, the most common type of kidney stone. Patients often have idiopathic hypercalciuria with normal serum calcium levels.

Note: Calcium oxalate stones are the most common and can present with envelope-shaped crystals in urine.

Question 44: A patient with renal colic is diagnosed with a calcium-oxalate stone. Which medication can reduce the risk of future stone formation?

Answer: Hydrochlorothiazide

Explanation: Thiazide diuretics decrease urinary calcium excretion, reducing the risk of calcium stone formation.

Note: Dietary modifications such as reducing sodium, protein, and oxalate intake, along with increased fluid intake, can also help prevent stone formation.

Question 45: A 55-year-old woman with recurrent urinary tract infections presents with fever, dysuria, and right flank pain. Imaging reveals a large staghorn calculus. Which infection is most likely involved?

Answer: Klebsiella infection

Explanation: Staghorn calculi are often composed of struvite, which forms in the presence of urease-producing bacteria like Klebsiella.

Note: Struvite stones are radiopaque and have a characteristic coffin-lid shape.

Question 46: A 46-year-old woman with a history of ileostomy presents with dehydration and right flank pain. She passes a uric acid stone. What is the most likely mechanism of stone formation?

Answer: Concentrated acidic urine

Explanation: Uric acid stones form in acidic urine and are associated with conditions like dehydration and hyperuricemia.

Note: Uric acid stones are radiolucent and can be treated with urine alkalinization and allopurinol.

URINARY TRACT INFECTIONS

Question 47: A young woman experiences a burning sensation during urination and increased urinary frequency. She denies fever or flank pain. Urinalysis shows pyuria and bacteriuria. What is the most appropriate initial treatment?

Answer: Empiric antibiotic therapy with trimethoprim-sulfamethoxazole

Explanation: The presentation is consistent with acute cystitis, commonly caused by E. coli. Empiric treatment with TMP-SMX is appropriate.

Note: Acute cystitis is characterized by dysuria, suprapubic pain, and urinary frequency without systemic symptoms.

Question 48: An elderly diabetic woman presents with fever, chills, flank pain, and nausea. Examination reveals costovertebral angle tenderness. Urinalysis shows white blood cell casts, pyuria, and bacteriuria. What is the most likely diagnosis?

Answer: Acute pyelonephritis

Explanation: The presence of WBC casts indicates renal involvement, consistent with acute pyelonephritis.

Note: Risk factors include urinary tract obstruction, indwelling catheters, and diabetes mellitus.

OTHER RENAL CONDITIONS

Question 49: A 45-year-old man presents with flank pain and hematuria. Imaging reveals multiple fluid-filled cysts in both kidneys. What is the most likely diagnosis?

Answer: Autosomal dominant polycystic kidney disease (ADPKD)

Explanation: ADPKD is characterized by renal cysts, hypertension, and hematuria, often due to mutations in PKD1 or PKD2.

Note: Extra-renal manifestations include liver cysts and cerebral aneurysms.

Question 50: A 23-year-old pregnant woman undergoes a 20-week ultrasound showing a male fetus with enlarged, cystic kidneys and severe oligohydramnios. What neonatal complication is most likely at birth?

Answer: POTTER sequence

Explanation: ARPKD leads to impaired fetal urine output and oligohydramnios, resulting in POTTER sequence.

Note: POTTER sequence includes pulmonary hypoplasia, limb deformities, and facial anomalies.

Question 51: A 22-year-old man experiences sudden gross hematuria after minor physical activity. He has a family history of sickle cell disease. What is the most likely cause?

Answer: Renal papillary necrosis

Explanation: Sickle cell disease can lead to renal papillary necrosis due to reduced blood flow or arterial occlusion.

Note: Sickle cell trait is often asymptomatic but can predispose to renal complications.

Question 52: A 46-year-old man has difficulty urinating after laparoscopic hernia repair under general anesthesia. Ultrasound shows a post-void residual volume of 300 mL. What medication would help improve bladder emptying?

Answer: Bethanechol

Explanation: Bethanechol, a muscarinic agonist, stimulates bladder contraction and improves emptying.

Note: Postoperative urinary retention is common and can be managed with medications that enhance detrusor muscle activity.

Question 53: A menopausal woman experiences urgency and incontinence episodes. She rushes to the bathroom but has incontinence on the way. What pharmacologic action is the best treatment?

Answer: Antagonism of muscarinic cholinergic receptors

Explanation: Urge incontinence is due to detrusor overactivity and can be treated with antimuscarinic drugs like oxybutynin.

Note: Antimuscarinic agents reduce bladder contractions and improve symptoms of urge incontinence.

Question 54: A 45-year-old man with poorly controlled type 1 diabetes reports involuntary urine leakage and difficulty starting urination. What would most likely be found on further evaluation?

Answer: Increased postvoid residual volume

Explanation: Overflow incontinence is due to impaired bladder emptying, often seen in diabetes, leading to increased residual volume.

Note: Management includes intermittent catheterization to relieve bladder distension.

Question 55: A 50-year-old woman experiences urinary leakage while coughing or laughing. What is the most likely underlying cause of her condition?

Answer: Urethral sphincter dysfunction

Explanation: Stress incontinence is due to weak sphincter or pelvic floor muscles, leading to leakage with increased abdominal pressure.

Note: Kegel exercises can strengthen pelvic floor muscles and improve stress incontinence.

Question 56: A young man presents to the emergency department after a fall. He has suprapubic tenderness, and FAST ultrasound shows intraperitoneal free fluid. His urine dipstick is positive for blood. What injury is most likely present?

Answer: Bladder dome rupture

Explanation: Bladder dome rupture occurs with blunt trauma when the bladder is full, leading to intraperitoneal urine leakage.

Note: Suprapubic tenderness and hematuria are indicative of bladder injury.

Question 57: A 28-year-old woman with new-onset severe hypertension dies from an intracranial hemorrhage. Autopsy reveals tortuous carotid arteries with alternating stenosis and dilation. What vascular abnormality is most likely responsible for her condition?

Answer: Fibromuscular dysplasia causing renal artery stenosis

Explanation: Fibromuscular dysplasia affects young women and causes renal artery stenosis, leading to hypertension.

Note: FMD can also involve cerebrovascular arteries, increasing the risk of stroke or aneurysm rupture.

Question 58: A patient with new-onset edema has a urinalysis showing casts with a "Maltese cross" appearance under polarized light. What is the most likely diagnosis?

Answer: Nephrotic syndrome

Explanation: Fatty casts with a "Maltese cross" appearance are characteristic of nephrotic syndrome.

Note: Nephrotic syndrome is associated with significant proteinuria, hypoalbuminemia, and edema.
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
    print("Extracting questions from renal/urology content...")
    questions = extract_questions(RENAL_CONTENT)
    
    print(f"Found {len(questions)} questions")
    
    # Create output directory
    output_dir = Path("renal_images")
    output_dir.mkdir(exist_ok=True)
    
    # Create a log file
    log_file = output_dir / "download_log.txt"
    
    downloaded_count = 0
    failed_count = 0
    
    print(f"Starting download process for {len(questions)} questions...")
    print(f"Output directory: {output_dir.absolute()}\n")
    
    with open(log_file, 'w', encoding='utf-8') as log:
        log.write("Renal/Urology Question Image Download Log\n")
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

