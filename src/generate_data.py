import csv
import os
import random
from datetime import datetime, timedelta

random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CONDITIONS = [
    ("Type 2 Diabetes", "Patient shows elevated HbA1c and fasting blood glucose; prescribed glycemic control protocol."),
    ("Hypertension", "Patient has persistent elevated blood pressure requiring antihypertensive therapy and cardiovascular monitoring."),
    ("Asthma", "Patient experiences reversible airway obstruction and bronchospasm; prescribed bronchodilator inhaler."),
    ("Depression", "Patient reports persistent major depressive symptoms; enrolled in behavioral therapy and SSRI regimen."),
    ("Osteoarthritis", "Patient exhibits degenerative joint cartilage wear and stiffness; prescribed anti-inflammatory therapy."),
    ("Chronic Kidney Disease", "Patient shows reduced eGFR and proteinuria requiring nephroprotective monitoring."),
    ("Breast Cancer", "Early-stage HER2-negative carcinoma scheduled for targeted oncology protocol."),
    ("Melanoma", "Cutaneous malignant lesion identified; candidate for checkpoint immunotherapy."),
]

CLINICAL_TRIALS = [
    ("CT-2026-001", "GLP-1 + SGLT2 Dual Metabolic Remission Study", "Type 2 Diabetes", 65, "Phase III",
     "Adults aged 18-65 diagnosed with Type 2 Diabetes on Metformin seeking improved glycemic and renal outcomes."),
    ("CT-2026-002", "Next-Gen Continuous Glucose & Insulin Loop Trial", "Type 2 Diabetes", 50, "Phase II",
     "Patients under 50 with Type 2 Diabetes requiring automated glycemic titration."),
    ("CT-2026-003", "Resistant Hypertension Renal Denervation Trial", "Hypertension", 75, "Phase III",
     "Patients with systolic hypertension on Lisinopril or Amlodipine."),
    ("CT-2026-004", "Biologic Anti-IL4R Severe Asthma Protocol", "Asthma", 60, "Phase III",
     "Adults with moderate-to-severe asthma experiencing frequent wheezing despite Albuterol rescue."),
    ("CT-2026-005", "Digital Neuro-Adaptive Behavioral Therapy Study", "Depression", 55, "Phase II",
     "Adults under 55 with major depressive disorder currently treated with SSRIs such as Sertraline."),
    ("CT-2026-006", "Regenerative Intra-Articular Cartilage Hydrogel Trial", "Osteoarthritis", 80, "Phase II",
     "Patients with knee or hip osteoarthritis seeking non-surgical pain and mobility recovery."),
    ("CT-2026-007", "Nephro-Shield Finerenone Progression Prevention Trial", "Chronic Kidney Disease", 70, "Phase III",
     "Patients with Chronic Kidney Disease and comorbid hypertension or diabetes."),
    ("CT-2026-008", "Targeted mRNA Neoantigen Immunotherapy Study", "Melanoma", 75, "Phase II",
     "Patients with resected Stage II/III melanoma or early-stage solid tumors."),
]


def generate_dataset(num_patients=50):
    genders = ["F", "M"]
    zip_codes = ["08001", "08018", "08012", "08028", "08036"]
    condition_to_med = {
        "Type 2 Diabetes": ("Metformin", "500mg"),
        "Hypertension": ("Lisinopril", "20mg"),
        "Asthma": ("Albuterol", "90mcg"),
        "Depression": ("Sertraline", "50mg"),
        "Osteoarthritis": ("Ibuprofen", "400mg"),
        "Chronic Kidney Disease": ("Amlodipine", "10mg"),
        "Breast Cancer": ("Tamoxifen", "20mg"),
        "Melanoma": ("Pembrolizumab", "200mg"),
    }

    patients_rows = []
    diagnoses_rows = []
    medications_rows = []
    d_id = 1
    m_id = 1

    for i in range(1, num_patients + 1):
        p_id = f"P{i:04d}"
        age = random.randint(24, 78)
        gender = random.choice(genders)
        zip_code = random.choice(zip_codes)

        chosen = random.sample(CONDITIONS, k=random.choice([1, 2]))
        cond_names = ", ".join(c[0] for c in chosen)
        desc = f"{age}-year-old {gender} patient (postal code {zip_code}) with documented history of {cond_names}."

        patients_rows.append([p_id, f"Patient_{i:03d}", age, gender, zip_code, desc])

        for cond_name, cond_desc in chosen:
            diag_date = (datetime.now() - timedelta(days=random.randint(15, 340))).strftime("%Y-%m-%d")
            diagnoses_rows.append([f"D{d_id:04d}", p_id, cond_name, diag_date, cond_desc])
            d_id += 1

            drug, dosage = condition_to_med[cond_name]
            medications_rows.append([
                f"M{m_id:04d}",
                p_id,
                drug,
                dosage,
                f"Prescribed {drug} ({dosage}) for {cond_name} starting {diag_date}.",
            ])
            m_id += 1

    with open(os.path.join(OUTPUT_DIR, "patients.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["patient_id", "name", "age", "gender", "zip_code", "description"])
        w.writerows(patients_rows)

    with open(os.path.join(OUTPUT_DIR, "diagnoses.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["diagnosis_id", "patient_id", "condition", "date", "description"])
        w.writerows(diagnoses_rows)

    with open(os.path.join(OUTPUT_DIR, "medications.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["medication_id", "patient_id", "medication", "dosage", "description"])
        w.writerows(medications_rows)

    with open(os.path.join(OUTPUT_DIR, "clinical_trials.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["trial_id", "title", "target_condition", "max_age", "phase", "eligibility_criteria"])
        w.writerows(CLINICAL_TRIALS)

    print(f"Generated {len(patients_rows)} patients, {len(diagnoses_rows)} diagnoses, "
          f"{len(medications_rows)} medications, and {len(CLINICAL_TRIALS)} clinical trials in '{OUTPUT_DIR}'.")
    print("Note: Real 768-dimensional vector embeddings are computed inside the K8s cluster via Ollama (nomic-embed-text) during 03-data-hydration-job.yaml.")


if __name__ == "__main__":
    generate_dataset(50)
