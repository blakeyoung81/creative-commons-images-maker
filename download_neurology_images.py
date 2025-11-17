#!/usr/bin/env python3
"""
Script to download Creative Commons licensed images for neurology medical education questions.
Uses Wikimedia Commons API to find and download CC-licensed images with citation overlays.
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

# Neurology content with all questions
NEUROLOGY_CONTENT = """IvyTutoring

*Be sure to watch the recorded session along with this document to make sure you get the full explanations. 

IvyTutoring

NEUROLOGY HIGH-YIELD NOTES

Question 1: A 36-year-old man presents with a painful ulcer on the anterior part of his tongue. Which nerve is responsible for transmitting pain from this area?

Answer: Mandibular division of the trigeminal nerve (CN V₃)

Explanation: The mandibular division of the trigeminal nerve provides general sensation to the anterior two-thirds of the tongue.

Note: The anterior two-thirds of the tongue receives sensory innervation from CN V₃, while taste is mediated by CN VII.

Question 2: A 21-year-old woman experiences recurrent painful vesicles. Which motor protein is involved in transporting the virus during reactivation?

Answer: Kinesin

Explanation: Kinesin facilitates the anterograde transport of herpes simplex virus from the sensory ganglion to the skin during reactivation.

Note: During initial infection, the virus uses dynein for retrograde transport to the sensory ganglia.

Question 3: A 5-year-old boy has gained weight rapidly and experiences morning headaches. Which hypothalamic nucleus is likely affected?

Answer: Ventromedial nucleus

Explanation: The ventromedial nucleus regulates satiety, and its damage can lead to hyperphagia and obesity.

Note: Lesions in the ventromedial nucleus can result in constant hunger and weight gain.

Question 4: A 4-year-old boy is unable to sweat during a heatwave and has a high fever. Which hypothalamic nucleus is likely impaired?

Answer: Anterior nucleus

Explanation: The anterior hypothalamic nucleus is responsible for cooling and its damage can lead to impaired heat dissipation and hyperthermia.

Note: The anterior nucleus activates the parasympathetic system to promote cooling.

Question 5: A 39-year-old woman with bipolar disorder delivers a stillborn baby with missing brain and scalp. What is the likely maternal factor?

Answer: Valproate use

Explanation: Valproate can inhibit folate metabolism, increasing the risk of neural tube defects such as anencephaly.

Note: Anencephaly results from the failure of the neural tube to close, typically by the fourth week of gestation.

Question 6: A newborn has a small dimple with a tuft of hair over the lower back but no neurological deficits. What is the diagnosis?

Answer: Spina bifida occulta

Explanation: Spina bifida occulta is characterized by a skin dimple or tuft of hair without herniation of neural contents.

Note: Unlike other neural tube defects, spina bifida occulta does not elevate AFP levels.

Question 7: A 21-year-old woman has headaches and gait instability. MRI shows cerebellar tonsils herniating through the foramen magnum. What is the diagnosis?

Answer: Chiari I malformation

Explanation: Chiari I malformation involves the herniation of cerebellar tonsils into the spinal canal, often presenting with headaches.

Note: Chiari I malformation is typically diagnosed in adulthood, unlike Chiari II, which presents earlier.

Question 8: After a peripheral nerve injury, the distal axon and myelin break down. What process clears the debris?

Answer: Wallerian degeneration

Explanation: Wallerian degeneration involves the breakdown of the distal axon and myelin, with Schwann cells clearing debris in the PNS.

Note: Chromatolysis occurs in the neuronal cell body as it attempts to repair the axon.

Question 9: A newborn has poor myelin formation in the CNS. Which embryological tissue are the affected cells derived from?

Answer: Neuroectoderm

Explanation: The neuroectoderm gives rise to CNS structures, including oligodendrocytes responsible for myelination.

Note: The neuroectoderm also forms CNS neurons and astrocytes.

Question 10: A child with morning headaches and nausea has a posterior fossa mass. The lateral and third ventricles are dilated, but the fourth is normal. Where is the obstruction?

Answer: Cerebral aqueduct

Explanation: Obstruction at the cerebral aqueduct leads to dilation of the third and lateral ventricles, causing hydrocephalus.

Note: Non-communicating hydrocephalus results from blockage within the ventricular system.

Question 11: A 65-year-old man is unresponsive after severe bleeding. Which brain region is most vulnerable to ischemic injury?

Answer: Hippocampus

Explanation: The hippocampus is highly susceptible to ischemia due to its high metabolic demand and role in memory.

Note: Other vulnerable areas include watershed zones in the brain.

Question 12: An 81-year-old woman is found with red neurons in the right MCA territory. How long ago did the injury occur?

Answer: 12–24 hours

Explanation: Red neurons, characterized by eosinophilic cytoplasm and pyknotic nuclei, appear 12-24 hours after ischemic injury.

Note: The timeline of ischemic injury progresses from red neurons to inflammation and eventually glial scar formation.

Question 13: A 60-year-old man has sudden right-sided weakness. MRI shows a small infarct in the internal capsule. What is the cause?

Answer: Hypertensive arteriolar sclerosis

Explanation: Chronic hypertension leads to lipohyalinosis and thickening of small arteries, causing lacunar infarcts.

Note: Lacunar strokes often result in pure motor or sensory deficits.

Question 14: A 60-year-old man presents with right arm weakness more than leg weakness. What is the likely cause?

Answer: Middle cerebral artery occlusion

Explanation: MCA occlusion typically causes contralateral weakness, affecting the upper limb more than the lower limb.

Note: Different artery occlusions present with varying patterns of limb weakness.

Question 15: A 55-year-old woman has a hemorrhage compressing the medial temporal lobe. Which cranial nerve is affected?

Answer: Oculomotor nerve

Explanation: Uncal herniation compresses the oculomotor nerve, leading to pupillary dilation and eye movement issues.

Note: Brain herniation can cause sudden neurological deficits and loss of consciousness.

NEUROLOGY

Question 16: A 60-year-old man experiences sudden right-sided weakness and confusion. His blood pressure is 190/100 mmHg, and a CT scan reveals an intracerebral hemorrhage. What is the most likely underlying cause?

Answer: Charcot-Bouchard microaneurysm rupture

Explanation: Charcot-Bouchard microaneurysms are associated with chronic hypertension and can lead to intracerebral hemorrhage, particularly in deep brain structures.

Note: These microaneurysms are distinct from saccular (berry) aneurysms, which typically cause subarachnoid hemorrhage.

Question 17: A 75-year-old man presents with sudden vision loss and right-sided sensory deficits. A CT scan shows multiple small hemorrhages in the occipital and parietal lobes. He had a frontal lobe hemorrhage two years ago and has no history of hypertension. What is the most likely cause?

Answer: Cerebral amyloid angiopathy

Explanation: Cerebral amyloid angiopathy involves β-amyloid deposition in cerebral vessels, leading to recurrent lobar hemorrhages in the elderly.

Note: This condition is independent of systemic amyloidosis, which involves AL-amyloid deposition in organs.

Question 18: A 68-year-old man presents with sudden dizziness, headache, and ataxia. A CT scan shows a hemorrhage in the cerebellar vermis. What neurologic finding is most likely observed?

Answer: Truncal ataxia

Explanation: The cerebellar vermis is responsible for axial coordination, and its injury leads to truncal ataxia, characterized by a wide-based gait.

Note: Damage to the cerebellar hemispheres affects limb coordination, causing limb ataxia and intention tremor.

Question 19: A 66-year-old man with atrial fibrillation wakes up with left lower limb weakness and a positive Babinski sign. Where is the lesion most likely located?

Answer: Right anterior cerebral artery territory

Explanation: An embolic stroke in the right anterior cerebral artery territory can cause contralateral leg weakness and sensory loss.

Note: Atrial fibrillation increases the risk of embolic strokes, which can present with sudden focal neurological deficits.

Question 20: A 61-year-old man with hypertension and a history of smoking experiences transient right arm weakness and aphasia. Symptoms resolve within an hour. What is the best medication for secondary prevention?

Answer: Aspirin and statin

Explanation: After a transient ischemic attack (TIA), antiplatelet therapy with aspirin and a statin is recommended to reduce the risk of future strokes.

Note: Management of TIA also includes controlling blood pressure, managing diabetes, and assessing carotid artery stenosis.

Question 21: A 66-year-old woman presents with sudden vertigo, right facial numbness, left extremities sensory loss, and decreased gag reflex. Which artery is involved?

Answer: Posterior inferior cerebellar artery (PICA)

Explanation: The "crossed signs" pattern, with right-sided cranial nerve involvement and left-sided sensory loss, indicates a lateral medullary lesion supplied by PICA.

Note: Brainstem ischemia can be localized using the rule of 4, which helps identify affected areas and their blood supply.

Question 22: An elderly man presents with acute weakness and diplopia. Examination reveals left ptosis and a dilated pupil, along with right hemiparesis. Which artery is involved?

Answer: Left posterior cerebral artery

Explanation: The combination of right-sided weakness and left-sided cranial nerve involvement suggests a "crossed signs" pattern, indicating a left medial midbrain lesion supplied by the left PCA.

Note: The rule of 4 helps localize brainstem lesions and identify the supplying artery.

Question 23: A 23-year-old man suffers head trauma, briefly loses consciousness, then regains alertness, but becomes unresponsive hours later. Where is the bleeding located?

Answer: Between the bone and dura mater

Explanation: The transient loss of consciousness followed by a lucid interval is characteristic of an epidural hematoma, where bleeding occurs between the skull and dura.

Note: Epidural hematomas often result from middle meningeal artery injury due to skull fracture.

Question 24: A 2-month-old infant presents with lethargy and a bulging anterior fontanelle. Fundoscopy reveals bilateral retinal hemorrhages. What is the most likely cause?

Answer: Shaken baby syndrome

Explanation: The combination of subdural hematomas, retinal hemorrhages, and rib fractures in an infant suggests shaken baby syndrome, a form of child abuse.

Note: Suspect non-accidental trauma in similar presentations.

Question 25: An elderly woman with altered mental status has a head CT showing a crescent-shaped, hyperdense lesion. What vessel injury is the most likely cause?

Answer: Cortical bridging veins

Explanation: Chronic subdural hemorrhage results from tearing of cortical bridging veins, often due to brain atrophy in the elderly.

Note: Subdural hemorrhages appear as crescent-shaped lesions on CT and can cross suture lines.

Question 26: A 27-year-old man involved in a high-speed car accident is in a coma. Brain histopathology shows widespread axonal swelling, especially at the gray-white matter junction. What is the underlying mechanism?

Answer: Shearing forces causing diffuse axonal injury

Explanation: Rapid acceleration-deceleration injuries disrupt white matter tracts, leading to diffuse axonal injury and often resulting in coma.

Note: This type of injury is common in severe traumatic brain injuries.

Question 27: A 32-year-old man with a subarachnoid hemorrhage develops new right-sided weakness five days later. What medication could have prevented this?

Answer: Calcium channel blocker (e.g., nimodipine)

Explanation: Calcium channel blockers prevent delayed cerebral vasospasm, a common complication after subarachnoid hemorrhage that can lead to ischemic deficits.

Note: Other complications of SAH include hydrocephalus and rebleeding.

Question 28: A premature infant becomes lethargic and hypotonic. Cranial ultrasound reveals blood in the lateral ventricles. What is the most likely source of bleeding?

Answer: Germinal matrix

Explanation: The germinal matrix is a highly vascular region in premature infants prone to hemorrhage due to fragile capillaries and poor blood flow regulation.

Note: Intraventricular hemorrhage is common in preterm infants and can lead to significant morbidity.

Question 29: A 75-year-old man with progressive memory loss and difficulty managing daily activities has a positive Babinski sign on the right side. What is the most likely diagnosis?

Answer: Vascular dementia

Explanation: Vascular dementia is characterized by cognitive decline with focal neurological deficits, often due to multiple infarcts.

Note: Stepwise cognitive decline and imaging showing multiple infarcts support the diagnosis.

Question 30: A 65-year-old woman presents with progressively slowing movements, muscle rigidity, and a resting tremor. Her facial expression is decreased, and her gait is shuffling. What is the most likely diagnosis?

Answer: Parkinson's Disease

Explanation: Parkinson's Disease is characterized by tremor, rigidity, akinesia, and postural instability (TRAP), due to loss of dopaminergic neurons in the substantia nigra.

Note: Histological findings include Lewy bodies, and gross pathology shows depigmentation of the substantia nigra.

NEUROLOGY

Question 31: A 54-year-old man has experienced behavioral changes over the past two years, including disinhibition, irritability, inappropriate joking, and poor insight. Which brain regions are most likely affected?

Answer: Temporal and frontal cortices

Explanation: These symptoms are indicative of frontotemporal dementia, which affects areas of the brain responsible for personality and social behavior.

Note: Frontotemporal dementia often presents with apathy, compulsive behaviors, and executive dysfunction.

Question 32: A 42-year-old woman exhibits choreiform movements and mood changes. Her family history includes a fatal neurodegenerative disorder. What is the likely diagnosis?

Answer: Huntington's disease

Explanation: The combination of chorea, aggression, depression, and dementia suggests Huntington's disease, caused by CAG trinucleotide repeat expansion on chromosome 4.

Note: Pathological findings include caudate nucleus atrophy and enlarged lateral ventricles, with neurotransmitter changes such as increased dopamine and decreased GABA and acetylcholine.

Question 33: An 80-year-old man presents with cognitive decline, vivid visual hallucinations, and recent tremor and bradykinesia. His cognitive symptoms began months before the motor symptoms. What is the most likely diagnosis?

Answer: Dementia with Lewy Bodies

Explanation: This condition is characterized by dementia, visual hallucinations, and early or concurrent parkinsonism within one year of cognitive decline.

Note: If parkinsonian symptoms precede dementia by more than a year, consider Parkinson's Disease Dementia.

Question 34: A 72-year-old woman has increasing forgetfulness and got lost while driving a year ago. What is the most likely pathological finding in her brain?

Answer: Neuritic plaques

Explanation: Neuritic plaques, composed of beta-amyloid protein, are characteristic of Alzheimer's disease, which is the most common cause of dementia.

Note: Alzheimer's disease is marked by progressive memory loss, brain atrophy, neurofibrillary tangles, amyloid angiopathy, and decreased acetylcholine.

Question 35: A 65-year-old woman with Parkinson's disease is treated with levodopa and carbidopa. She reports improved mobility and reduced nausea. What is the mechanism by which carbidopa enhances therapy?

Answer: Inhibits peripheral conversion of levodopa to dopamine

Explanation: Carbidopa inhibits peripheral DOPA decarboxylase, reducing peripheral side effects and increasing CNS availability of levodopa.

Note: Carbidopa does not cross the blood-brain barrier and thus has no central effects.

Question 36: A 70-year-old man with Parkinson's disease develops compulsive gambling and hypersexuality after starting a new medication. Which drug is the most likely cause?

Answer: Pramipexole

Explanation: Pramipexole, a dopamine agonist, is associated with impulse control disorders.

Note: Other Parkinson's medications include amantadine, entacapone, tolcapone, selegiline, rasagiline, benztropine, and trihexyphenidyl.

Question 37: A 72-year-old man becomes combative and confused since this morning. His wife notes mild memory issues over the past year. What best explains his behavior?

Answer: Delirium

Explanation: The acute onset of confusion and combativeness suggests delirium, an acute reversible confusional state.

Note: Delirium is common in older adults and can be triggered by infections, medications, electrolyte imbalances, or hospitalization.

Question 38: A 60-year-old woman experiences fatigue and drooping eyelids that worsen in the evening. Chest CT shows an anterior mediastinal mass. What is the most likely mechanism?

Answer: Antibodies against acetylcholine receptors

Explanation: Myasthenia gravis is characterized by muscle weakness that worsens with activity, due to autoantibodies against postsynaptic acetylcholine receptors.

Note: Myasthenia gravis is associated with thymus hyperplasia and thymoma, and symptoms improve with cholinesterase inhibitors.

Question 39: An elderly man presents with progressive weakness and absent knee reflexes. Symptoms improve after repeated exercise. What lung pathology is associated with this condition?

Answer: Small cell lung cancer

Explanation: Lambert-Eaton Myasthenic Syndrome, often associated with small cell lung cancer, is characterized by proximal muscle weakness and absent reflexes.

Note: It is caused by autoantibodies against presynaptic voltage-gated calcium channels, leading to decreased acetylcholine release.

Question 40: A 35-year-old man experiences progressive weakness starting in his feet and moving upward. Reflexes are absent at the knees. What is the most likely underlying pathology?

Answer: Endoneurial inflammatory infiltration

Explanation: Guillain-Barré Syndrome is an autoimmune condition causing endoneurial inflammatory infiltration and demyelination of peripheral nerves.

Note: It often follows infections like Campylobacter jejuni and presents with symmetrical ascending weakness and areflexia.

Question 41: A 22-year-old man has weakness and difficulty releasing his grip. Muscle biopsy shows atrophy of type 1 fibers. What is the most likely diagnosis?

Answer: Myotonic dystrophy

Explanation: Difficulty releasing grip is characteristic of myotonic dystrophy, which affects skeletal muscle chloride channels.

Note: Symptoms include frontal balding, cataracts, testicular atrophy, and arrhythmias, caused by CTG trinucleotide repeat expansion.

Question 42: An elderly woman with poorly controlled diabetes has numbness and tingling in her feet. What is the underlying cause of her neuropathy?

Answer: Endoneurial arteriolar hyalinization

Explanation: Diabetic neuropathy is caused by endoneurial arteriolar hyalinization due to chronic hyperglycemia.

Note: This leads to peripheral polyneuropathy, autonomic neuropathy, and motor neuropathy.

Question 43: A 13-year-old boy has worsening headaches and vision problems. Brain imaging reveals a suprasellar calcified cystic mass. What embryological structure is this mass most likely derived from?

Answer: Rathke's pouch

Explanation: Craniopharyngioma, derived from Rathke's pouch, presents as a suprasellar mass with cystic components and calcifications.

Note: It arises in children and differs from pituitary adenomas, which are solid and occur in adults.

Question 44: A 47-year-old woman with new-onset seizures has a brain mass attached to the dura. Biopsy reveals whorled cell clusters and calcified structures. What is the most likely diagnosis?

Answer: Meningioma

Explanation: Meningioma is an extra-axial tumor with whorled cell patterns and psammoma bodies.

Note: It arises from arachnoid cap cells and can cause seizures or headaches due to compression of adjacent structures.

Question 45: A 62-year-old man with a seizure has a brain mass in the right hemisphere crossing the midline. What is the most likely diagnosis?

Answer: Glioblastoma multiforme

Explanation: A mass crossing the midline, known as a butterfly glioma, is indicative of glioblastoma multiforme.

Note: It is the most common adult brain tumor, characterized by pseudopalisading necrosis and hemorrhage.

Question 46: An 11-month-old boy is irritable and hypotonic, with chaotic eye movements and a firm abdominal mass. Urine shows elevated catecholamine metabolites. What is the most likely diagnosis?

Answer: Neuroblastoma

Explanation: Neuroblastoma presents in infants with an abdominal mass, opsoclonus-myoclonus, and elevated HVA/VMA.

Note: It is a neural crest-derived tumor, and if the mass crosses the midline, it suggests neuroblastoma over Wilm's tumor.

Question 47: A 16-year-old boy with morning headaches and blurry vision has an intraventricular mass and hydrocephalus. What is the cell of origin for this tumor?

Answer: Ependymal cells

Explanation: Ependymoma arises from ependymal cells lining the ventricular system, causing obstructive hydrocephalus.

Note: It can spread via cerebrospinal fluid, leading to potential drop metastases in the spinal cord.

Question 48: A 36-year-old woman has sensorineural hearing loss, facial numbness, and an asymmetric smile. Where is the most likely location of the lesion?

Answer: Between the cerebellum and lateral pons (Cerebellopontine angle)

Explanation: Vestibular schwannoma arises at the cerebellopontine angle, compressing cranial nerves VIII, V, and VII.

Note: Bilateral vestibular schwannomas suggest Neurofibromatosis II.

HEADACHES AND FACIAL PAIN

Question 49: A 6-year-old boy experiences frequent episodes of staring spells during the day, each lasting a few seconds, with immediate recovery. What is the most appropriate treatment?

Answer: Ethosuximide

Explanation: The child's symptoms are indicative of absence seizures, characterized by brief staring spells without postictal confusion. Ethosuximide is the first-line treatment as it blocks T-type calcium channels.

Note: Absence seizures are confirmed by 3-Hz spike-and-wave discharges on EEG.

Question 50: A 4-year-old boy has a generalized tonic-clonic seizure during a fever. The seizure lasts 3 minutes, and he has no neurological deficits. What is the most appropriate next step?

Answer: Reassurance

Explanation: The child likely experienced a simple febrile seizure, common in children aged 6 months to 5 years. These seizures are typically benign and self-limiting, requiring only reassurance.

Note: Simple febrile seizures last less than 15 minutes, occur once in 24 hours, and have no focal neurological deficits.

Question 51: A 10-year-old boy is brought to the emergency department during a generalized tonic-clonic seizure. What is the first-line treatment?

Answer: Benzodiazepine

Explanation: The presentation suggests status epilepticus, defined as a seizure lasting 5 minutes or more. Benzodiazepines are the first-line abortive therapy.

Note: Status epilepticus requires immediate treatment to prevent long-term neurological damage.

Question 52: A 30-year-old man experiences severe, sharp headaches behind his left eye, lasting about 30 minutes, with left-sided ptosis and nasal congestion. What is the diagnosis?

Answer: Cluster headache

Explanation: The symptoms are characteristic of cluster headaches, which are unilateral and associated with autonomic symptoms like ptosis and nasal congestion.

Note: Cluster headaches are treated with 100% oxygen and can occur in clusters over weeks.

Question 53: A 30-year-old woman has daily dull, bilateral headaches that feel like a tight band around her head. What is the most likely diagnosis?

Answer: Tension headache

Explanation: Tension headaches are characterized by bilateral, non-throbbing pain often associated with stress and fatigue.

Note: Simple analgesics are typically effective for tension headaches.

Question 54: A 30-year-old woman experiences a sudden "hole" in her right visual field followed by a severe headache that resolves over 5 hours. What is the most likely diagnosis?

Answer: Migraine with aura

Explanation: The transient visual disturbance followed by a throbbing headache suggests a migraine with aura.

Note: Migraine treatment includes abortive medications like triptans and preventive options such as beta blockers.

Question 55: A 30-year-old woman experiences electric shock-like facial pain triggered by chewing. What is the best initial treatment?

Answer: Carbamazepine

Explanation: The brief, intense facial pain suggests trigeminal neuralgia, best treated initially with carbamazepine, a sodium channel blocker.

Note: Bilateral trigeminal neuralgia may indicate multiple sclerosis.

Question 56: A 34-year-old man has difficulty tolerating normal sounds in his right ear and facial asymmetry. Which cranial nerve is involved?

Answer: Facial nerve (CN VII)

Explanation: The symptoms indicate facial nerve dysfunction, affecting the entire ipsilateral face and causing hyperacusis.

Note: Bell's palsy is a common cause of facial nerve palsy.

CRANIAL NERVE DISORDERS

Question 57: A 55-year-old man reports double vision when walking downstairs. Which cranial nerve is most likely affected?

Answer: Trochlear nerve (CN IV)

Explanation: The trochlear nerve innervates the superior oblique muscle, and its dysfunction leads to vertical diplopia, especially when looking down.

Note: Patients may compensate by tilting their heads.

Question 58: A 58-year-old man with diabetes presents with sudden double vision, ptosis, and a "down and out" right eye. Pupils are normal. What is the cause?

Answer: CN III ischemia

Explanation: The presentation suggests diabetic mononeuropathy affecting CN III, sparing the pupil due to ischemia.

Note: Pupil involvement in CN III palsy suggests compression, often from an aneurysm.

CNS INFECTIONS

Question 59: A 23-year-old man with fever, confusion, and seizures has CSF showing normal glucose, elevated protein, and increased lymphocytes and erythrocytes. What is the diagnosis?

Answer: Herpes simplex virus (HSV) encephalitis

Explanation: The CSF findings and clinical presentation are typical of HSV encephalitis, often affecting the temporal lobes.

Note: MRI may show temporal lobe edema in HSV encephalitis.

Question 60: A 45-year-old man with fever, headache, and neck stiffness has CSF with high neutrophils, low glucose, and high protein. What organism is responsible?

Answer: Streptococcus pneumoniae

Explanation: The CSF profile is indicative of bacterial meningitis, with Streptococcus pneumoniae being the most common cause in adults.

Note: Prompt antibiotic treatment is crucial for bacterial meningitis.

Question 61: A 19-year-old college student with fever, headache, and a petechial rash lives in a dormitory. What organism is likely responsible?

Answer: Neisseria meningitidis

Explanation: The presentation is typical of meningococcal meningitis, common in close-contact settings like dormitories.

Note: Vaccination can prevent Neisseria meningitidis infections.

Question 62: A 74-year-old man undergoing chemotherapy presents with fever and neck stiffness after consuming soft cheese. What organism is likely responsible?

Answer: Listeria monocytogenes

Explanation: Listeria is a common cause of meningitis in the elderly and immunocompromised, often linked to unpasteurized dairy.

Note: Listeria meningitis requires specific antibiotic coverage, including ampicillin.

SPINAL CORD LESIONS

Question 63: A 44-year-old man with gait instability, positive Romberg sign, and absent leg reflexes. What is the diagnosis?

Answer: Tabes dorsalis

Explanation: The symptoms suggest demyelination of the dorsal columns and roots, characteristic of tabes dorsalis, a late manifestation of neurosyphilis.

Note: Diagnosis is confirmed with a reactive VDRL in CSF.

Question 64: A 65-year-old woman with recurrent falls and megaloblastic anemia. What is the cause of her neurological findings?

Answer: Subacute combined degeneration

Explanation: The combination of sensory ataxia and megaloblastic anemia suggests vitamin B12 deficiency, leading to subacute combined degeneration.

Note: Vitamin B12 deficiency affects both the dorsal columns and lateral corticospinal tracts.

Question 65: A 20-year-old woman with hand burns and loss of pain sensation in her upper limbs. What is the diagnosis?

Answer: Syringomyelia

Explanation: Syringomyelia involves central spinal cord cavitation, leading to bilateral loss of pain and temperature sensation and hand muscle atrophy.

Note: Syringomyelia is often associated with Chiari I malformation.

Question 66: A 60-year-old man with muscle weakness, hyperreflexia, and limb atrophy. What is the diagnosis?

Answer: Amyotrophic lateral sclerosis (ALS)

Explanation: The combination of upper and lower motor neuron signs without sensory involvement suggests ALS.

Note: ALS is a progressive neurodegenerative disease affecting motor neurons.

MOVEMENT DISORDERS, SLEEP & METABOLIC SYNDROMES

Question 67: A young man experiences excessive daytime sleepiness, hears voices before falling asleep, and has brief muscle weakness triggered by laughter. What is the most likely diagnosis?

Answer: Narcolepsy

Explanation: Narcolepsy is characterized by excessive daytime sleepiness, cataplexy (sudden muscle weakness triggered by emotions), and hallucinations during sleep-wake transitions. It is caused by the loss of hypocretin-producing neurons.

Note: Diagnosis is confirmed by shortened REM latency on sleep studies and low hypocretin levels.

Question 68: A 52-year-old woman experiences unpleasant sensations in her legs at night, relieved by movement. What is the appropriate treatment?

Answer: Iron supplementation and Gabapentin

Explanation: Restless legs syndrome is characterized by an urge to move the legs, worsened by inactivity and relieved by movement. It is associated with iron deficiency, chronic kidney disease, and diabetes.

Note: Treatment options include iron supplementation, Gabapentin, and dopamine agonists.

Question 69: A 22-year-old man presents with tremor, gait instability, and dysarthria. Laboratory tests reveal elevated liver enzymes. What is the next diagnostic step?

Answer: Slit lamp examination

Explanation: The combination of neuropsychiatric symptoms and elevated liver enzymes suggests Wilson disease. A slit lamp examination can reveal Kayser-Fleischer rings, indicative of copper accumulation.

Note: Wilson disease is caused by ATP7B mutations, leading to copper accumulation in the basal ganglia, liver, and cornea. It is confirmed by low ceruloplasmin and increased urinary copper.

Question 70: A 29-year-old woman has a coarse hand tremor that worsens as she reaches for objects, with no tremor at rest. Which brain structure is involved?

Answer: Cerebellum

Explanation: An intention tremor, which worsens as a patient reaches for objects, indicates cerebellar dysfunction.

Note: Intention tremors are characterized by zigzag pointing and abnormal finger-to-nose testing.

Question 71: An elderly diabetic man presents with severe right ear pain and purulent discharge. Manipulation of the ear causes severe pain, and there is tenderness behind the ear. What is the most likely diagnosis?

Answer: Malignant otitis externa

Explanation: Malignant otitis externa is a severe form of otitis externa that progresses to osteomyelitis of the skull base, commonly occurring in elderly diabetic patients.

Note: It is often caused by Pseudomonas and presents with otalgia worsened by manipulation, discharge, and pruritus.

Question 72: A 2-year-old boy has a fever and is tugging at his right ear. Otoscopy shows a red, bulging tympanic membrane. What is the most likely diagnosis?

Answer: Acute otitis media

Explanation: Acute otitis media is characterized by fever, otalgia, and an erythematous tympanic membrane. It is commonly caused by S. pneumoniae, H. influenzae, and M. catarrhalis.

Note: A common complication is mastoiditis, which can lead to postauricular tenderness and swelling.

Question 73: A man has difficulty hearing. The Weber test lateralizes to the right ear, and the Rinne test shows air conduction greater than bone conduction bilaterally. What is the most likely cause?

Answer: Left ear sensorineural hearing loss

Explanation: The Weber and Rinne tests help differentiate types of hearing loss. Sensorineural hearing loss is indicated by lateralization to the unaffected ear and air conduction greater than bone conduction.

Note: Common causes include noise-induced hearing loss and presbycusis.

OPHTHALMOLOGY & VISUAL PATHWAY DISORDERS

Question 74: A 43-year-old woman experiences dizziness lasting less than a minute when turning her head, without hearing loss or tinnitus. What is the most likely diagnosis?

Answer: Benign paroxysmal positional vertigo (BPPV)

Explanation: BPPV is characterized by brief episodes of vertigo triggered by head movements, without associated hearing loss or tinnitus. It is caused by dislodged calcium carbonate crystals in the semicircular canals.

Note: Nystagmus in BPPV is brief, mixed horizontal and torsional, provoked by positional changes, and suppressed with visual fixation.

Question 75: A 7-year-old boy presents with bilateral eye redness and intense itching, with a history of seasonal allergies. What is the most likely diagnosis?

Answer: Allergic conjunctivitis

Explanation: Allergic conjunctivitis is characterized by bilateral eye itching and redness, often associated with a history of allergies.

Note: Conjunctivitis types include allergic (itchy, bilateral discharge), bacterial (purulent discharge), and viral (watery discharge, swollen preauricular node).

Question 76: A 64-year-old woman experiences sudden-onset severe eye pain, blurry vision, and seeing halos around lights after moving to a dark room. Her right eye is red with a mid-dilated non-reactive pupil. What is the most likely diagnosis?

Answer: Acute angle-closure glaucoma

Explanation: Acute angle-closure glaucoma is a true emergency characterized by eye pain after moving into a dark room, with a mid-dilated non-reactive pupil.

Note: Treatment includes laser peripheral iridotomy and medications to decrease aqueous humor production and increase outflow.

Question 77: A 72-year-old man experiences gradual loss of central vision in both eyes. Fundoscopy shows drusen deposits under the retina. What is the most likely diagnosis?

Answer: Dry age-related macular degeneration

Explanation: Dry age-related macular degeneration is characterized by gradual central vision loss and drusen deposits on fundoscopy.

Note: Other fundoscopy findings include wet AMD (rapid vision loss, choroidal neovascularization) and diabetic retinopathy (microaneurysms, hemorrhages).

Question 78: A 68-year-old man with poorly controlled hypertension presents for a routine eye examination. Fundoscopy reveals flame-shaped hemorrhages, arteriovenous nicking, and cotton-wool spots. What is the most likely diagnosis?

Answer: Hypertensive retinopathy

Explanation: Hypertensive retinopathy is characterized by flame hemorrhages, AV nicking, and cotton-wool spots on fundoscopy.

Note: Other fundoscopy findings include retinal artery occlusion (painless vision loss, "cherry-red spot") and retinal vein occlusion (retinal hemorrhage, edema).

Question 79: A 3-year-old child presents with a white pupillary reflex in the left eye. What is the most likely underlying cause?

Answer: Retinoblastoma due to RB1 mutation

Explanation: A unilateral white reflex suggests retinoblastoma, which is caused by an RB1 gene mutation.

Note: Retinoblastoma is the most common intraocular tumor in children and presents with leukocoria and strabismus.

Question 80: A 22-year-old man with facial trauma has difficulty looking up with the affected eye. What is the most likely explanation?

Answer: Inferior rectus entrapment from orbital fracture

Explanation: Orbital floor fractures can lead to inferior rectus entrapment, causing impaired upward gaze.

Note: It can be associated with inferior orbital nerve injury, causing hypoesthesia of the cheek.

Question 81: A 55-year-old woman presents with bilateral galactorrhea and progressive difficulty seeing objects on the sides of her visual field. Visual field testing reveals bitemporal hemianopia. What is the most likely location of the lesion?

Answer: Optic chiasm

Explanation: Compression of the optic chiasm disrupts crossing nasal fibers, leading to loss of lateral visual fields in both eyes, known as bitemporal hemianopia.

Note: Optic chiasm compression is most commonly due to a pituitary adenoma, such as a prolactinoma.

NEUROLOGY

Question 82: A 29-year-old woman experiences double vision. When she looks to the left, her left eye moves outward with nystagmus, but her right eye does not move inward. Where is the lesion likely located?

Answer: Right medial longitudinal fasciculus

Explanation: A lesion in the medial longitudinal fasciculus (MLF) disrupts the coordination between the abducens (CN VI) and oculomotor (CN III) nuclei, leading to internuclear ophthalmoplegia. This results in the failure of the ipsilateral eye to adduct and nystagmus in the contralateral abducting eye.

Note: Internuclear ophthalmoplegia is often caused by multiple sclerosis in young women and by stroke in older individuals.

VISUAL FIELD DEFECTS

Note: Regular review of these high-yield notes can enhance retention and understanding of key concepts for Step 1.
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
    print("Extracting questions from neurology content...")
    questions = extract_questions(NEUROLOGY_CONTENT)
    
    print(f"Found {len(questions)} questions")
    
    # Create output directory
    output_dir = Path("neurology_images")
    output_dir.mkdir(exist_ok=True)
    
    # Create a log file
    log_file = output_dir / "download_log.txt"
    
    downloaded_count = 0
    failed_count = 0
    
    print(f"Starting download process for {len(questions)} questions...")
    print(f"Output directory: {output_dir.absolute()}\n")
    
    with open(log_file, 'w', encoding='utf-8') as log:
        log.write("Neurology Question Image Download Log\n")
        log.write("=" * 50 + "\n\n")
        
        for idx, q in enumerate(questions, 1):
            q_num = q['number']
            topic = q['topic']
            
            print(f"\n[{idx}/{len(questions)}] Processing Question {q_num}: {topic}")
            log.write(f"Question {q_num}: {topic}\n")
            log.write(f"  Question: {q['question'][:100]}...\n")
            log.write(f"  Answer: {q['answer'][:100]}...\n")
            
            # Search for images
            search_results = search_wikimedia_commons(topic, limit=10)
            
            if not search_results:
                # Try alternative search terms
                alt_terms = [
                    topic.replace(' ', '_'),
                    topic.lower(),
                    q['answer'].split()[0] if q['answer'] else topic
                ]
                for alt_term in alt_terms:
                    search_results = search_wikimedia_commons(alt_term, limit=10)
                    if search_results:
                        break
            
            # Try to find a CC-licensed image
            image_found = False
            
            # Process Wikimedia Commons results if we have them - download 2 options per question
            images_downloaded = 0
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
    print(f"Successfully downloaded: {downloaded_count}/{len(questions)}")
    print(f"Failed: {failed_count}/{len(questions)}")
    print(f"\nImages saved to: {output_dir.absolute()}")
    print(f"Log file: {log_file.absolute()}")


if __name__ == "__main__":
    main()

