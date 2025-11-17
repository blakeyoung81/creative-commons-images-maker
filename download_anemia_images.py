#!/usr/bin/env python3
"""
Script to download Creative Commons licensed images for anemia/hematology medical education questions.
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

# Anemia/Hematology content with all questions
ANEMIA_CONTENT = """IvyTutoring

*Be sure to watch the recorded session along with this document to make sure you get the full explanations. Attributions are found at the bottom of the document. 

IvyTutoring

ANEMIA

Question 1: A 35-year-old man reports dark, cola-colored urine each morning for the past several weeks. He notes increasing fatigue and has a history of unexplained deep vein thrombosis in the hepatic veins (Budd–Chiari syndrome). Physical exam reveals pallor and mild jaundice.

Answer: Paroxysmal nocturnal hemoglobinuria (PNH)

Explanation: PNH results from an acquired PIGA gene mutation in hematopoietic stem cells. This gene is required for synthesis of GPI anchors that attach complement-regulatory proteins (CD55 and CD59) to red cell membranes. Without these proteins, red cells become vulnerable to complement-mediated lysis, particularly at night when mild respiratory acidosis enhances complement activation. Chronic intravascular hemolysis leads to hemoglobinuria and hemosiderinuria, and free hemoglobin scavenges nitric oxide, promoting smooth muscle spasm and thrombosis—especially in hepatic, portal, or cerebral veins.

Note: Eculizumab, a monoclonal antibody against complement C5, prevents further complement-mediated destruction.

Question 2: A 26-year-old pregnant woman presents for evaluation of persistent fatigue. CBC shows a hemoglobin of 10.2 g/dL, MCV of 68 fL, ferritin within the normal range, and no improvement after several weeks of oral iron therapy.

Answer: Hemoglobin electrophoresis

Explanation: Microcytic anemia with normal ferritin and no response to iron therapy suggests thalassemia, a defect in globin chain synthesis. Iron studies are normal because iron metabolism is intact. The next diagnostic step is hemoglobin electrophoresis, which can distinguish between β-thalassemia (↑HbA₂, ±↑HbF) and α-thalassemia (normal electrophoresis in silent/minor forms). Microcytosis occurs due to extra cell divisions in erythroid precursors trying to normalize MCHC despite defective hemoglobin formation.

Note: Thalassemia severity depends on the number of affected globin genes; β⁰ mutations abolish β-globin synthesis entirely.

Question 3: A 29-year-old vegan presents with progressive numbness in her fingertips and gait instability. Labs reveal macrocytic anemia and elevated methylmalonic acid and homocysteine levels.

Answer: Vitamin B12 deficiency

Explanation: Vitamin B12 (cobalamin) deficiency causes impaired DNA synthesis and abnormal myelin formation. It is required to convert methylmalonyl-CoA → succinyl-CoA and homocysteine → methionine. Elevated methylmalonic acid disrupts myelin, producing paresthesias and posterior column demyelination. B12 is found only in animal products; thus strict vegans are susceptible. Other causes include pernicious anemia (autoimmune loss of intrinsic factor), ileal disease, or tapeworm infection.

Note: Neurologic findings distinguish B12 deficiency from folate deficiency, which lacks methylmalonic acid elevation.

Question 4: A fetus is stillborn at 32 weeks' gestation with severe generalized edema, ascites, and placentomegaly. Hemoglobin electrophoresis shows only Hb Barts (γ₄).

Answer: Alpha thalassemia major (hydrops fetalis)

Explanation: Deletion of all four α-globin genes (—/— —/—) results in absence of α chains, forcing γ chains to form tetramers (Hb Barts) with extremely high oxygen affinity. This prevents oxygen delivery to tissues, causing severe hypoxia, high-output cardiac failure, and hydrops fetalis. α-globin gene deletions are more common in Southeast Asian populations due to cis deletions.

Note: Hydrops fetalis is uniformly fatal without in utero transfusion.

Question 5: A 42-year-old man receiving isoniazid therapy for latent tuberculosis develops fatigue and pallor. CBC reveals microcytic anemia, and bone marrow examination shows ringed sideroblasts.

Answer: Vitamin B6 (pyridoxine) supplementation

Explanation: Isoniazid inhibits pyridoxine phosphokinase, decreasing active vitamin B6, a cofactor for δ-aminolevulinic acid (ALA) synthase—the rate-limiting enzyme in heme synthesis. This leads to defective protoporphyrin formation and iron accumulation in mitochondria (ringed sideroblasts). Despite high serum iron and ferritin, functional hemoglobin synthesis is impaired.

Note: Sideroblastic anemia may also result from alcohol, lead toxicity, or myelodysplastic syndromes.

Question 6: A 28-year-old woman presents with fatigue and pica (craving ice). Labs show: Hb 9.5 g/dL [12–16], MCV 72 fL [80–100], ferritin 8 ng/mL [15–150], and elevated total iron-binding capacity (TIBC).

Answer: Iron deficiency anemia

Explanation: Low ferritin and high TIBC reflect depleted iron stores and increased transferrin production by the liver. Iron deficiency causes defective heme synthesis, producing microcytosis and hypochromia. Early symptoms include fatigue, pallor, and sometimes pica. Common causes: menstrual blood loss, poor diet, or occult GI bleeding (colon cancer in older adults). Chronic deficiency leads to spoon nails (koilonychia) and glossitis.

Note: Treat with oral iron and identify source of loss before replacement.

Question 7: A 4-year-old boy presents with pallor, growth delay, and characteristic facial changes including frontal bossing and maxillary overgrowth. He has massive hepatosplenomegaly. Hemoglobin electrophoresis reveals elevated HbA₂ and HbF with absent HbA.

Answer: Increased HbF and HbA₂, absence of HbA

Explanation: These findings are diagnostic for β-thalassemia major, caused by mutations leading to absent β-globin synthesis. Without β chains, fetal γ chains persist (↑HbF) and δ chains increase (↑HbA₂). The imbalance causes ineffective erythropoiesis and extramedullary hematopoiesis, explaining bone deformities and hepatosplenomegaly. Repeated transfusions are required but cause secondary hemosiderosis (iron overload).

Note: Iron chelation is necessary in long-term transfusion therapy.

Question 8: A 34-year-old woman with systemic lupus erythematosus presents with progressive fatigue and dark urine. Labs show hemoglobin 8.5 g/dL and a positive direct Coombs test.

Answer: Warm autoimmune hemolytic anemia

Explanation: Warm AIHA involves IgG antibodies that bind red cells at body temperature. These opsonized cells are cleared by splenic macrophages, causing extravascular hemolysis. It often occurs secondary to autoimmune diseases like SLE or CLL and certain drugs. Peripheral smear may show spherocytes from partial phagocytosis.

Note: First-line therapy is corticosteroids; refractory cases may require rituximab or splenectomy.

Question 9: A 58-year-old man with long-standing rheumatoid arthritis presents with fatigue. Labs show normocytic anemia, elevated ferritin, and low total iron-binding capacity.

Answer: Treat the underlying disease

Explanation: Anemia of chronic disease (ACD) is mediated by chronic inflammation increasing hepcidin production from the liver. Hepcidin degrades ferroportin, trapping iron in macrophages and enterocytes, and inhibiting erythropoietin production. The result is impaired iron utilization despite normal stores. Correction requires control of the underlying inflammatory condition.

Note: Ferritin is high because iron is sequestered intracellularly; serum iron and TIBC are both low.

Question 10: A 30-year-old man develops sudden fatigue, jaundice, and dark urine after taking trimethoprim-sulfamethoxazole for a urinary tract infection. His peripheral smear shows bite cells and Heinz bodies.

Answer: Glucose-6-phosphate dehydrogenase (G6PD) deficiency

Explanation: G6PD deficiency is an X-linked disorder causing impaired regeneration of NADPH in the pentose phosphate pathway. Without NADPH, glutathione cannot neutralize oxidative stress from drugs (sulfa drugs, antimalarials), infections, or fava beans. Oxidized hemoglobin forms Heinz bodies that are removed by splenic macrophages, producing bite cells and intravascular hemolysis.

Note: Avoid known oxidant triggers to prevent recurrence.

Question 11: A 60-year-old woman presents with fatigue, paresthesias, and glossitis. Labs reveal macrocytosis and elevated methylmalonic acid. Anti–intrinsic factor antibodies are positive.

Answer: Autoimmune destruction of gastric parietal cells

Explanation: Pernicious anemia is an autoimmune gastritis in which antibodies target intrinsic factor or parietal cells, leading to loss of intrinsic factor and subsequent vitamin B12 malabsorption. This causes megaloblastic anemia with neurologic symptoms due to demyelination of the posterior and lateral spinal columns. The chronic atrophic gastritis also predisposes to gastric adenocarcinoma.

Note: Lifelong parenteral vitamin B12 replacement is required.

Question 12: A 45-year-old woman with rheumatoid arthritis treated with methotrexate presents with fatigue. Labs show macrocytic anemia and elevated homocysteine but normal methylmalonic acid.

Answer: Folate deficiency

Explanation: Methotrexate inhibits dihydrofolate reductase, preventing the conversion of dihydrofolate to tetrahydrofolate, an essential cofactor for thymidine synthesis. This blocks DNA synthesis and causes megaloblastic anemia. Because methylmalonic acid remains normal, this distinguishes folate deficiency from B12 deficiency.

Note: Folic acid supplementation prevents this adverse effect during methotrexate therapy.

Question 13: A 7-year-old boy presents with pallor, recurrent infections, and skeletal anomalies including absent thumbs and short stature. CBC shows pancytopenia.

Answer: Stem cell transplant

Explanation: Fanconi anemia is an autosomal recessive disorder of DNA repair, leading to bone marrow failure, aplastic anemia, and congenital malformations (thumb/radial defects, short stature, café-au-lait spots). There is increased risk of AML and squamous cell carcinoma. Bone marrow transplantation is curative for the hematologic component.

Note: Cells show increased chromosomal breakage after DNA cross-linking agents.

Question 14: A 22-year-old man presents with jaundice and splenomegaly. Labs reveal mild anemia and elevated MCHC. Peripheral smear shows small, dense red cells without central pallor.

Answer: Pigmented gallstones

Explanation: Hereditary spherocytosis is caused by defects in membrane proteins such as spectrin or ankyrin, leading to loss of membrane surface area and formation of spherocytes. These are trapped and destroyed in the spleen (extravascular hemolysis), causing hyperbilirubinemia and increased risk of pigmented gallstones. Splenectomy prevents further hemolysis.

Note: The osmotic fragility test confirms diagnosis.

Question 15: A 50-year-old man with chronic alcoholism presents with fatigue and glossitis. CBC shows macrocytic anemia with elevated homocysteine but normal methylmalonic acid.

Answer: Folate supplementation

Explanation: Alcohol interferes with folate absorption in the jejunum and impairs hepatic folate storage. Folate deficiency causes defective thymidine synthesis and megaloblastic anemia. Elevated homocysteine reflects impaired methylation pathways, but methylmalonic acid remains normal, distinguishing it from B12 deficiency.

Note: Chronic alcoholism often causes concurrent nutritional and liver-related anemias.

Question 16: A 5-year-old boy with known sickle cell disease presents with sudden left upper quadrant pain, pallor, and lethargy. Exam shows a rapidly enlarging spleen. Labs reveal severe anemia with elevated reticulocyte count.

Answer: Splenic sequestration crisis

Explanation: In sickle cell disease, repeated vaso-occlusion can trap large volumes of blood in the spleen, causing hypovolemic shock and acute anemia. Reticulocyte count rises as bone marrow responds. This differs from aplastic crisis (usually due to parvovirus B19), which features absent reticulocytes and no splenomegaly.

Note: Chronic infarction eventually leads to autosplenectomy by adolescence.

Question 17: A 9-month-old boy is brought to the clinic for evaluation of persistent pallor and jaundice. His parents report that he tires easily during feeding and has had several episodes of scleral icterus since infancy. There is no history of infection or medication exposure. Physical exam reveals mild hepatosplenomegaly. Laboratory studies show hemoglobin 8.2 g/dL, elevated indirect bilirubin, increased lactate dehydrogenase, and a markedly elevated reticulocyte count. Peripheral smear shows echinocytes (burr cells). 2,3-bisphosphoglycerate (2,3-BPG) levels are elevated.

Answer: Pyruvate kinase deficiency

Explanation: Pyruvate kinase deficiency is an autosomal recessive defect in glycolysis that prevents conversion of phosphoenolpyruvate to pyruvate, blocking ATP generation in erythrocytes. Red blood cells rely entirely on glycolysis for energy; without sufficient ATP, Na⁺/K⁺ pumps fail, membranes become rigid, and cells undergo extravascular hemolysis in the spleen. The chronic hemolysis causes indirect hyperbilirubinemia, jaundice, and splenomegaly. Elevated 2,3-BPG shifts the hemoglobin–oxygen dissociation curve to the right, facilitating oxygen unloading to tissues but worsening anemia.

Note: Management is mainly supportive with transfusions as needed; splenectomy may reduce hemolysis in severe cases.

Question 18: A 3-year-old child presents with developmental delay, constipation, and abdominal pain. CBC shows microcytic anemia. Peripheral smear reveals coarse basophilic stippling of erythrocytes.

Answer: Basophilic stippling

Explanation: Lead poisoning inhibits ferrochelatase and ALA dehydratase, blocking heme synthesis. It also inhibits ribonuclease, leading to retention of ribosomal RNA—seen as basophilic stippling. Children are at risk due to ingestion of lead-based paint or contaminated dust. Neurologic and gastrointestinal symptoms are common.

Note: Treat with chelation (succimer or EDTA) if blood lead levels are significantly elevated.

SICKLE CELL DISEASE

Question 19: A 10-year-old boy with known sickle cell disease presents with high fever, chills, and lethargy. His parents report he has had several previous episodes of pneumonia. On exam, he is tachycardic and febrile. Blood smear shows sickled red cells and Howell-Jolly bodies. Laboratory studies reveal leukocytosis.

Answer: Vaccination and prophylactic antibiotics

Explanation: Howell-Jolly bodies indicate functional asplenia, which occurs after repeated splenic infarctions ("autosplenectomy") in sickle cell disease. The absence of splenic clearance predisposes to sepsis from encapsulated bacteria (Streptococcus pneumoniae, Haemophilus influenzae type b, Neisseria meningitidis). Patients require immunization against these organisms and daily prophylactic penicillin during childhood to prevent overwhelming sepsis.

Note: Lifelong vigilance for fever is essential—empiric broad-spectrum antibiotics are started immediately.

Question 20: A 7-year-old boy with homozygous sickle cell disease presents with sudden onset of pleuritic chest pain, fever, and shortness of breath. Pulse oximetry shows 88% on room air. Chest X-ray reveals a new infiltrate in the right lower lobe. CBC shows leukocytosis and anemia compared with baseline.

Answer: Acute chest syndrome

Explanation: Acute chest syndrome is a life-threatening complication defined by fever, respiratory symptoms, and a new pulmonary infiltrate. Triggers include infection (commonly Mycoplasma pneumoniae), fat emboli from bone infarction, or pulmonary vaso-occlusion. Sickled erythrocytes obstruct pulmonary vessels, causing inflammation and hypoxemia that further promotes sickling.

Note: Treatment includes oxygen, broad-spectrum antibiotics, pain control, and simple or exchange transfusion to reduce HbS concentration.

Question 21: A 22-year-old college athlete with sickle cell trait presents with intermittent painless gross hematuria after intense exercise. Physical exam is unremarkable. Urinalysis reveals numerous red blood cells but no casts or proteinuria. Serum creatinine is normal.

Answer: Renal papillary necrosis

Explanation: In sickle cell trait, mild hypoxia and hypertonicity of the renal medulla promote limited sickling, leading to ischemic necrosis of renal papillae. This causes painless hematuria, often exercise-induced, without renal insufficiency. In contrast, full sickle cell disease may lead to chronic kidney disease from repeated vaso-occlusion.

Note: Management is supportive; ensure hydration and avoid hypoxic conditions.

Question 22: An 8-year-old boy with sickle cell disease suddenly develops right-sided weakness and slurred speech. CT of the head shows no hemorrhage. His prior history includes multiple vaso-occlusive pain crises but no regular preventive therapy.

Answer: Hydroxyurea or chronic transfusion therapy

Explanation: Sickle cell patients are prone to ischemic stroke due to vaso-occlusion of cerebral vessels. Preventive therapy with hydroxyurea increases fetal hemoglobin (HbF), which inhibits HbS polymerization, reduces vaso-occlusive crises, and lowers stroke risk. Alternatively, chronic exchange transfusions maintain HbS < 30%.

Note: Early institution of hydroxyurea also decreases dactylitis, acute chest episodes, and overall mortality.

HEMOLYTIC DISEASE OF THE NEWBORN

Question 23: A 1-day-old newborn born to a 26-year-old type O⁺ mother develops jaundice within 12 hours of birth. The pregnancy was uncomplicated. The infant's blood type is A⁺. Physical exam reveals mild scleral icterus but no hepatosplenomegaly. Laboratory studies show indirect hyperbilirubinemia, mild anemia, and a positive direct Coombs test.

Answer: ABO incompatibility

Explanation: ABO incompatibility occurs when a type O mother produces anti-A or anti-B IgG antibodies that cross the placenta and hemolyze fetal red cells. It can affect the first pregnancy because anti-A and anti-B antibodies are preformed. Hemolysis causes early-onset jaundice and mild anemia.

Note: Treatment is with phototherapy; severe cases may require exchange transfusion.

Question 24: A 2-day-old newborn develops severe jaundice and pallor within 24 hours of birth. The mother is Rh-negative, and the father is Rh-positive. The pregnancy history reveals no prophylactic treatment during gestation. The infant's total bilirubin is 22 mg/dL, and the direct Coombs test is strongly positive.

Answer: Rh incompatibility

Explanation: Rh hemolytic disease results when an Rh-negative mother is sensitized to Rh antigen from a previous pregnancy and produces anti-D IgG antibodies. These cross the placenta in subsequent pregnancies, causing hemolysis, severe anemia, hydrops fetalis, and kernicterus in the fetus or newborn.

Note: Prevention requires administration of Rho(D) immune globulin (Rhogam) to the mother at 28 weeks and within 72 hours postpartum.

PORPHYRIA AND BLEEDING DISORDERS

Question 25: A 45-year-old man presents with fragile blisters on the backs of his hands and forearms that worsen with sun exposure. He has hyperpigmentation and mild facial hypertrichosis. Past history is significant for chronic hepatitis C and heavy alcohol use. Urinalysis shows elevated uroporphyrins.

Answer: Porphyria cutanea tarda (PCT)

Explanation: PCT is the most common porphyria, caused by uroporphyrinogen decarboxylase deficiency. Accumulated uroporphyrins react with light, producing photosensitivity and blistering on sun-exposed skin. It is strongly associated with hepatitis C, alcohol use, and iron overload.

Note: Management includes phlebotomy, sun protection, and low-dose hydroxychloroquine.

Question 26: A 32-year-old woman presents with easy bruising, petechiae, and prolonged menstrual bleeding. She recently recovered from an upper respiratory infection. Physical exam shows scattered ecchymoses. CBC shows platelet count 50,000/µL [normal 150,000–400,000] with normal PT and PTT.

Answer: Immune thrombocytopenic purpura (ITP)

Explanation: ITP is an autoimmune destruction of platelets by IgG antibodies targeting platelet membrane antigens. It often follows viral infection and is more common in women. Bone marrow biopsy shows increased megakaryocytes reflecting compensatory platelet production.

Note: First-line therapy is corticosteroids; IVIG for severe bleeding; splenectomy for chronic or refractory disease.

Question 27: A 30-year-old woman presents with severe, colicky abdominal pain and dark red urine after fasting and starting a new oral contraceptive. She reports anxiety and tingling in her fingers but no photosensitivity. Urinalysis darkens on standing.

Answer: Acute intermittent porphyria (AIP)

Explanation: AIP is caused by a deficiency of porphobilinogen deaminase, leading to accumulation of ALA and porphobilinogen, which are neurotoxic. Attacks are precipitated by factors that upregulate ALA synthase (fasting, drugs, stress, hormones). Classic triad: abdominal pain, neurologic dysfunction, and red/brown urine that darkens on exposure to air.

Note: Treat with glucose and hemin to inhibit ALA synthase and reduce precursor buildup.

COAGULATION AND BLEEDING DISORDERS

Question 28: A 5-year-old boy is brought to the clinic for evaluation of recurrent nosebleeds and easy bruising since infancy. Physical exam reveals multiple ecchymoses on the lower limbs. Laboratory studies show normal platelet count, prolonged bleeding time, and absence of platelet agglutination with ristocetin. Peripheral smear demonstrates giant platelets.

Answer: Bernard–Soulier syndrome

Explanation: Bernard–Soulier syndrome is an autosomal recessive defect in the GPIb platelet receptor, which binds von Willebrand factor to mediate platelet adhesion to subendothelial collagen. Defective adhesion leads to mucocutaneous bleeding despite normal platelet numbers. The platelets are large and functionally abnormal.

Note: The ristocetin test remains abnormal even when normal plasma is added, distinguishing it from vWF disease.

Question 29: A 5-day-old male, born at home without medical supervision, presents with bleeding from the umbilical stump and oozing from heel-stick sites. Physical exam shows pallor and mild bruising. Laboratory tests reveal prolonged PT and PTT with normal platelet count.

Answer: Vitamin K

Explanation: Newborns lack intestinal flora that synthesize vitamin K, required for γ-carboxylation of clotting factors II, VII, IX, and X as well as proteins C and S. This results in vitamin K deficiency bleeding, presenting with mucosal or umbilical bleeding within the first week of life.

Note: Routine intramuscular vitamin K prophylaxis at birth prevents this condition.

Question 30: A 22-year-old woman presents with recurrent nosebleeds, heavy menstrual bleeding, and prolonged bleeding after dental extractions. Labs show prolonged bleeding time and PTT with normal PT and platelet count. Ristocetin-induced aggregation is abnormal but corrects when normal plasma is added.

Answer: Desmopressin

Explanation: Von Willebrand disease results from quantitative or qualitative deficiency of vWF, impairing platelet adhesion and reducing factor VIII stability. This causes both primary hemostatic (platelet) and secondary hemostatic (coagulation) defects. Desmopressin (DDAVP) releases vWF and factor VIII from endothelial storage sites, improving hemostasis.

Note: Avoid NSAIDs, which worsen bleeding by further impairing platelet function.

Question 31: A 60-year-old man with stage 5 chronic kidney disease presents with frequent gum bleeding and prolonged bleeding after minor cuts. CBC shows normal platelet count, and coagulation studies (PT/PTT) are within normal limits. Bleeding time is prolonged.

Answer: Uremic platelet dysfunction

Explanation: In uremic platelet dysfunction, accumulation of nitrogenous waste products inhibits platelet aggregation and adhesion to the vessel wall. Although platelet numbers are normal, function is impaired, leading to mucosal bleeding and easy bruising.

Note: Desmopressin can transiently improve platelet function by releasing vWF and factor VIII.

Question 32: A 10-year-old boy presents with swelling and pain in his right knee after a minor fall. He has a history of prolonged bleeding after circumcision. His uncle had a similar condition. Labs show prolonged PTT with normal PT and platelet count.

Answer: Hemophilia A or B

Explanation: Hemophilia A (factor VIII deficiency) and Hemophilia B (factor IX deficiency) are X-linked recessive disorders causing defective intrinsic pathway activation, leading to prolonged PTT with normal PT. Recurrent hemarthroses, deep muscle hematomas, and delayed bleeding after trauma are characteristic.

Note: Treatment involves factor replacement; desmopressin is useful only in Hemophilia A.

DISSEMINATED INTRAVASCULAR COAGULATION (DIC)

Question 33: A 32-year-old woman develops acute shortness of breath, hypotension, and diffuse oozing from IV and surgical sites hours after delivery complicated by retained placental fragments. She has petechiae and cyanosis. Labs show elevated PT, PTT, and bleeding time, elevated D-dimer, and decreased fibrinogen and platelets.

Answer: Increased PT/PTT/BT/D-dimer, decreased fibrinogen and platelets

Explanation: Disseminated intravascular coagulation (DIC) in the postpartum period often results from amniotic fluid embolism, which activates tissue factor and the coagulation cascade. Widespread microthrombi consume platelets and clotting factors, leading to bleeding, hypoxia, and end-organ damage.

Note: Management includes supportive care, replacement of blood products, and treating the underlying cause.

Question 34: A 58-year-old man hospitalized for septic shock from Neisseria meningitidis develops oozing from venipuncture sites and hematuria. Exam shows petechiae and ecchymoses. Labs reveal thrombocytopenia, prolonged PT and PTT, elevated D-dimer, and low fibrinogen. Peripheral smear shows schistocytes.

Answer: Disseminated intravascular coagulation (DIC)

Explanation: Sepsis-associated DIC results from bacterial endotoxins inducing cytokine release and tissue factor activation. The uncontrolled coagulation leads to microvascular thrombi and consumption of platelets and factors, followed by secondary fibrinolysis and hemorrhage. Schistocytes form due to mechanical RBC destruction in fibrin strands.

Note: Treat the underlying infection, support circulation, and replace coagulation factors with fresh frozen plasma and cryoprecipitate as needed.

THROMBOPHILIA AND ANTICOAGULATION

Question 35: A 36-year-old woman presents with swelling and pain in her left leg. Doppler ultrasound confirms a deep vein thrombosis (DVT). She reports a prior episode of pulmonary embolism 2 years ago and no history of prolonged immobilization or malignancy. Her father also had a DVT in his 40s. Laboratory coagulation studies show normal PT and PTT.

Answer: Factor V Leiden mutation

Explanation: Factor V Leiden is a point mutation in the factor V gene that makes the protein resistant to inactivation by activated protein C, leading to a hypercoagulable state. It is the most common inherited thrombophilia and predisposes to venous thromboembolism (DVT and PE). Arterial thrombosis is rare.

Note: Diagnosis is by PCR for the factor V Leiden mutation. PT and PTT remain normal because the overall levels of coagulation factors are unaffected.

Question 36: A 45-year-old man with long-standing nephrotic syndrome presents with sudden onset of left flank pain and hematuria. Imaging reveals renal vein thrombosis. Labs show hypoalbuminemia, hyperlipidemia, and significant proteinuria.

Answer: Antithrombin III deficiency

Explanation: Antithrombin III normally inhibits thrombin and factor Xa. In nephrotic syndrome, urinary loss of antithrombin III leads to decreased anticoagulant activity and a hypercoagulable state. Patients are at risk for renal vein thrombosis, DVT, and pulmonary embolism.

Note: Because heparin acts by enhancing antithrombin activity, it may be less effective; direct thrombin inhibitors (e.g., argatroban) are preferred.

Question 37: A 30-year-old woman with systemic lupus erythematosus presents with swelling of her right leg and dyspnea. She has a history of two first-trimester miscarriages. Laboratory evaluation reveals prolonged PTT that fails to correct on a mixing study. Anticardiolipin antibodies are positive.

Answer: Antiphospholipid syndrome

Explanation:

Antiphospholipid syndrome involves autoantibodies (lupus anticoagulant, anticardiolipin, anti–β₂ glycoprotein I) that cause arterial and venous thrombosis and recurrent pregnancy loss. Despite a prolonged PTT, patients are hypercoagulable because the antibodies interfere with phospholipid-dependent coagulation assays.

Note: Lifelong anticoagulation is required; this condition can occur with or without underlying SLE.

HEPARIN AND WARFARIN MANAGEMENT

Question 38: A 62-year-old man treated with unfractionated heparin for DVT develops a 50% drop in platelet count five days after therapy initiation. He develops new right leg pain and pallor. Duplex ultrasound shows new arterial thrombosis.

Answer: Heparin-induced thrombocytopenia (HIT)

Explanation: HIT type II is a IgG-mediated hypersensitivity reaction against the heparin–platelet factor 4 complex. The immune complex activates platelets, causing thrombocytopenia and a paradoxical prothrombotic state.

Note: Stop all heparin immediately and start a direct thrombin inhibitor (argatroban or bivalirudin). Platelet transfusions are contraindicated.

Question 39: A 58-year-old man with atrial fibrillation is started on rivaroxaban for stroke prevention. He asks about its advantages compared with warfarin.

Answer: Factor Xa inhibitor

Explanation: Rivaroxaban directly inhibits factor Xa, blocking the conversion of prothrombin to thrombin. It provides predictable anticoagulation with no need for INR monitoring, fewer food and drug interactions, and oral dosing convenience.

Note: Major bleeding can be reversed with andexanet alfa, a specific antidote for factor Xa inhibitors.

Question 40: A 54-year-old woman with atrial fibrillation starts warfarin therapy and develops painful, red necrotic lesions on her thighs within four days. Laboratory tests reveal decreased protein C levels.

Answer: Bridging with heparin

Explanation: Warfarin inhibits synthesis of vitamin K–dependent factors (II, VII, IX, X) and proteins C and S. Because protein C has a short half-life, initial therapy causes a transient hypercoagulable state, predisposing to skin necrosis and thrombosis in microvasculature.

Note: Bridging with heparin during warfarin initiation provides immediate anticoagulation until INR is therapeutic and protein C levels stabilize.

Question 41: A hospitalized patient on intravenous heparin for pulmonary embolism undergoes daily coagulation monitoring. The laboratory test used is the partial thromboplastin time (PTT). Two days later, he accidentally receives an excessive heparin dose.

Answer: Monitor with PTT; reverse with protamine sulfate

Explanation: Heparin enhances antithrombin III, inhibiting thrombin (factor IIa) and factor Xa. The degree of anticoagulation is monitored with PTT. Overanticoagulation leads to bleeding and is reversed by protamine sulfate, a positively charged molecule that binds and neutralizes heparin.

Note: Heparin does not cross the placenta and is safe for use during pregnancy.

Question 42: A 68-year-old man with a mechanical aortic valve is maintained on warfarin. His PT/INR is elevated, and he presents with gum bleeding and ecchymoses.

Answer: Inhibits vitamin K epoxide reductase, reducing synthesis of factors II, VII, IX, X, and proteins C and S

Explanation: Warfarin blocks vitamin K epoxide reductase, preventing γ-carboxylation of vitamin K–dependent clotting factors. This reduces synthesis of active factors II, VII, IX, and X, and anticoagulant proteins C and S. It is monitored by PT/INR.

Note: Toxicity causes bleeding; reversal involves vitamin K for gradual correction or fresh frozen plasma for rapid reversal.

Question 43: A 60-year-old man with coronary artery disease is placed on daily low-dose aspirin for secondary prevention of myocardial infarction. He asks how the drug prevents clot formation.

Answer: Irreversibly inhibits COX-1 and COX-2, reducing thromboxane A₂

Explanation: Aspirin irreversibly acetylates cyclooxygenase-1 and -2 (COX-1/2), preventing conversion of arachidonic acid to thromboxane A₂ (TXA₂) in platelets. TXA₂ normally promotes platelet aggregation and vasoconstriction, so its inhibition prolongs bleeding time.

Note: Clopidogrel (ADP receptor blocker) is an alternative for aspirin allergy or as part of dual antiplatelet therapy after stent placement.

LEUKEMIA & LYMPHOMA

Question 44: A 52-year-old man presents with progressive fatigue, early satiety, and abdominal fullness. Exam reveals splenomegaly. CBC shows marked leukocytosis with predominance of myeloid precursors and basophilia. Leukocyte alkaline phosphatase (LAP) score is low.

Answer: BCR-ABL fusion

Explanation: Findings indicate chronic myeloid leukemia (CML), driven by the BCR-ABL fusion gene from the t(9;22) Philadelphia chromosome. The BCR-ABL tyrosine kinase constitutively activates growth pathways, causing uncontrolled granulocyte proliferation and basophilia. Low LAP differentiates CML from a leukemoid reaction.

Note: Treat with imatinib, a BCR-ABL tyrosine-kinase inhibitor that normalizes counts and induces long-term remission.

Question 45: A 13-year-old boy presents with fatigue, pallor, and bone pain. Exam shows generalized lymphadenopathy and a firm anterior mediastinal mass compressing the trachea. CBC shows elevated WBCs with lymphoblasts that are TdT-positive and CD3-positive.

Answer: T-cell acute lymphoblastic leukemia (T-ALL)

Explanation:

T-ALL arises from immature T-cell precursors that infiltrate the thymus, producing a mediastinal mass. It occurs mostly in adolescent males. Cells express TdT (marker of pre-T and pre-B blasts) and T-cell markers (CD2–CD8).

Note: Prognosis is worse with t(9;22) and better with t(12;21); therapy includes multi-agent chemotherapy ± CNS prophylaxis.

Question 46: A 28-year-old man presents with painless cervical lymphadenopathy, recurrent fevers, drenching night sweats, and intense itching after alcohol consumption. CBC is normal. Lymph node biopsy shows large binucleated cells with prominent nucleoli in a mixed inflammatory background.

Answer: Reed–Sternberg cells

Explanation:

Hodgkin lymphoma is defined by Reed–Sternberg cells (CD15⁺, CD30⁺ B cells) surrounded by reactive lymphocytes, plasma cells, and eosinophils. The cytokine-rich milieu causes B symptoms (fever, night sweats, weight loss).

Note: Lymphocyte-rich subtype has the best prognosis; lymphocyte-depleted subtype the worst.

Question 47: A 60-year-old man presents with progressive fatigue and fullness in the left upper quadrant. Physical exam reveals massive splenomegaly. CBC shows pancytopenia. Bone-marrow aspiration yields a dry tap due to fibrosis; biopsy shows lymphocytes with cytoplasmic "hairy" projections.

Answer: Cladribine

Explanation: Hairy cell leukemia is a mature B-cell neoplasm with cells positive for TRAP and CD11c/CD103. Fibrotic marrow causes a dry tap, and splenic infiltration leads to massive splenomegaly.

Note: Cladribine, a purine analog resistant to adenosine deaminase degradation, is the treatment of choice and is highly effective.

Question 48: A 42-year-old man presents with fatigue, bleeding gums, and easy bruising. Peripheral smear shows myeloblasts containing Auer rods. Coagulation studies reveal elevated PT/PTT and low fibrinogen. Cytogenetic analysis demonstrates t(15;17).

Answer: All-trans retinoic acid (ATRA)

Explanation: This is acute promyelocytic leukemia (APL), an AML subtype caused by t(15;17) forming the PML-RARα fusion, which blocks myeloid differentiation at the promyelocyte stage. Accumulated promyelocytes release procoagulants, causing DIC.

Note: ATRA binds the fusion receptor, restoring differentiation and remission.

Question 49: A 65-year-old man presents with chest pain and is diagnosed with STEMI. He receives intravenous alteplase. Shortly thereafter, he develops hematuria and gingival bleeding.

Answer: Thrombolytics convert plasminogen to plasmin, which degrades fibrin

Explanation: tPA (alteplase) and related drugs activate plasminogen → plasmin, which breaks down fibrin clots and fibrinogen, lysing thrombi. This restores perfusion but increases bleeding risk.

Note: Contraindicated in active bleeding, recent stroke or surgery, and severe uncontrolled hypertension (> 180/110 mm Hg).

Question 50: A 70-year-old man presents with progressive fatigue and painless cervical lymphadenopathy. CBC shows lymphocytosis with smudge cells on smear. Flow cytometry reveals CD5⁺ CD20⁺ CD23⁺ B cells.

Answer: Chronic lymphocytic leukemia (CLL)

Explanation:

CLL is an indolent B-cell leukemia of older adults, featuring fragile lymphocytes that appear as smudge cells. Lymphadenopathy and splenomegaly are common. Advanced disease may cause autoimmune hemolytic anemia.

Note: Managed expectantly until symptomatic; transformation to large-cell lymphoma (Richter syndrome) signifies poor prognosis.

Question 51: A 9-year-old boy from rural Uganda presents with a rapidly enlarging jaw mass. Biopsy shows a "starry-sky" pattern with sheets of medium-sized lymphocytes interspersed with macrophages containing ingested apoptotic debris.

Answer: Burkitt lymphoma

Explanation: Burkitt lymphoma, an aggressive B-cell tumor, is associated with EBV infection and c-myc activation from t(8;14) (c-myc on 8; Ig heavy-chain on 14). High mitotic rate produces the classic starry-sky appearance.

Note: Endemic (African) form involves the jaw; sporadic form typically affects the abdomen or pelvis.

ONCOLOGY PHARMACOLOGY

Question 52: A 62-year-old woman treated with doxorubicin for metastatic breast cancer develops progressive shortness of breath, orthopnea, and lower-extremity edema three months after completing therapy. Echocardiography reveals global left-ventricular dilation and reduced ejection fraction.

Answer: Dilated cardiomyopathy

Explanation: Doxorubicin (adriamycin) generates oxygen free radicals via iron-dependent redox cycling, damaging myocardial cell membranes and mitochondria. The result is dose-dependent dilated cardiomyopathy.

Note: Dexrazoxane, an iron-chelating agent, prevents free-radical formation and limits cardiac toxicity without affecting antitumor efficacy.

Question 53: A 50-year-old man with a history of chronic Helicobacter pylori gastritis presents with early satiety and epigastric discomfort. Endoscopy reveals a shallow gastric ulcer with surrounding nodularity; biopsy shows small B cells infiltrating the lamina propria.

Answer: Marginal-zone lymphoma

Explanation: Chronic antigenic stimulation by H. pylori leads to formation of mucosa-associated lymphoid tissue (MALT) and eventual marginal-zone B-cell lymphoma. Eradication of H. pylori with proton-pump inhibitor plus antibiotics often induces regression.

Note: Unlike follicular lymphoma (t(14;18), BCL2 activation), MALT lymphoma is antigen-driven and potentially reversible early.

Question 54: A 48-year-old woman receiving cytotoxic chemotherapy for breast cancer develops a temperature of 101.8 °F, chills, and oral ulcers. CBC shows WBC 0.4 × 10⁹/L with an absolute neutrophil count < 500/µL.

Answer: Neutropenic fever

Explanation: Neutropenic fever is an oncologic emergency caused by chemotherapy-induced marrow suppression. Loss of neutrophil-mediated host defense allows rapid bacteremia, most often from Pseudomonas or enteric flora.

Note: Start empiric broad-spectrum IV antibiotics (e.g., cefepime, piperacillin–tazobactam) immediately—before cultures—to prevent sepsis.

Question 55: A 67-year-old man on long-term amiodarone therapy for atrial fibrillation presents with progressive dyspnea and dry cough. Pulmonary exam reveals fine inspiratory crackles. High-resolution CT shows diffuse interstitial infiltrates.

Answer: Busulfan, Bleomycin, Methotrexate, and Amiodarone

Explanation: Several agents—including bleomycin (free-radical injury), busulfan (DNA alkylation), methotrexate (hypersensitivity reaction), and amiodarone (phospholipid accumulation)—cause restrictive interstitial pulmonary fibrosis.

Note: Monitor pulmonary function tests; discontinue the offending drug if DLCO declines.

Question 56: A 58-year-old man presents with scaly, erythematous skin patches on the trunk that have gradually thickened into nodules. He also has generalized lymphadenopathy. Skin biopsy shows epidermotropic CD4⁺ T cells forming Pautrier microabscesses.

Answer: Mycosis fungoides

Explanation: Mycosis fungoides is a cutaneous T-cell lymphoma in which malignant helper T cells infiltrate the skin. It progresses from eczematous patches → plaques → tumors.

Note: Blood involvement produces Sézary syndrome, featuring cerebriform lymphocytes (folded nuclei) on smear.

Question 57: A 44-year-old man receiving 6-mercaptopurine (6-MP) for acute lymphoblastic leukemia starts allopurinol for gout prophylaxis and subsequently develops profound pancytopenia.

Answer: 6-MP is degraded by xanthine oxidase, which is inhibited by allopurinol

Explanation: Allopurinol inhibits xanthine oxidase, the enzyme that metabolizes 6-MP to inactive products. Concomitant use markedly increases 6-MP levels, leading to marrow suppression and hepatotoxicity.

Note: Reduce the 6-MP dose when combined with xanthine-oxidase inhibitors.

Question 58: A 7-year-old boy receiving induction chemotherapy for acute lymphoblastic leukemia develops flank pain, nausea, and dark urine. Labs show K⁺ 6.1 mEq/L [3.5–5.0], phosphate 6.5 mg/dL [2.5–4.5], uric acid 12 mg/dL [3.5–7.2], and Ca²⁺ 6.8 mg/dL [8.5–10.5].

Answer: Elevated uric acid, elevated phosphate, elevated potassium, decreased calcium

Explanation: Tumor lysis syndrome arises from rapid destruction of malignant cells releasing nucleic acids, K⁺, and phosphate. Precipitation of uric acid and Ca-phosphate in renal tubules causes acute kidney injury.

Note: Prevent with aggressive hydration, allopurinol (xanthine-oxidase inhibitor) or rasburicase (uricase enzyme).

Question 59: A 6-year-old girl receiving combination chemotherapy for leukemia develops symmetric tingling and weakness in her hands and feet. Neuro exam reveals decreased ankle reflexes.

Answer: Inhibits microtubule formation, preventing mitotic spindle formation

Explanation: Vincristine binds β-tubulin, preventing polymerization of microtubules and arresting cells in metaphase. The drug selectively injures neurons, causing peripheral neuropathy that is dose-limiting.

Note: Vinblastine causes myelosuppression instead; "cristine = CNS, blastine = bone marrow**."

Question 60: A 42-year-old HIV-positive man with CD4 count < 50 cells/µL presents with new-onset confusion and right-sided weakness. Brain MRI shows a single ring-enhancing lesion in the parietal lobe. Serology for Toxoplasma gondii is negative.

Answer: Primary CNS lymphoma

Explanation:

Primary CNS lymphoma is an EBV-driven B-cell lymphoma that occurs in severe immunosuppression. It typically appears as a solitary periventricular ring-enhancing lesion and must be distinguished from toxoplasmosis (usually multiple lesions).

Note: Diagnosis confirmed by EBV DNA in CSF or biopsy.

Question 61: A 68-year-old man reports recurrent headaches, blurred vision, and tingling in his feet. Fundoscopy shows dilated, tortuous retinal veins. Serum protein electrophoresis demonstrates an IgM spike.

Answer: Waldenström macroglobulinemia

Explanation:

Waldenström macroglobulinemia is a lymphoplasmacytic B-cell neoplasm producing IgM monoclonal gammopathy, which causes hyperviscosity (headache, vision changes, neuropathy) but no lytic bone lesions.

Note: Plasmapheresis rapidly relieves hyperviscosity; bone marrow has < 10 % plasma cells (unlike multiple myeloma).

Question 62: A 59-year-old woman treated with cyclophosphamide for ovarian carcinoma develops dysuria and hematuria. Urinalysis reveals numerous red blood cells without infection. Cystoscopy shows erythematous bladder mucosa.

Answer: Hemorrhagic cystitis and bladder cancer

Explanation:

Cyclophosphamide is metabolized to acrolein, which irritates the bladder epithelium, causing hemorrhagic cystitis and, chronically, transitional-cell carcinoma.

Note: MESNA (2-mercaptoethanesulfonate) binds acrolein, neutralizing its toxicity.

Question 63: A 70-year-old man with multiple myeloma receives bortezomib and dexamethasone. After several cycles, his M-protein level decreases markedly.

Answer: Proteasome inhibitor that induces apoptosis, used in multiple myeloma

Explanation:

Bortezomib and carfilzomib inhibit the 26S proteasome, preventing degradation of pro-apoptotic proteins and causing accumulation of misfolded proteins → ER stress and apoptosis in plasma cells.

Note: Also used for mantle-cell lymphoma; main toxicity is peripheral neuropathy.

Question 64: A 55-year-old woman on weekly methotrexate for rheumatoid arthritis develops painful mouth ulcers and pancytopenia.

Answer: Leucovorin (folinic acid)

Explanation:

Methotrexate inhibits dihydrofolate reductase, blocking tetrahydrofolate regeneration and halting dTMP synthesis, leading to mucositis and marrow suppression. Leucovorin bypasses the blocked enzyme, rescuing normal cells without reducing antitumor activity.

Note: Distinct from folic acid—it does not require activation by DHFR.

Question 65: A 72-year-old man presents with chronic back pain and fatigue. Labs show Ca²⁺ 11.8 mg/dL [8.5–10.5], creatinine 2.3 mg/dL, and normocytic anemia. Peripheral smear shows rouleaux formation.

Answer: Multiple myeloma

Explanation:

Multiple myeloma is a malignant proliferation of plasma cells producing monoclonal Ig (or light chains) leading to CRAB findings: hyperCalcemia, Renal failure, Anemia, Bone lytic lesions. Serum protein electrophoresis shows an M-spike.

Note: Pathologic fractures and recurrent infections are common; confirm with bone-marrow biopsy showing > 10 % plasma cells.

HEMATOLOGY/ONCOLOGY HIGH-YIELD NOTES

Question 66: A 3-year-old child presents with pallor, hepatosplenomegaly, and characteristic "chipmunk" facies due to maxillary overgrowth. Hemoglobin electrophoresis shows ↑ HbA₂, ↑ HbF, and absence of HbA.

Answer: Beta-thalassemia major

Explanation:

β-thalassemia major results from mutations causing absent β-globin synthesis. Unpaired α-chains precipitate, destroying erythroblasts (ineffective erythropoiesis). Extramedullary hematopoiesis enlarges the liver, spleen, and bones.

Note: Transfusion-dependent; iron chelation prevents secondary hemochromatosis.

Question 67: A 30-year-old man presents with progressive fatigue. CBC reveals Hb 8.0 g/dL [13–17], MCV 68 fL [80–100], ferritin normal, and no improvement after oral iron.

Answer: Hemoglobin electrophoresis

Explanation:

Microcytic anemia with normal ferritin and no iron-therapy response suggests thalassemia rather than iron deficiency. Electrophoresis distinguishes α- vs β-thalassemia by identifying abnormal Hb fractions (↑ HbA₂, HbF).

Note: Always rule out thalassemia before giving long-term iron supplementation.

Question 68: A 45-year-old woman reports fatigue and pallor. Labs show Hb 9.5 g/dL, MCV 72 fL, ferritin 8 ng/mL [15–150], and elevated TIBC.

Answer: Iron deficiency anemia

Explanation:

Classic pattern—low Hb, low MCV, low ferritin, high TIBC—reflects iron deficiency from chronic blood loss or poor intake. Decreased heme synthesis produces microcytic, hypochromic RBCs.

Note: In older adults, evaluate for occult gastrointestinal bleeding (colon carcinoma or angiodysplasia).
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
    print("Extracting questions from anemia/hematology content...")
    questions = extract_questions(ANEMIA_CONTENT)
    
    print(f"Found {len(questions)} questions")
    
    # Create output directory
    output_dir = Path("anemia_images")
    output_dir.mkdir(exist_ok=True)
    
    # Create a log file
    log_file = output_dir / "download_log.txt"
    
    downloaded_count = 0
    failed_count = 0
    
    print(f"Starting download process for {len(questions)} questions...")
    print(f"Output directory: {output_dir.absolute()}\n")
    
    with open(log_file, 'w', encoding='utf-8') as log:
        log.write("Anemia/Hematology Question Image Download Log\n")
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






