# ResearchPilot Demo Walkthrough Script

This script walks through an end-to-end presentation of ResearchPilot using the generated benchmark academic papers.

---

## Preparation (2 minutes)
1. Ensure the application is running:
   ```bash
   docker compose up -d
   # OR start API, worker, and frontend locally
   ```
2. Verify sample papers exist in `data/sample_papers/`:
   - `chen_2023_deep_cnn_glioma.pdf`
   - `gupta_2024_vision_transformers_neuro.pdf`
   - `thorne_2024_comparative_benchmark_mri.pdf`
   *(If not present, run `python scripts/generate_sample_papers.py`)*

---

## Step 1: Registration & Workspace Creation
1. Open browser at `http://localhost:5173`.
2. Click **Get Started** and register a demo account:
   - Name: `Dr. Alex Morgan`
   - Email: `alex.morgan@stanford.edu`
   - Password: `AcademicReview2024!`
3. In the Dashboard, click **New Research Project**:
   - Title: `Deep Learning in Brain Tumor Segmentation`
   - Description: `Comparative literature review evaluating 3D CNNs versus Vision Transformers on BraTS benchmark.`
4. Click **Create Project**.

---

## Step 2: Uploading Papers & Ingestion
1. Open the created project workspace.
2. Drag and drop all 3 sample PDFs from `data/sample_papers/` into the upload zone.
3. Observe live ingestion status pills transitioning:
   - `uploaded` -> `extracting` -> `chunking` -> `embedding` -> `ready`.
4. Note that file sizes, page counts, and publication years are extracted without hallucination.

---

## Step 3: Posing Research Question & Plan Review
1. Click **Start Literature Review**.
2. Research Question:
   > *"How do Convolutional Neural Networks and Vision Transformers compare in Brain Tumor MRI segmentation accuracy and computational latency?"*
3. Verify that all 3 uploaded papers are selected.
4. Click **Generate & Review Plan**.
5. Inspect the generated plan:
   - Refined research objective.
   - Decomposed sub-questions (model architectures, evaluation metrics, cross-paper gaps).
   - Ordered execution steps and comparability dimensions.
6. Click **Approve & Run Agent**.

---

## Step 4: Observability Timeline & Multi-Step Execution
1. Watch the real-time activity timeline transition across stages:
   - **Retrieval:** Searching the user's paper library with Hybrid Reciprocal Rank Fusion.
   - **Paper Analysis:** Extracting structured methods, datasets, sample sizes, and limitations per paper.
   - **Synthesis:** Drafting comparison matrices and classifying agreements.
   - **Verification:** Grounding claims against chunk IDs and page numbers.

---

## Step 5: Literature Review Report & Grounded Citations
1. Once completed, the UI automatically transitions to the final **Research Report**.
2. Demonstrate core product features:
   - **Executive Summary & Scope:** Transparent overview of the uploaded corpus.
   - **Interactive Citations:** Click any `[1]`, `[2]` citation pill. Point out that it opens the exact excerpt from the source chunk and links to the source PDF.
   - **Methodology Matrix:** Show the comparability tiers (`partially_comparable`) and notes explaining differing protocols.
   - **Agreements & Disagreements:** Point out that differences in scanner field strength (1.5T vs 3.0T) are classified as *contextual differences*, not arbitrary contradictions.
   - **Candidate Research Gaps:** Highlight the clear caveat that gaps are observed strictly within the uploaded corpus.
   - **Export:** Click **Export Report (PDF)** or **Copy Markdown** to show print-ready document generation.
