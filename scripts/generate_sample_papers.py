"""Script to generate realistic synthetic benchmark research papers for local evaluation and demos."""
from pathlib import Path
import fitz

PAPER_1_TEXT = """
Deep Convolutional Neural Networks for Glioblastoma MRI Segmentation
Authors: Dr. Elizabeth Chen, Dr. Marcus Vance, Dr. Arthur Dent
Publication Year: 2023
Published in: Journal of Medical Imaging and AI (Synthetic Academic Corpus)

Abstract:
Glioblastoma multiforme (GBM) remains one of the most aggressive and heterogeneous cerebral malignancies. 
In this study, we propose an optimized 3D U-Net convolutional architecture with residual connections (Res-UNet-3D) 
for multi-modal brain tumor segmentation. We evaluate our approach on the BraTS 2021 benchmark dataset comprising 
1,251 multi-parametric magnetic resonance imaging (mpMRI) scans.

Methodology:
The proposed model utilizes deep encoder-decoder paths with strided 3D convolutions and squeeze-and-excitation 
attention modules. Preprocessing involves skull stripping, N4 bias field correction, and intensity normalization 
to zero mean and unit variance. Training is performed using a hybrid loss combining Soft Dice and Focal Loss.

Experimental Results and Findings:
On the held-out validation cohort (N = 250 scans), our Res-UNet-3D architecture achieved a mean Dice similarity 
coefficient of 93.8% for the whole tumor (WT), 89.4% for the tumor core (TC), and 85.2% for enhancing tumor (ET). 
Mean 95th percentile Hausdorff Distance (HD95) was 4.1 mm. The model demonstrated rapid convergence within 120 epochs.

Author-Acknowledged Limitations:
Despite high segmentation precision, performance degrades on low-field 1.5T scanners not represented in the training cohort. 
Furthermore, boundary delineation remains ambiguous in cases with severe peritumoral edema, and the model requires 
significant GPU memory during 3D patch inference.
"""

PAPER_2_TEXT = """
Vision Transformers for Multi-Modal Neuroimaging and Brain Lesion Delineation
Authors: Dr. Sanjay Gupta, Dr. Elena Rostova
Publication Year: 2024
Published in: Advances in Neural Computing (Synthetic Academic Corpus)

Abstract:
While Convolutional Neural Networks (CNNs) have dominated biomedical image segmentation, their local receptive fields 
limit their ability to model long-range spatial correlations across multi-slice MRI volumes. We introduce TransNeuro, 
a pure Vision Transformer (ViT) architecture incorporating shifted-window self-attention for brain tumor boundary estimation.

Methodology:
TransNeuro tokenizes 3D MRI patches and projects them into high-dimensional latent representations. Cross-attention layers 
fuse T1, T1-contrast, T2, and FLAIR modalities prior to token decoding. We trained TransNeuro on the BraTS 2021 dataset 
using self-supervised masked autoencoder pretraining followed by supervised fine-tuning.

Experimental Results and Findings:
TransNeuro achieved a Dice similarity coefficient of 92.4% on the whole tumor, 88.1% on the tumor core, and 84.7% on enhancing tumor. 
Although its Dice score is slightly lower than residual CNNs on small focal lesions, TransNeuro demonstrated superior boundary continuity 
and reduced false positive detections in distant cortical regions. Inference throughput was measured at 18 scans per minute on an NVIDIA A100.

Author-Acknowledged Limitations:
Vision Transformers require substantial pretraining datasets to avoid overfitting. The computational complexity scales quadratically 
with sequence length, creating latency bottlenecks for high-resolution volumetric scans without specialized hardware acceleration.
"""

PAPER_3_TEXT = """
Comparative Benchmark of Deep Architectures and Domain Adaptation in Brain Tumor MRI
Authors: Dr. Michael Thorne, Dr. Sarah Jenkins
Publication Year: 2024
Published in: International Review of Computational Oncology (Synthetic Academic Corpus)

Abstract:
Clinical translation of artificial intelligence in neuro-oncology requires robust generalization across heterogeneous hospital imaging protocols. 
We perform an extensive comparative benchmark of convolutional architectures versus transformer hybrids across 1,500 patient scans, 
evaluating sensitivity to scanner vendor differences and contrast dosage variations.

Methodology and Benchmark Protocol:
We implemented ResNet-3D, Swin-UNet, and TransNeuro under identical cross-validation splits. Standardized preprocessing and automated metric 
computation were executed across Siemens 3T, GE 1.5T, and Philips 3T scanners.

Comparative Findings:
1. Architectural Efficacy: Hybrid CNN-Transformer models yielded the highest overall composite Dice score (94.1%), combining local edge sensitivity with global context.
2. Cross-Scanner Discrepancy: All evaluated architectures exhibited a 4.5% to 7.2% Dice reduction when transferred to external 1.5T scanners without fine-tuning.
3. Consensus: Attention mechanisms consistently improve necrotic core delineation compared to standard convolutional filters.

Candidate Research Gaps:
A critical gap observed across literature is the lack of standardized uncertainty calibration. Most current papers report point estimates 
of Dice coefficients without confidence intervals or out-of-distribution detection flags, limiting clinical trust in borderline cases.
"""


def generate_papers():
    output_dir = Path("data/sample_papers")
    output_dir.mkdir(parents=True, exist_ok=True)

    papers = [
        ("chen_2023_deep_cnn_glioma.pdf", PAPER_1_TEXT),
        ("gupta_2024_vision_transformers_neuro.pdf", PAPER_2_TEXT),
        ("thorne_2024_comparative_benchmark_mri.pdf", PAPER_3_TEXT),
    ]

    for fname, text in papers:
        doc = fitz.open()
        p = doc.new_page()
        p.insert_text((40, 50), text.strip(), fontsize=10)
        out_path = output_dir / fname
        doc.save(str(out_path))
        doc.close()
        print(f"Generated sample paper: {out_path}")


if __name__ == "__main__":
    generate_papers()
