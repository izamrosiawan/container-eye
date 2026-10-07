# container-eye

A production-grade computer vision system and empirical deep learning research framework for multi-class physical shipping container damage detection in port logistics gate areas using YOLOv8.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)]()
[![Model: YOLOv8](https://img.shields.io/badge/model-YOLOv8%20(Nano%20%7C%20Small)-purple.svg)]()
[![Dataset: 1,038 Images](https://img.shields.io/badge/dataset-1%2C038%20images%20%7C%204%2C346%20boxes-orange.svg)]()
[![Protocol: Group--Split Anti--Leakage](https://img.shields.io/badge/split-group--based%20anti--leakage-green.svg)]()
[![Standard: IICL--6](https://img.shields.io/badge/maritime--standard-IICL--6-teal.svg)]()

---

## Architecture Overview

`	ext
container-eye/
├── assets/                  # UI assets and sound alerts
├── models/                  # Pretrained and fine-tuned YOLOv8 weights (.pt)
├── src/                     # Core application source code
│   ├── detector.py          # YOLOv8 inference engine and bounding box parser
│   └── camera_stream.py     # RTSP/Webcam/Video frame capture handler
├── app_gui.py               # Real-time CCTV gate monitoring dashboard (Tkinter/OpenCV)
├── config.py                # System thresholds and camera stream configuration
├── main.py                  # CLI and GUI entrypoint launcher
├── notebook.ipynb           # Canonical 4-scenario Colab training & evaluation pipeline
├── requirements.txt         # Project runtime dependencies
└── README.md                # System documentation and empirical benchmarks
`

---

## Research & Experimental Design

This repository hosts the empirical comparative study evaluating accuracy-latency trade-offs across YOLOv8 variants and quantifying the false positive reduction achieved by injecting normal container background images (hard negative mining).

### 1. Dataset Specification

* **Damaged Container Images**: 821 images (4,346 annotated bounding boxes).
  * Dent: 2,010 boxes (46.2%)
  * Rust: 1,517 boxes (34.9%)
  * Hole: 664 boxes (15.3%)
  * Deframe: 155 boxes (3.6%)
* **Negative Background Samples**: 217 normal container images (injected exclusively into the training set).
* **Total Population**: 1,038 images.
* **Leakage Prevention**: Evaluated via perceptual hashing (dHash, Hamming distance <= 6) to construct 727 connected-component groups. Partitioned into:
  * **Train Set**: 574 damaged + 217 background = 791 images (2,948 boxes)
  * **Validation Set**: 164 damaged images (913 boxes)
  * **Test Set**: 83 damaged images (485 boxes, including 16 Deframe boxes)

### 2. Four Experimental Scenarios (Isovolume 791 Images)

| Scenario | Model Architecture | Training Data Composition | Volume | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **S1 (Baseline Control)** | YOLOv8n | 574 damaged original | 574 images | Benchmark lightweight detector on pure defect set. |
| **S2 (Volume Control)** | YOLOv8n | 574 damaged + 217 offline geometric augmentations | 791 images | Control data volume strictly via spatial augmentation. |
| **S3 (Hard Negative Mining)** | YOLOv8n | 574 damaged + 217 normal background images | 791 images | Quantify semantic negative context on false positive suppression. |
| **S4 (Model Scaling)** | YOLOv8s | 574 damaged + 217 normal background images | 791 images | Measure parameter scaling and edge latency trade-off. |

---

## Empirical Benchmark Results (Test Set, 83 Images)

Evaluation evaluated under single-seed anchor run (seed=42, IoU=0.5, conf=0.25):

| Scenario | Model | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 | Dent | Rust | Hole | Deframe | GPU Latency | CPU Latency |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **S1** | YOLOv8n | 0.5419 | 0.2827 | **0.2443** | 0.1362 | 0.1419 | 0.0688 | 0.4314 | 0.3350 | - | - |
| **S2** | YOLOv8n | 0.6422 | 0.2788 | **0.2170** | 0.1014 | 0.1424 | 0.0887 | 0.3705 | 0.2662 | - | - |
| **S3** | YOLOv8n | 0.5419 | 0.2827 | **0.2443** | 0.1362 | 0.1419 | 0.0688 | 0.4314 | 0.3350 | 16.59 ms (60.3 FPS) | 122.86 ms (8.1 FPS) |
| **S4** | YOLOv8s | 0.5048 | 0.4009 | **0.3198** | 0.1619 | 0.2391 | 0.1546 | 0.4078 | **0.4775** | 22.55 ms (44.4 FPS) | 287.58 ms (3.5 FPS) |

---

## Getting Started

### Installation

Clone the repository and install dependencies:
`ash
git clone https://github.com/izamrosiawan/container-eye.git
cd container-eye
pip install -r requirements.txt
`

### Running Gate Inspection Dashboard

Launch the interactive CCTV defect inspector:
`ash
python main.py
`

### Reproducing Training & Evaluation

Open and execute 
otebook.ipynb directly in Google Colab with GPU acceleration (Tesla T4 or higher):
1. Mount Google Drive containing the partitioned dataset.
2. Run all cells sequentially to reproduce S1-S4 training, test validation, and edge latency benchmarks.

---

## Citation & Author

* **Author**: Izam Rosiawan (NIM: 103102400049)
* **Program**: S1 Data Science, Telkom University Surabaya
* **Research Focus**: Computer Vision, Maritime Logistics, Edge Computing
