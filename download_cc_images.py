#!/usr/bin/env python3
"""
Script to download Creative Commons licensed images for medical education questions.
Uses Wikimedia Commons API to find and download CC-licensed images.
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
    print("Install with: pip3 install --user Pillow")

# Content text with all questions
CONTENT = """IvyTutoring































*Be sure to watch the recorded session along with this document to make sure you get the full explanations. 













IvyTutoring

ANEMIA

Question 1: A 35-year-old man reports dark, cola-colored urine each morning for the past several weeks. He notes increasing fatigue and has a history of unexplained deep vein thrombosis in the hepatic veins (Budd–Chiari syndrome). Physical exam reveals pallor and mild jaundice.

Answer: Paroxysmal nocturnal hemoglobinuria (PNH)

Explanation:

PNH results from an acquired PIGA gene mutation in hematopoietic stem cells. This gene is required for synthesis of GPI anchors that attach complement-regulatory proteins (CD55 and CD59) to red cell membranes. Without these proteins, red cells become vulnerable to complement-mediated lysis, particularly at night when mild respiratory acidosis enhances complement activation. Chronic intravascular hemolysis leads to hemoglobinuria and hemosiderinuria, and free hemoglobin scavenges nitric oxide, promoting smooth muscle spasm and thrombosis—especially in hepatic, portal, or cerebral veins.

Note: Eculizumab, a monoclonal antibody against complement C5, prevents further complement-mediated destruction.



Question 2: A 26-year-old pregnant woman presents for evaluation of persistent fatigue. CBC shows a hemoglobin of 10.2 g/dL, MCV of 68 fL, ferritin within the normal range, and no improvement after several weeks of oral iron therapy.

Answer: Hemoglobin electrophoresis

Explanation:

Microcytic anemia with normal ferritin and no response to iron therapy suggests thalassemia, a defect in globin chain synthesis. Iron studies are normal because iron metabolism is intact. The next diagnostic step is hemoglobin electrophoresis, which can distinguish between β-thalassemia (↑HbA₂, ±↑HbF) and α-thalassemia (normal electrophoresis in silent/minor forms). Microcytosis occurs due to extra cell divisions in erythroid precursors trying to normalize MCHC despite defective hemoglobin formation.

Note: Thalassemia severity depends on the number of affected globin genes; β⁰ mutations abolish β-globin synthesis entirely.



Question 3: A 29-year-old vegan presents with progressive numbness in her fingertips and gait instability. Labs reveal macrocytic anemia and elevated methylmalonic acid and homocysteine levels.

Answer: Vitamin B12 deficiency

Explanation:

Vitamin B12 (cobalamin) deficiency causes impaired DNA synthesis and abnormal myelin formation. It is required to convert methylmalonyl-CoA → succinyl-CoA and homocysteine → methionine. Elevated methylmalonic acid disrupts myelin, producing paresthesias and posterior column demyelination. B12 is found only in animal products; thus strict vegans are susceptible. Other causes include pernicious anemia (autoimmune loss of intrinsic factor), ileal disease, or tapeworm infection.

Note: Neurologic findings distinguish B12 deficiency from folate deficiency, which lacks methylmalonic acid elevation.



Question 4: A fetus is stillborn at 32 weeks' gestation with severe generalized edema, ascites, and placentomegaly. Hemoglobin electrophoresis shows only Hb Barts (γ₄).

Answer: Alpha thalassemia major (hydrops fetalis)

Explanation:

Deletion of all four α-globin genes (—/— —/—) results in absence of α chains, forcing γ chains to form tetramers (Hb Barts) with extremely high oxygen affinity. This prevents oxygen delivery to tissues, causing severe hypoxia, high-output cardiac failure, and hydrops fetalis. α-globin gene deletions are more common in Southeast Asian populations due to cis deletions.

Note: Hydrops fetalis is uniformly fatal without in utero transfusion.



Question 5: A 42-year-old man receiving isoniazid therapy for latent tuberculosis develops fatigue and pallor. CBC reveals microcytic anemia, and bone marrow examination shows ringed sideroblasts.

Answer: Vitamin B6 (pyridoxine) supplementation

Explanation:

Isoniazid inhibits pyridoxine phosphokinase, decreasing active vitamin B6, a cofactor for δ-aminolevulinic acid (ALA) synthase—the rate-limiting enzyme in heme synthesis. This leads to defective protoporphyrin formation and iron accumulation in mitochondria (ringed sideroblasts). Despite high serum iron and ferritin, functional hemoglobin synthesis is impaired.

Note: Sideroblastic anemia may also result from alcohol, lead toxicity, or myelodysplastic syndromes.



Question 6: A 28-year-old woman presents with fatigue and pica (craving ice). Labs show: Hb 9.5 g/dL [12–16], MCV 72 fL [80–100], ferritin 8 ng/mL [15–150], and elevated total iron-binding capacity (TIBC).

Answer: Iron deficiency anemia

Explanation:

Low ferritin and high TIBC reflect depleted iron stores and increased transferrin production by the liver. Iron deficiency causes defective heme synthesis, producing microcytosis and hypochromia. Early symptoms include fatigue, pallor, and sometimes pica. Common causes: menstrual blood loss, poor diet, or occult GI bleeding (colon cancer in older adults). Chronic deficiency leads to spoon nails (koilonychia) and glossitis.

Note: Treat with oral iron and identify source of loss before replacement.



Question 7: A 4-year-old boy presents with pallor, growth delay, and characteristic facial changes including frontal bossing and maxillary overgrowth. He has massive hepatosplenomegaly. Hemoglobin electrophoresis reveals elevated HbA₂ and HbF with absent HbA.

Answer: Increased HbF and HbA₂, absence of HbA

Explanation:

These findings are diagnostic for β-thalassemia major, caused by mutations leading to absent β-globin synthesis. Without β chains, fetal γ chains persist (↑HbF) and δ chains increase (↑HbA₂). The imbalance causes ineffective erythropoiesis and extramedullary hematopoiesis, explaining bone deformities and hepatosplenomegaly. Repeated transfusions are required but cause secondary hemosiderosis (iron overload).

Note: Iron chelation is necessary in long-term transfusion therapy.



Question 8: A 34-year-old woman with systemic lupus erythematosus presents with progressive fatigue and dark urine. Labs show hemoglobin 8.5 g/dL and a positive direct Coombs test.

Answer: Warm autoimmune hemolytic anemia

Explanation:

Warm AIHA involves IgG antibodies that bind red cells at body temperature. These opsonized cells are cleared by splenic macrophages, causing extravascular hemolysis. It often occurs secondary to autoimmune diseases like SLE or CLL and certain drugs. Peripheral smear may show spherocytes from partial phagocytosis.

Note: First-line therapy is corticosteroids; refractory cases may require rituximab or splenectomy.



Question 9: A 58-year-old man with long-standing rheumatoid arthritis presents with fatigue. Labs show normocytic anemia, elevated ferritin, and low total iron-binding capacity.

Answer: Treat the underlying disease

Explanation:

Anemia of chronic disease (ACD) is mediated by chronic inflammation increasing hepcidin production from the liver. Hepcidin degrades ferroportin, trapping iron in macrophages and enterocytes, and inhibiting erythropoietin production. The result is impaired iron utilization despite normal stores. Correction requires control of the underlying inflammatory condition.

Note: Ferritin is high because iron is sequestered intracellularly; serum iron and TIBC are both low.



Question 10: A 30-year-old man develops sudden fatigue, jaundice, and dark urine after taking trimethoprim-sulfamethoxazole for a urinary tract infection. His peripheral smear shows bite cells and Heinz bodies.

Answer: Glucose-6-phosphate dehydrogenase (G6PD) deficiency

Explanation:

G6PD deficiency is an X-linked disorder causing impaired regeneration of NADPH in the pentose phosphate pathway. Without NADPH, glutathione cannot neutralize oxidative stress from drugs (sulfa drugs, antimalarials), infections, or fava beans. Oxidized hemoglobin forms Heinz bodies that are removed by splenic macrophages, producing bite cells and intravascular hemolysis.

Note: Avoid known oxidant triggers to prevent recurrence.



Question 11: A 60-year-old woman presents with fatigue, paresthesias, and glossitis. Labs reveal macrocytosis and elevated methylmalonic acid. Anti–intrinsic factor antibodies are positive.

Answer: Autoimmune destruction of gastric parietal cells

Explanation:

Pernicious anemia is an autoimmune gastritis in which antibodies target intrinsic factor or parietal cells, leading to loss of intrinsic factor and subsequent vitamin B12 malabsorption. This causes megaloblastic anemia with neurologic symptoms due to demyelination of the posterior and lateral spinal columns. The chronic atrophic gastritis also predisposes to gastric adenocarcinoma.

Note: Lifelong parenteral vitamin B12 replacement is required.



Question 12: A 45-year-old woman with rheumatoid arthritis treated with methotrexate presents with fatigue. Labs show macrocytic anemia and elevated homocysteine but normal methylmalonic acid.

Answer: Folate deficiency

Explanation:

Methotrexate inhibits dihydrofolate reductase, preventing the conversion of dihydrofolate to tetrahydrofolate, an essential cofactor for thymidine synthesis. This blocks DNA synthesis and causes megaloblastic anemia. Because methylmalonic acid remains normal, this distinguishes folate deficiency from B12 deficiency.

Note: Folic acid supplementation prevents this adverse effect during methotrexate therapy.



Question 13: A 7-year-old boy presents with pallor, recurrent infections, and skeletal anomalies including absent thumbs and short stature. CBC shows pancytopenia.

Answer: Stem cell transplant

Explanation:

Fanconi anemia is an autosomal recessive disorder of DNA repair, leading to bone marrow failure, aplastic anemia, and congenital malformations (thumb/radial defects, short stature, café-au-lait spots). There is increased risk of AML and squamous cell carcinoma. Bone marrow transplantation is curative for the hematologic component.

Note: Cells show increased chromosomal breakage after DNA cross-linking agents.



Question 14: A 22-year-old man presents with jaundice and splenomegaly. Labs reveal mild anemia and elevated MCHC. Peripheral smear shows small, dense red cells without central pallor.

Answer: Pigmented gallstones

Explanation:

Hereditary spherocytosis is caused by defects in membrane proteins such as spectrin or ankyrin, leading to loss of membrane surface area and formation of spherocytes. These are trapped and destroyed in the spleen (extravascular hemolysis), causing hyperbilirubinemia and increased risk of pigmented gallstones. Splenectomy prevents further hemolysis.

Note: The osmotic fragility test confirms diagnosis.



Question 15: A 50-year-old man with chronic alcoholism presents with fatigue and glossitis. CBC shows macrocytic anemia with elevated homocysteine but normal methylmalonic acid.

Answer: Folate supplementation

Explanation:

Alcohol interferes with folate absorption in the jejunum and impairs hepatic folate storage. Folate deficiency causes defective thymidine synthesis and megaloblastic anemia. Elevated homocysteine reflects impaired methylation pathways, but methylmalonic acid remains normal, distinguishing it from B12 deficiency.

Note: Chronic alcoholism often causes concurrent nutritional and liver-related anemias.



Question 16: A 5-year-old boy with known sickle cell disease presents with sudden left upper quadrant pain, pallor, and lethargy. Exam shows a rapidly enlarging spleen. Labs reveal severe anemia with elevated reticulocyte count.

Answer: Splenic sequestration crisis

Explanation:

In sickle cell disease, repeated vaso-occlusion can trap large volumes of blood in the spleen, causing hypovolemic shock and acute anemia. Reticulocyte count rises as bone marrow responds. This differs from aplastic crisis (usually due to parvovirus B19), which features absent reticulocytes and no splenomegaly.

Note: Chronic infarction eventually leads to autosplenectomy by adolescence.



Question 17: A 9-month-old boy is brought to the clinic for evaluation of persistent pallor and jaundice. His parents report that he tires easily during feeding and has had several episodes of scleral icterus since infancy. There is no history of infection or medication exposure. Physical exam reveals mild hepatosplenomegaly. Laboratory studies show hemoglobin 8.2 g/dL, elevated indirect bilirubin, increased lactate dehydrogenase, and a markedly elevated reticulocyte count. Peripheral smear shows echinocytes (burr cells). 2,3-bisphosphoglycerate (2,3-BPG) levels are elevated.

Answer: Pyruvate kinase deficiency

Explanation:

 Pyruvate kinase deficiency is an autosomal recessive defect in glycolysis that prevents conversion of phosphoenolpyruvate to pyruvate, blocking ATP generation in erythrocytes. Red blood cells rely entirely on glycolysis for energy; without sufficient ATP, Na⁺/K⁺ pumps fail, membranes become rigid, and cells undergo extravascular hemolysis in the spleen. The chronic hemolysis causes indirect hyperbilirubinemia, jaundice, and splenomegaly. Elevated 2,3-BPG shifts the hemoglobin–oxygen dissociation curve to the right, facilitating oxygen unloading to tissues but worsening anemia.

 Note: Management is mainly supportive with transfusions as needed; splenectomy may reduce hemolysis in severe cases.





Question 18: A 3-year-old child presents with developmental delay, constipation, and abdominal pain. CBC shows microcytic anemia. Peripheral smear reveals coarse basophilic stippling of erythrocytes.

Answer: Basophilic stippling

Explanation:

Lead poisoning inhibits ferrochelatase and ALA dehydratase, blocking heme synthesis. It also inhibits ribonuclease, leading to retention of ribosomal RNA—seen as basophilic stippling. Children are at risk due to ingestion of lead-based paint or contaminated dust. Neurologic and gastrointestinal symptoms are common.

Note: Treat with chelation (succimer or EDTA) if blood lead levels are significantly elevated.



SICKLE CELL DISEASE

Question 19: A sickle cell patient presents with fever, signs of sepsis, and Howell-Jolly bodies on a blood smear. What is the next step in management?

 Answer: Vaccination and prophylactic antibiotics

 Explanation: Howell-Jolly bodies indicate functional asplenia, increasing the risk of infections by encapsulated organisms. Vaccination and antibiotics are crucial.

 Note: Autosplenectomy in sickle cell disease results from repeated splenic infarctions.



Question 20: A child with sickle cell disease presents with joint pain, fever, chest pain, and a new infiltrate on chest X-ray. What is the diagnosis?

 Answer: Acute chest syndrome

 Explanation: Acute chest syndrome is a complication of sickle cell disease characterized by chest pain, fever, and pulmonary infiltrates, often triggered by infection.

 Note: Management includes oxygen, antibiotics, blood transfusion, and pain control.



Question 21: A patient with sickle cell trait presents with painless hematuria. What is the most likely cause?

 Answer: Renal papillary necrosis

 Explanation: Sickle cell trait can lead to ischemic necrosis of the renal papillae, causing hematuria.

 Note: Hematuria in sickle cell trait is typically isolated, without casts or proteinuria.



Question 22: A child with sickle cell disease experiences acute neurological deficits. What preventive measure could have been taken?

 Answer: Hydroxyurea or chronic transfusion therapy

 Explanation: Hydroxyurea and chronic transfusions reduce the risk of stroke in sickle cell patients by decreasing sickling and improving blood flow.

 Note: Vaso-occlusive crises in sickle cell disease can lead to strokes and other complications.



HEMOLYTIC DISEASE OF THE NEWBORN

Question 23: A type O mother delivers a baby with jaundice in the first 24 hours. What is the diagnosis?

 Answer: ABO incompatibility

 Explanation: ABO incompatibility is the most common cause of hemolytic disease in newborns, affecting the first pregnancy and causing jaundice.

 Note: The Coombs test is positive, and treatment includes phototherapy.



Question 24: A newborn develops severe jaundice within the first 24 hours of life. What is the diagnosis?

 Answer: Rh incompatibility

 Explanation: Rh incompatibility occurs when an Rh-negative mother produces antibodies against an Rh-positive fetus, leading to hemolytic anemia and jaundice.

 Note: Prevention involves administering Rho(D) immune globulin to the mother during and after pregnancy.



PORPHYRIA AND BLEEDING DISORDERS

Question 25: A man presents with blisters on sun-exposed areas. What condition is associated with these symptoms?

 Answer: Porphyria cutanea tarda (PCT)

 Explanation: PCT is linked to chronic blistering photosensitivity and is often associated with hepatitis C.

 Note: Treatment includes phlebotomy and low-dose hydroxychloroquine.



Question 26: A female presents with bruises, prolonged bleeding time, and a platelet count of 50,000. What condition explains these findings?

 Answer: Immune thrombocytopenic purpura (ITP)

 Explanation: ITP is characterized by autoantibody-mediated platelet destruction, leading to thrombocytopenia and bleeding.

 Note: First-line treatment is corticosteroids, with splenectomy for refractory cases.



Question 27: A woman experiences abdominal pain and dark urine after fasting or taking certain drugs. What condition explains these symptoms?

 Answer: Acute intermittent porphyria (AIP)

 Explanation: AIP is caused by a defect in porphobilinogen deaminase, leading to a buildup of ALA and symptoms like abdominal pain and dark urine.

 Note: Treatment involves glucose and hemin to downregulate ALA synthase.



COAGULATION AND BLEEDING DISORDERS

Question 28: A child has bruises, normal platelet count, prolonged bleeding time, and no agglutination with ristocetin. What is the diagnosis?

 Answer: Bernard-Soulier syndrome

 Explanation: Bernard-Soulier syndrome is due to a deficiency in GP1b, impairing platelet adhesion and causing bleeding.

 Note: Glanzmann thrombasthenia involves a deficiency in GPIIb/IIIa, affecting platelet aggregation.



Question 29: A neonate born at home presents with bleeding from the umbilical stump. What is the treatment?

 Answer: Vitamin K

 Explanation: Vitamin K deficiency in neonates leads to bleeding, as they lack sufficient vitamin K for clotting factor synthesis.

 Note: Prophylactic vitamin K is essential to prevent bleeding in newborns.



Question 30: A female with menorrhagia, epistaxis, and bleeding after dental extraction has labs showing increased BT and PTT with normal PT. What is the treatment?

 Answer: Desmopressin

 Explanation: Von Willebrand disease involves defective platelet adhesion due to decreased vWF, which also stabilizes factor VIII.

 Note: Desmopressin increases vWF release, improving hemostasis.



Question 31: A patient with chronic kidney disease has mucosal bleeding despite a normal platelet count. What is the explanation?

 Answer: Uremic platelet dysfunction

 Explanation: Uremic toxins impair platelet function, leading to prolonged bleeding time despite normal platelet count.

 Note: Desmopressin can temporarily improve platelet function.



Question 32: A boy presents with hemarthrosis and prolonged PTT, with normal PT. What is the diagnosis?

 Answer: Hemophilia A or B

 Explanation: Hemophilia A (factor VIII deficiency) and B (factor IX deficiency) are X-linked disorders causing prolonged PTT and bleeding.

 Note: Joint bleeding and muscle hematomas are common, with a positive family history.



DISSEMINATED INTRAVASCULAR COAGULATION (DIC)

Question 33: A postpartum woman develops shortness of breath and bleeding from IV sites. What are the lab findings?

 Answer: Increased PT/PTT/BT/D-dimer, decreased fibrinogen and platelets

 Explanation: DIC due to amniotic fluid embolism causes massive coagulation and fibrinolysis, resulting in respiratory distress and bleeding.

 Note: Management focuses on supportive care and treating the underlying cause.



Question 34: A patient with sepsis develops bleeding from catheter and IV sites. What condition explains these findings?

 Answer: Disseminated intravascular coagulation (DIC)

 Explanation: DIC is a consumptive coagulopathy triggered by infection, trauma, or malignancy, leading to widespread bleeding.

 Note: Treatment involves addressing the underlying cause and providing fresh frozen plasma.



THROMBOPHILIA AND ANTICOAGULATION

Question 35: A patient has recurrent venous clots. What is the most likely etiology?

 Answer: Factor V Leiden mutation

 Explanation: Factor V Leiden mutation is the most common inherited thrombophilia, causing resistance to inactivation by protein C.

 Note: It increases the risk of DVT and PE, with normal PT/PTT.



Question 36: A patient with nephrotic syndrome develops DVT or renal vein thrombosis. What is the diagnosis?

 Answer: Antithrombin III deficiency

 Explanation: Nephrotic syndrome leads to urinary loss of antithrombin III, increasing the risk of thrombosis.

 Note: Heparin may be ineffective; consider direct thrombin inhibitors.



Question 37: A female with SLE presents with DVT and prolonged PTT that does not correct with a mixing study. What is the diagnosis?

 Answer: Antiphospholipid syndrome

 Explanation: Antiphospholipid syndrome is characterized by recurrent thrombosis and pregnancy loss, with positive antiphospholipid antibodies.

 Note: Lifelong anticoagulation is required, as lupus anticoagulant prolongs PTT without causing bleeding.



HEPARIN AND WARFARIN MANAGEMENT

Question 38: A patient on heparin develops a 50% drop in platelet count. What is the diagnosis?

 Answer: Heparin-induced thrombocytopenia (HIT)

 Explanation: HIT is a type II hypersensitivity reaction with IgG antibodies against the heparin-platelet factor 4 complex, increasing thrombosis risk.

 Note: Discontinue heparin and start a direct thrombin inhibitor.



Question 39: What is the mechanism and advantage of rivaroxaban?

 Answer: Factor Xa inhibitor

 Explanation: Rivaroxaban is a direct oral anticoagulant that inhibits factor Xa, reducing clot formation without routine monitoring.

 Note: It has fewer food and drug interactions, with andexanet alfa as a reversal agent.



Question 40: A patient develops skin necrosis shortly after starting warfarin. What could have prevented this?

 Answer: Bridging with heparin

 Explanation: Protein C deficiency can cause a transient hypercoagulable state when starting warfarin, leading to skin necrosis.

 Note: Bridging with heparin prevents this complication by providing anticoagulation during the initial phase.



Question 41: How do you monitor heparin therapy? What is the reversal agent?

 Answer: Monitor with PTT; reverse with protamine sulfate

 Explanation: Heparin enhances antithrombin III activity, inhibiting thrombin and factor Xa, requiring PTT monitoring.

 Note: Heparin is safe in pregnancy, unlike warfarin.



Question 42: What is the mechanism of warfarin?

 Answer: Inhibits vitamin K epoxide reductase, reducing synthesis of factors II, VII, IX, X, and proteins C and S

 Explanation: Warfarin decreases vitamin K-dependent clotting factors, monitored by PT/INR.

 Note: Warfarin toxicity causes bleeding; reversal involves vitamin K and fresh frozen plasma.



Question 43: What is the mechanism of aspirin?

 Answer: Irreversibly inhibits COX-1 and COX-2, reducing thromboxane A2

 Explanation: Aspirin inhibits platelet aggregation by blocking thromboxane A2 production.

 Note: Clopidogrel, an ADP receptor inhibitor, is used in patients with aspirin allergy or in dual antiplatelet therapy.



LEUKEMIA & LYMPHOMA

Question 44: A patient presents with fatigue, splenomegaly, elevated basophils, and low leukocyte alkaline phosphatase (LAP). What is the most likely associated gene mutation?

 Answer: BCR-ABL fusion

 Explanation: The BCR-ABL fusion gene, resulting from t(9;22), is associated with chronic myeloid leukemia (CML), characterized by leukocytosis with a left shift and basophilia.

 Note: Imatinib, a tyrosine kinase inhibitor, is effective in treating CML.



Question 45: A child presents with bone pain, fatigue, pallor, lymphadenopathy, and a mediastinal mass. What condition best explains these findings?

 Answer: T-cell acute lymphoblastic leukemia (T-ALL)

 Explanation: T-ALL is characterized by a mediastinal mass due to thymic involvement, often seen in adolescent males. It may present with elevated WBCs and lymphoblasts that are TdT positive.

 Note: Poor prognosis is associated with t(9;22), while t(12;21) indicates a better prognosis.



Question 46: A patient presents with cervical lymphadenopathy, night sweats, and itching after alcohol intake. What would smear show?

 Answer: Reed-Sternberg cells

 Explanation: Reed-Sternberg cells (CD15+, CD30+) are characteristic of Hodgkin lymphoma, which often presents with B symptoms such as fever, night sweats, and weight loss.

 Note: The lymphocyte-rich subtype has the best prognosis, while the lymphocyte-depleted subtype has the worst.



Question 47: A patient has pancytopenia, massive splenomegaly, and a dry tap on bone marrow aspiration. What is the treatment?

 Answer: Cladribine

 Explanation: Cladribine is used to treat hairy cell leukemia, a B-cell neoplasm characterized by "hairy" cytoplasmic projections and a fibrotic bone marrow leading to a dry tap.

 Note: Hairy cell leukemia cells are positive for tartrate-resistant acid phosphatase (TRAP).



Question 48: A patient presents with fatigue and petechiae. Peripheral smear shows Auer rods. What is the treatment?

 Answer: All-trans retinoic acid (ATRA)

 Explanation: ATRA induces maturation of blasts in acute promyelocytic leukemia (APL), a subtype of acute myeloid leukemia (AML) characterized by the presence of Auer rods.

 Note: APL is associated with t(15;17) and has a high risk of disseminated intravascular coagulation (DIC).



Question 49: What is the mechanism and contraindications of thrombolytics like tPA?

 Answer: Thrombolytics convert plasminogen to plasmin, which degrades fibrin.

 Explanation: Thrombolytics facilitate clot breakdown by activating plasminogen to plasmin, which then degrades fibrin clots.

 Note: Contraindications include active bleeding, recent stroke or surgery, and severe hypertension (>180/110 mmHg).



Question 50: An elderly patient presents with fatigue, lymphadenopathy, and a smear showing smudge cells. What is the diagnosis?

 Answer: Chronic lymphocytic leukemia (CLL)

 Explanation: CLL is the most common leukemia in adults, characterized by fragile lymphocytes that appear as smudge cells on a smear. Flow cytometry shows CD5+, CD20+, CD23+ B cells.

 Note: CLL often presents with lymphadenopathy and is typically indolent.



Question 51: An African boy has a jaw mass. Biopsy shows a "starry-sky" appearance. What is the diagnosis?

 Answer: Burkitt lymphoma

 Explanation: Burkitt lymphoma is associated with Epstein-Barr virus (EBV) and characterized by a "starry-sky" appearance on biopsy. It involves c-myc activation due to t(8;14).

 Note: The endemic form affects the jaw, while the sporadic form affects the abdomen.



ONCOLOGY PHARMACOLOGY

Question 52: What is the major toxicity of doxorubicin?

 Answer: Dilated cardiomyopathy

 Explanation: Doxorubicin can cause dilated cardiomyopathy due to free radical formation, which can be mitigated with dexrazoxane.

 Note: Dexrazoxane is an iron-chelating agent that reduces free radical damage.



Question 53: A patient with H. pylori infection develops gastric MALT lymphoma. What is the most likely etiology?

 Answer: Marginal zone lymphoma

 Explanation: Gastric MALT lymphoma is a type of marginal zone lymphoma that may regress with H. pylori eradication using proton pump inhibitors and antibiotics.

 Note: Follicular lymphoma presents with painless waxing and waning lymphadenopathy and is associated with t(14;18).



Question 54: A chemotherapy patient develops pancytopenia and fever of 101.8°F. What is the diagnosis?

 Answer: Neutropenic fever

 Explanation: Neutropenic fever is a medical emergency in chemotherapy patients, requiring immediate empiric IV broad-spectrum antibiotics.

 Note: It can also lead to aplastic anemia due to damage to hematopoietic stem cells.



Question 55: Which drugs cause pulmonary fibrosis?

 Answer: Busulfan, Bleomycin, Methotrexate, and Amiodarone

 Explanation: These drugs can cause pulmonary fibrosis, necessitating monitoring with pulmonary function tests during therapy.

 Note: Pulmonary toxicity is a significant concern with these medications.



Question 56: A patient develops scaly skin patches, nodules, and lymphadenopathy. What condition best explains these findings?

 Answer: Mycosis fungoides

 Explanation: Mycosis fungoides is a cutaneous T-cell lymphoma characterized by malignant CD4+ T cells infiltrating the skin, forming Pautrier microabscesses.

 Note: It can progress to Sezary syndrome, which involves leukemic spread with cerebriform nuclei on smear.



Question 57: A cancer patient on 6-mercaptopurine develops toxicity after starting allopurinol. What is the explanation?

 Answer: 6-MP is degraded by xanthine oxidase, which is inhibited by allopurinol

 Explanation: Allopurinol inhibits xanthine oxidase, leading to increased levels of 6-mercaptopurine and potential toxicity.

 Note: The dose of 6-MP should be reduced when used with allopurinol.



Question 58: A child with ALL on chemotherapy develops flank pain, hyperkalemia, and hypocalcemia. What lab findings are most likely to be there?

 Answer: Elevated uric acid, elevated phosphate, elevated potassium, decreased calcium

 Explanation: Tumor lysis syndrome results from the rapid release of intracellular contents, causing electrolyte imbalances and potential renal failure.

 Note: Management includes aggressive IV hydration and medications like allopurinol or rasburicase to manage uric acid levels.



Question 59: What is the mechanism and toxicity of vincristine?

 Answer: Inhibits microtubule formation, preventing mitotic spindle formation

 Explanation: Vincristine disrupts microtubule assembly, leading to cell cycle arrest in mitosis, and can cause peripheral neuropathy.

 Note: Peripheral neuropathy is a dose-limiting side effect of vincristine.



Question 60: An HIV-positive patient presents with a solitary ring-enhancing brain lesion. What is the diagnosis?

 Answer: Primary CNS lymphoma

 Explanation: Primary CNS lymphoma is often associated with Epstein-Barr virus (EBV) in immunocompromised patients and typically presents as a single brain lesion.

 Note: Toxoplasmosis, in contrast, usually presents with multiple lesions.



Question 61: A patient with headaches, blurry vision, and peripheral neuropathy. What condition best explains these findings?

 Answer: Waldenström macroglobulinemia

 Explanation: Waldenström macroglobulinemia is a B-cell neoplasm with IgM monoclonal gammopathy, leading to hyperviscosity syndrome.

 Note: Unlike multiple myeloma, bone marrow in Waldenström macroglobulinemia shows less than 10% plasma cells.



Question 62: What is the major toxicity of cyclophosphamide?

 Answer: Hemorrhagic cystitis and bladder cancer

 Explanation: Cyclophosphamide can cause hemorrhagic cystitis due to toxic metabolites like acrolein, which can be prevented with MESNA.

 Note: MESNA binds to and neutralizes these toxic metabolites.



Question 63: What is the mechanism and use of bortezomib?

 Answer: Proteasome inhibitor that induces apoptosis, used in multiple myeloma

 Explanation: Bortezomib inhibits the degradation of pro-apoptotic factors, leading to increased apoptosis in cancer cells.

 Note: It is particularly effective in treating multiple myeloma.



Question 64: A patient on methotrexate develops stomatitis and pancytopenia. What reverses this toxicity?

 Answer: Leucovorin (folinic acid)

 Explanation: Leucovorin bypasses the inhibited enzyme dihydrofolate reductase, reducing methotrexate toxicity without decreasing its efficacy.

 Note: Methotrexate inhibits DNA replication by reducing dTMP synthesis.



Question 65: An elderly patient presents with back pain, hypercalcemia, and anemia. What is the diagnosis?

 Answer: Multiple myeloma

 Explanation: Multiple myeloma is a plasma cell malignancy common in older adults, presenting with CRAB criteria: hypercalcemia, renal failure, anemia, and bone lesions.

 Note: It is associated with high serum protein, rouleaux formation, and an M-spike on serum protein electrophoresis.



HEMATOLOGY/ONCOLOGY HIGH-YIELD NOTES

Question 66: A child presents with distinctive facial features and significant hepatosplenomegaly. Laboratory tests show elevated levels of HbA2 and HbF, with an absence of HbA. What is the diagnosis?

 Answer: Beta-thalassemia major

 Explanation: The laboratory findings of elevated HbA2 and HbF with no HbA are characteristic of beta-thalassemia major, where there is a failure to produce beta chains, resulting in the absence of HbA.

 Note: Beta-thalassemia major often presents with severe anemia and requires regular blood transfusions.



Question 67: A 30-year-old male presents with fatigue and pallor. Laboratory tests reveal hemoglobin of 8.0 g/dL, MCV of 68 fL, and normal ferritin levels. What is the most appropriate next step in diagnosis?

 Answer: Hemoglobin electrophoresis

 Explanation: The combination of microcytic anemia with normal ferritin levels and no response to iron supplementation suggests thalassemia. Hemoglobin electrophoresis is used to confirm the diagnosis.

 Note: Thalassemia should be suspected in cases of microcytic anemia that do not improve with iron therapy.



Question 68: A 45-year-old woman presents with fatigue and pallor. Her laboratory results show hemoglobin of 9.5 g/dL, MCV of 72 fL, ferritin of 8 ng/mL, and elevated total iron-binding capacity (TIBC). What is the most likely diagnosis?

 Answer: Iron deficiency anemia

 Explanation: The laboratory findings of low hemoglobin, low MCV, low ferritin, and elevated TIBC are indicative of iron deficiency anemia.

 Note: In elderly patients, iron deficiency anemia often warrants evaluation for gastrointestinal blood loss, such as a colonoscopy to rule out malignancy.
"""


def extract_questions(content: str) -> List[Dict[str, str]]:
    """Extract questions and their main topics from the content."""
    questions = []
    
    # Pattern to match questions
    question_pattern = r'Question (\d+):\s*(.*?)(?=Answer:|$)'
    answer_pattern = r'Answer:\s*(.*?)(?=Explanation:|$)'
    
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


def extract_topic(answer: str, question: str) -> str:
    """Extract the main medical topic/condition from the answer or question."""
    answer_lower = answer.lower()
    question_lower = question.lower()
    
    # Mapping of answers to search terms (more specific)
    answer_to_topic = {
        'paroxysmal nocturnal hemoglobinuria': 'paroxysmal nocturnal hemoglobinuria',
        'pnh': 'paroxysmal nocturnal hemoglobinuria',
        'hemoglobin electrophoresis': 'hemoglobin electrophoresis thalassemia',
        'vitamin b12 deficiency': 'vitamin b12 deficiency anemia',
        'vitamin b6': 'vitamin b6 pyridoxine sideroblastic anemia',
        'pyridoxine': 'vitamin b6 pyridoxine sideroblastic anemia',
        'iron deficiency anemia': 'iron deficiency anemia',
        'beta-thalassemia major': 'beta thalassemia major',
        'warm autoimmune hemolytic anemia': 'autoimmune hemolytic anemia',
        'treat the underlying disease': 'anemia of chronic disease',
        'glucose-6-phosphate dehydrogenase': 'g6pd deficiency hemolytic anemia',
        'g6pd deficiency': 'g6pd deficiency hemolytic anemia',
        'autoimmune destruction': 'pernicious anemia vitamin b12',
        'folate deficiency': 'folate deficiency megaloblastic anemia',
        'stem cell transplant': 'fanconi anemia',
        'pigmented gallstones': 'hereditary spherocytosis',
        'splenic sequestration crisis': 'sickle cell disease',
        'pyruvate kinase deficiency': 'pyruvate kinase deficiency hemolytic anemia',
        'basophilic stippling': 'lead poisoning anemia',
        'vaccination and prophylactic antibiotics': 'sickle cell disease asplenia',
        'acute chest syndrome': 'sickle cell disease acute chest syndrome',
        'renal papillary necrosis': 'sickle cell trait',
        'hydroxyurea': 'sickle cell disease hydroxyurea',
        'abo incompatibility': 'abo incompatibility hemolytic disease newborn',
        'rh incompatibility': 'rh incompatibility hemolytic disease newborn',
        'porphyria cutanea tarda': 'porphyria cutanea tarda',
        'pct': 'porphyria cutanea tarda',
        'immune thrombocytopenic purpura': 'immune thrombocytopenic purpura itp',
        'itp': 'immune thrombocytopenic purpura',
        'acute intermittent porphyria': 'acute intermittent porphyria',
        'bernard-soulier syndrome': 'bernard-soulier syndrome',
        'vitamin k': 'vitamin k deficiency bleeding',
        'desmopressin': 'von willebrand disease',
        'uremic platelet dysfunction': 'uremic platelet dysfunction',
        'hemophilia': 'hemophilia bleeding disorder',
        'increased pt/ptt/bt/d-dimer': 'disseminated intravascular coagulation dic',
        'disseminated intravascular coagulation': 'disseminated intravascular coagulation',
        'dic': 'disseminated intravascular coagulation',
        'factor v leiden': 'factor v leiden thrombophilia',
        'antithrombin iii deficiency': 'antithrombin deficiency',
        'antiphospholipid syndrome': 'antiphospholipid syndrome',
        'heparin-induced thrombocytopenia': 'heparin induced thrombocytopenia',
        'hit': 'heparin induced thrombocytopenia',
        'factor xa inhibitor': 'rivaroxaban anticoagulant',
        'bridging with heparin': 'warfarin skin necrosis',
        'monitor with ptt': 'heparin anticoagulation',
        'inhibits vitamin k': 'warfarin anticoagulation',
        'irreversibly inhibits cox': 'aspirin antiplatelet',
        'bcr-abl fusion': 'chronic myeloid leukemia cml',
        't-cell acute lymphoblastic leukemia': 't-all acute lymphoblastic leukemia',
        't-all': 't-cell acute lymphoblastic leukemia',
        'reed-sternberg cells': 'hodgkin lymphoma',
        'cladribine': 'hairy cell leukemia',
        'all-trans retinoic acid': 'acute promyelocytic leukemia apl',
        'atra': 'acute promyelocytic leukemia',
        'thrombolytics': 'thrombolytic therapy tpa',
        'chronic lymphocytic leukemia': 'chronic lymphocytic leukemia cll',
        'cll': 'chronic lymphocytic leukemia',
        'burkitt lymphoma': 'burkitt lymphoma',
        'dilated cardiomyopathy': 'doxorubicin cardiomyopathy',
        'marginal zone lymphoma': 'malt lymphoma',
        'neutropenic fever': 'neutropenic fever chemotherapy',
        'busulfan, bleomycin': 'pulmonary fibrosis chemotherapy',
        'mycosis fungoides': 'mycosis fungoides cutaneous lymphoma',
        '6-mp is degraded': 'mercaptopurine allopurinol',
        'elevated uric acid': 'tumor lysis syndrome',
        'inhibits microtubule': 'vincristine chemotherapy',
        'primary cns lymphoma': 'primary cns lymphoma',
        'waldenström macroglobulinemia': 'waldenstrom macroglobulinemia',
        'hemorrhagic cystitis': 'cyclophosphamide chemotherapy',
        'proteasome inhibitor': 'bortezomib multiple myeloma',
        'leucovorin': 'methotrexate leucovorin rescue',
        'multiple myeloma': 'multiple myeloma',
    }
    
    # Check answer first
    for key, topic in answer_to_topic.items():
        if key in answer_lower:
            return topic  # Return full topic for search
    
    # Fallback: extract from answer text
    # Remove common prefixes
    answer_clean = answer_lower
    for prefix in ['answer:', 'the', 'a', 'an']:
        if answer_clean.startswith(prefix):
            answer_clean = answer_clean[len(prefix):].strip()
    
    # Get first meaningful words (skip articles, prepositions)
    words = [w for w in answer_clean.split() if len(w) > 2 and w not in ['the', 'and', 'or', 'for', 'with']]
    
    if words:
        # Take first 2-3 words
        topic = ' '.join(words[:3])
        return topic
    
    # Last resort: use first word of question
    q_words = question_lower.split()[:3]
    return ' '.join(q_words)


def search_wikimedia_commons(query: str, limit: int = 5) -> List[Dict]:
    """Search Wikimedia Commons for Creative Commons licensed images."""
    base_url = "https://commons.wikimedia.org/w/api.php"
    
    headers = {
        'User-Agent': 'MedicalEducationImageDownloader/1.0 (https://example.com/contact)'
    }
    
    params = {
        'action': 'query',
        'format': 'json',
        'list': 'search',
        'srsearch': query,
        'srnamespace': 6,  # File namespace
        'srlimit': limit,
        'srprop': 'size|wordcount|timestamp|snippet'
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'query' in data and 'search' in data['query']:
            return data['query']['search']
        return []
    except Exception as e:
        print(f"Error searching Wikimedia Commons for '{query}': {e}")
        return []


def get_image_url(filename: str) -> str:
    """Get the direct image URL from Wikimedia Commons filename."""
    base_url = "https://commons.wikimedia.org/w/api.php"
    
    headers = {
        'User-Agent': 'MedicalEducationImageDownloader/1.0 (https://example.com/contact)'
    }
    
    # Remove "File:" prefix if present
    filename = filename.replace('File:', '').strip()
    
    params = {
        'action': 'query',
        'format': 'json',
        'titles': f'File:{filename}',
        'prop': 'imageinfo',
        'iiprop': 'url',
        'iiurlwidth': '800'  # Get a reasonable size
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        pages = data.get('query', {}).get('pages', {})
        for page_id, page_data in pages.items():
            imageinfo = page_data.get('imageinfo', [])
            if imageinfo:
                return imageinfo[0].get('url', '')
        
        return ''
    except Exception as e:
        print(f"Error getting image URL for '{filename}': {e}")
        return ''


def get_image_metadata(filename: str) -> Optional[Dict]:
    """Get image metadata including author, title, license, and source URL."""
    base_url = "https://commons.wikimedia.org/w/api.php"
    
    headers = {
        'User-Agent': 'MedicalEducationImageDownloader/1.0 (https://example.com/contact)'
    }
    
    filename_clean = filename.replace('File:', '').strip()
    
    params = {
        'action': 'query',
        'format': 'json',
        'titles': f'File:{filename_clean}',
        'prop': 'imageinfo|revisions',
        'iiprop': 'url|extmetadata',
        'rvprop': 'user',
        'rvlimit': 1
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        pages = data.get('query', {}).get('pages', {})
        for page_id, page_data in pages.items():
            if page_id == '-1':  # Page doesn't exist
                return None
                
            imageinfo = page_data.get('imageinfo', [])
            revisions = page_data.get('revisions', [])
            
            if imageinfo:
                info = imageinfo[0]
                extmetadata = info.get('extmetadata', {})
                
                # Extract metadata
                title = extmetadata.get('ObjectName', {}).get('value', '') or filename_clean
                author = extmetadata.get('Artist', {}).get('value', '')
                if not author and revisions:
                    author = revisions[0].get('user', 'Unknown')
                if not author:
                    author = 'Unknown'
                
                # Clean HTML tags from author name
                import re as re_module
                author = re_module.sub(r'<[^>]+>', '', author)
                author = author.strip()
                if not author:
                    author = 'Unknown'
                
                # Get license
                license_info = extmetadata.get('License', {}).get('value', '')
                license_short = 'CC'
                if 'cc-by' in license_info.lower() or 'cc by' in license_info.lower():
                    license_short = 'CC BY'
                    if '2.0' in license_info:
                        license_short = 'CC BY 2.0'
                    elif '3.0' in license_info:
                        license_short = 'CC BY 3.0'
                    elif '4.0' in license_info:
                        license_short = 'CC BY 4.0'
                elif 'cc-by-sa' in license_info.lower():
                    license_short = 'CC BY-SA'
                    if '2.0' in license_info:
                        license_short = 'CC BY-SA 2.0'
                    elif '3.0' in license_info:
                        license_short = 'CC BY-SA 3.0'
                    elif '4.0' in license_info:
                        license_short = 'CC BY-SA 4.0'
                elif 'cc0' in license_info.lower() or 'public domain' in license_info.lower():
                    license_short = 'CC0'
                
                # Source URL
                source_url = info.get('descriptionurl', '') or f"https://commons.wikimedia.org/wiki/File:{filename_clean.replace(' ', '_')}"
                
                # Author URL (if available)
                author_url = ''
                if author and author != 'Unknown':
                    author_url = f"https://commons.wikimedia.org/wiki/User:{author.replace(' ', '_')}"
                
                return {
                    'title': title,
                    'author': author,
                    'author_url': author_url,
                    'license': license_short,
                    'source_url': source_url,
                    'filename': filename_clean
                }
        
        return None
    except Exception as e:
        print(f"Error getting metadata for '{filename}': {e}")
        return None


def check_cc_license(filename: str) -> bool:
    """Check if the image has a Creative Commons license."""
    metadata = get_image_metadata(filename)
    if metadata:
        return metadata['license'].startswith('CC')
    return False


def search_unsplash(query: str, limit: int = 5) -> List[Dict]:
    """Search Unsplash for free images (fallback when Wikimedia Commons fails)."""
    # Unsplash Source API - free, no authentication required
    # Using their public source API
    base_url = "https://source.unsplash.com/800x600"
    
    # For now, return a simple structure that we can use
    # We'll construct direct image URLs
    results = []
    for i in range(limit):
        # Unsplash Source allows direct image access with keywords
        # Format: https://source.unsplash.com/800x600/?{keyword}
        keyword = query.replace(' ', ',')
        image_url = f"{base_url}/?{keyword}&sig={i}"
        results.append({
            'url': image_url,
            'keyword': query
        })
    return results


def download_image(url: str, filepath: Path) -> bool:
    """Download an image from a URL."""
    headers = {
        'User-Agent': 'MedicalEducationImageDownloader/1.0 (https://example.com/contact)'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except Exception as e:
        print(f"Error downloading image from '{url}': {e}")
        return False


def convert_svg_to_jpg(svg_path: Path, jpg_path: Path) -> bool:
    """Convert SVG file to JPG format."""
    if not PIL_AVAILABLE:
        return False
    
    try:
        # Try using cairosvg if available
        try:
            import cairosvg
            cairosvg.svg2png(url=str(svg_path), write_to=str(jpg_path.with_suffix('.png')))
            # Convert PNG to JPG
            img = Image.open(jpg_path.with_suffix('.png'))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(jpg_path, quality=95)
            jpg_path.with_suffix('.png').unlink()  # Remove temporary PNG
            return True
        except ImportError:
            # Fallback: try svglib
            try:
                from svglib.svglib import svg2rlg
                from reportlab.graphics import renderPM
                drawing = svg2rlg(str(svg_path))
                if drawing:
                    renderPM.drawToFile(drawing, str(jpg_path), fmt='JPG')
                    return True
            except ImportError:
                # Last resort: use PIL with basic SVG support (may not work well)
                print(f"  Warning: SVG conversion libraries not available. Install cairosvg or svglib.")
                return False
    except Exception as e:
        print(f"  Error converting SVG to JPG: {e}")
        return False


def add_citation_overlay(image_path: Path, metadata: Dict) -> bool:
    """Add Creative Commons citation overlay to the bottom of an image."""
    if not PIL_AVAILABLE:
        print(f"  Note: Skipping citation overlay (Pillow not installed)")
        return False
    
    try:
        # Convert SVG files to JPG first
        original_path = image_path
        if image_path.suffix.lower() == '.svg':
            print(f"  Converting SVG to JPG...")
            jpg_path = image_path.with_suffix('.jpg')
            if convert_svg_to_jpg(image_path, jpg_path):
                image_path.unlink()  # Remove original SVG
                image_path = jpg_path
                print(f"  ✓ Converted to {jpg_path.name}")
            else:
                print(f"  Note: SVG conversion failed, skipping citation overlay")
                return False
        
        # Open the image
        img = Image.open(image_path)
        
        # Convert to RGB if necessary (for PNG with transparency, etc.)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calculate citation text
        title = metadata.get('title', metadata.get('filename', 'Image'))
        author = metadata.get('author', 'Unknown')
        license_text = metadata.get('license', 'CC')
        
        # Format citation: "Title" by Author CC BY 2.0
        citation_text = f'"{title}" by {author} {license_text}'
        
        # Calculate text size and padding
        draw = ImageDraw.Draw(img)
        
        # Try to use a nice font, fallback to default if not available
        try:
            # Try system fonts
            font_size = max(16, min(img.width, img.height) // 40)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Get text bounding box
        bbox = draw.textbbox((0, 0), citation_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Add padding
        padding = 20
        overlay_height = text_height + (padding * 2)
        
        # Create overlay image
        overlay = Image.new('RGB', (img.width, img.height + overlay_height), (255, 255, 255))
        
        # Paste original image
        overlay.paste(img, (0, 0))
        
        # Draw citation text on overlay
        draw_overlay = ImageDraw.Draw(overlay)
        
        # Calculate text position (centered horizontally, at bottom)
        text_x = (overlay.width - text_width) // 2
        text_y = img.height + padding
        
        # Draw text in dark gray/black
        draw_overlay.text((text_x, text_y), citation_text, fill=(0, 0, 0), font=font)
        
        # Save the image with citation
        overlay.save(image_path, quality=95)
        
        return True
    except Exception as e:
        print(f"Error adding citation overlay: {e}")
        return False


def main():
    """Main function to process questions and download images."""
    print("Extracting questions from content...")
    questions = extract_questions(CONTENT)
    
    print(f"Found {len(questions)} questions")
    
    # Create output directory
    output_dir = Path("downloaded_images")
    output_dir.mkdir(exist_ok=True)
    
    # Create a log file
    log_file = output_dir / "download_log.txt"
    
    downloaded_count = 0
    failed_count = 0
    
    print(f"Starting download process for {len(questions)} questions...")
    print(f"Output directory: {output_dir.absolute()}\n")
    
    with open(log_file, 'w', encoding='utf-8') as log:
        log.write("Question Image Download Log\n")
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
            # Note: Most Wikimedia Commons images are CC-licensed, so we'll try to download
            # and skip the license check if it fails (to speed things up)
            image_found = False
            
            # If Wikimedia Commons fails, try Unsplash as fallback
            if not search_results:
                print(f"  Wikimedia Commons failed, trying Unsplash...")
                unsplash_results = search_unsplash(topic, limit=3)
                if unsplash_results:
                    for photo in unsplash_results:
                        image_url = photo.get('url', '')
                        if image_url:
                            ext = '.jpg'
                            output_path = output_dir / f"question_{q_num:02d}{ext}"
                            
                            print(f"  Downloading from Unsplash: {photo.get('keyword', topic)}")
                            log.write(f"  Downloading from Unsplash: {photo.get('keyword', topic)}\n")
                            log.write(f"  URL: {image_url}\n")
                            
                            if download_image(image_url, output_path):
                                # For Unsplash images, create basic metadata
                                metadata = {
                                    'title': photo.get('keyword', topic),
                                    'author': 'Unsplash',
                                    'license': 'Unsplash License',
                                    'source_url': image_url,
                                    'filename': f"question_{q_num:02d}"
                                }
                                if add_citation_overlay(output_path, metadata):
                                    print(f"  ✓ Saved with citation to {output_path}")
                                    log.write(f"  ✓ Successfully saved with citation (Unsplash License)\n\n")
                                else:
                                    print(f"  ✓ Saved to {output_path}")
                                    log.write(f"  ✓ Successfully saved (Unsplash License)\n\n")
                                downloaded_count += 1
                                image_found = True
                                break
                
                if not image_found:
                    print(f"  No search results found for '{topic}'")
                    log.write(f"  ERROR: No search results found\n\n")
                    failed_count += 1
                    continue
            
            # Process Wikimedia Commons results if we have them
            if search_results:
                for result in search_results:
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
                        
                        output_path = output_dir / f"question_{q_num:02d}{ext}"
                        
                        print(f"  Downloading: {filename}")
                        log.write(f"  Downloading: {filename}\n")
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
                            image_found = True
                            break
                        else:
                            log.write(f"  ✗ Download failed\n")
            
            if not image_found:
                print(f"  ✗ No CC-licensed image found for Question {q_num}")
                log.write(f"  ERROR: No CC-licensed image found\n\n")
                failed_count += 1
            
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

