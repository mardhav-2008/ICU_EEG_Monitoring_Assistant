# ICU EEG Monitoring Assistant

**A Multimodal Deep Learning System for ICU EEG Classification, Analysis, and Continuous Monitoring**

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![PyTorch](https://img.shields.io/badge/PyTorch-2.14-EE4C2C?logo=pytorch)
![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52?logo=qt)
![CUDA](https://img.shields.io/badge/Acceleration-CUDA-76B900?logo=nvidia)
![Status](https://img.shields.io/badge/Status-Research%20Prototype-teal)

---

## Overview

The ICU EEG Monitoring Assistant is a research-oriented system designed to identify potentially harmful brain activity patterns from electroencephalography (EEG) recordings.

The project combines raw EEG signals and EEG-derived spectrograms using a **Residual Attention-Based Multimodal Convolutional Neural Network**. It also incorporates a traditional Random Forest classifier as a baseline for performance comparison.

Beyond classification, the system includes uncertainty estimation, attention-level assessment, temporal event detection, and a desktop graphical interface with interactive 3D anatomical visualization.

The objective is to develop an integrated pipeline that transforms EEG recordings into interpretable classification results and continuous monitoring summaries.

> **Clinical disclaimer:** This project is an experimental research prototype, not a clinically validated medical device. Its predictions must not be used as standalone medical diagnoses or for autonomous clinical decision-making.

---

## Key Features

- **Multimodal EEG Classification:** Combines raw EEG signals and spectrogram representations.
- **Residual CNN Architecture:** Independent 1D and 2D residual encoders for the two input modalities.
- **Attention-Based Fusion:** Uses multi-head attention to combine learned features.
- **Six-Class Classification:** Identifies six categories of harmful brain activity.
- **Random Forest Baseline:** Uses frequency-domain features for traditional machine learning comparison.
- **Uncertainty Estimation:** Evaluates prediction confidence and competition between alternative classes.
- **Attention Assessment:** Assigns monitoring priority based on the predicted pattern, confidence, and uncertainty.
- **Continuous Monitoring:** Processes recordings in overlapping time windows and groups consecutive predictions into events.
- **Event Detection:** Identifies persistent predicted patterns and generates seizure-related review alerts.
- **3D Anatomical Interface:** Interactive male and female anatomical models with holographic visualization.
- **Desktop Dashboard:** EEG waveforms, spectrograms, prediction probabilities, and model interpretation.

---

## System Architecture

```text
                 EEG Recording
                       |
                       v
                Data Preprocessing
                       |
             +---------+---------+
             |                   |
             v                   v
         Raw EEG             Spectrogram
       20 x 2000             4 x 60 x 100
             |                   |
             v                   v
       Residual 1D CNN      Residual 2D CNN
             |                   |
             v                   v
       EEG Features       Spectrogram Features
             |                   |
             +---------+---------+
                       |
                       v
              Attention Fusion
                 8 Heads
                       |
                       v
              Fully Connected
                 Classifier
                       |
                       v
                Six-Class Output
                       |
             +---------+---------+
             |         |         |
             v         v         v
         Prediction Confidence Uncertainty
             |
             v
       Attention Assessment
             |
             v
       Continuous Monitoring
             |
             v
       Event Detection & Alerts
             |
             v
         Desktop GUI
```

---

## Dataset

The project uses the **HMS – Harmful Brain Activity Classification** dataset, hosted on Kaggle.

**Dataset:** https://www.kaggle.com/competitions/hms-harmful-brain-activity-classification

The dataset contains EEG recordings from critically ill patients, annotated by expert reviewers.

### Dataset Statistics

| Attribute | Value |
|---|---:|
| Labelled training rows | 106,800 |
| Unique EEG recordings | 17,089 |
| Unique patients | 1,950 |
| EEG sampling frequency | 200 Hz |
| EEG channels | 20 |
| Classification categories | 6 |

### Classification Categories

| Class | Description |
|---|---|
| Seizure | Seizure-related EEG activity |
| GPD | Generalized Periodic Discharges |
| LRDA | Lateralized Rhythmic Delta Activity |
| Other | Other EEG patterns |
| GRDA | Generalized Rhythmic Delta Activity |
| LPD | Lateralized Periodic Discharges |

The target variable is `expert_consensus`.

### Patient-Level Data Splitting

To reduce patient-level data leakage, the dataset is divided using patient identifiers rather than randomly splitting individual rows.

| Split | Samples |
|---|---:|
| Training | 83,684 |
| Validation | 23,116 |
| Total | 106,800 |

The split uses a fixed random seed of 42.

---

## Data Preprocessing

Two separate preprocessing pipelines prepare the inputs for the multimodal model.

### 1. Raw EEG Processing

Implemented in `src/prepare_data.py`.

Processing steps:

1. Load EEG Parquet recordings.
2. Extract the appropriate recording segment.
3. Select a 10-second EEG window.
4. Handle missing and invalid values.
5. Normalize individual channels.
6. Convert processed data to a compact numerical representation.
7. Save the processed arrays.

**Input dimensions:**

| Parameter | Value |
|---|---:|
| Sampling rate | 200 Hz |
| Window duration | 10 seconds |
| Number of channels | 20 |
| Samples per channel | 2,000 |

Final tensor:

```text
20 x 2000
```

### 2. Spectrogram Processing

Implemented in `src/prepare_spectrograms.py`.

The spectrogram pipeline extracts four frequency-channel groups:

- LL
- RL
- LP
- RP

Processing steps:

1. Load spectrogram Parquet files.
2. Extract the four channel groups.
3. Align the window using spectrogram label offsets.
4. Extract 120 seconds of context.
5. Select a two-second time grid.
6. Normalize each spectrogram channel.
7. Zero-pad missing context.
8. Save the processed representation.

Final tensor:

```text
4 x 60 x 100
```

The EEG and spectrogram offsets are handled independently.

---

## Model Architecture

The primary classifier is a **Residual Attention-Based Multimodal CNN**, implemented in `src/model.py`.

It contains three major components:

1. Raw EEG encoder.
2. Spectrogram encoder.
3. Attention-based feature fusion and classification.

### 1. EEG Encoder

The EEG branch uses residual 1D convolutional blocks to learn temporal patterns from the raw signals.

| Layer | Input Channels | Output Channels |
|---|---:|---:|
| Stem | 20 | 64 |
| Residual Block 1 | 64 | 64 |
| Residual Block 2 | 64 | 128 |
| Residual Block 3 | 128 | 256 |
| Residual Block 4 | 256 | 256 |
| Residual Block 5 | 256 | 384 |

The encoder uses:

- 1D convolutions with kernel size 7 in residual blocks.
- Batch normalization.
- GELU activation.
- Residual connections.
- Dropout.
- Adaptive average pooling.

The resulting 384-dimensional representation is projected into a 256-dimensional feature vector.

### 2. Spectrogram Encoder

The spectrogram branch uses residual 2D convolutional blocks to extract spatial and frequency-related features.

| Layer | Input Channels | Output Channels |
|---|---:|---:|
| Stem | 4 | 64 |
| Residual Block 1 | 64 | 64 |
| Residual Block 2 | 64 | 128 |
| Residual Block 3 | 128 | 256 |
| Residual Block 4 | 256 | 384 |
| Residual Block 5 | 384 | 384 |

The encoder uses:

- 2D convolutions with kernel size 3 in residual blocks.
- Batch normalization.
- GELU activation.
- Residual connections.
- Dropout.
- Adaptive average pooling.

The resulting 384-dimensional representation is projected into a 256-dimensional feature vector.

### 3. Attention-Based Fusion

The two feature vectors are combined using a multi-head self-attention mechanism.

Configuration:

| Parameter | Value |
|---|---:|
| Feature dimension | 256 |
| Number of attention heads | 8 |
| Number of modality tokens | 2 |
| Feed-forward hidden dimension | 512 |
| Attention dropout | 0.1 |

Learnable modality embeddings distinguish EEG and spectrogram features.

The attention module applies:

- Multi-head attention.
- Residual connections.
- Layer normalization.
- Feed-forward transformation.
- Mean pooling across modality tokens.

The resulting fused representation contains 256 features.

### 4. Classification Head

```text
Linear(256 -> 256)
LayerNorm
GELU
Dropout(0.3)

Linear(256 -> 128)
GELU
Dropout(0.2)

Linear(128 -> 6)
```

The final output consists of six logits, converted into class probabilities using softmax during inference.

---

## Random Forest Baseline

A traditional Random Forest classifier is implemented in `src/random_forest.py`.

This model provides a baseline against which the multimodal deep learning architecture can be evaluated.

### Feature Extraction

The baseline uses Welch's Power Spectral Density (PSD) estimation.

Five frequency bands are extracted from each of the 20 EEG channels.

| Frequency Band | Range |
|---|---|
| Delta | 0.5–4 Hz |
| Theta | 4–8 Hz |
| Alpha | 8–13 Hz |
| Beta | 13–30 Hz |
| Gamma | 30–45 Hz |

Relative band power is calculated as:

```text
Relative Power = Band Power / Total Power
```

The resulting feature vector contains:

```text
20 channels x 5 bands = 100 features
```

### Random Forest Configuration

| Parameter | Value |
|---|---|
| Number of estimators | 200 |
| Maximum features | sqrt |
| Minimum samples per leaf | 2 |
| Class weighting | balanced_subsample |
| Random state | 42 |
| Parallel processing | All available CPU cores |

---

## Training

The deep learning model is trained using PyTorch.

### Training Configuration

| Parameter | Value |
|---|---|
| Optimizer | Adam |
| Learning rate | 0.001 |
| Batch size | 64 |
| Maximum epochs | 8 |
| Early stopping patience | 3 |
| Loss function | Weighted Cross Entropy |
| DataLoader workers | 4 |
| CUDA acceleration | Supported |

### Class Weighting

Weighted cross-entropy is used to account for class imbalance.

Class weights are calculated from the training sample counts:

```python
class_weights = class_counts.sum() / (
    len(class_counts) * class_counts
)
```

This increases the relative contribution of less frequent classes during training.

### Checkpoint Saving

The training script saves the best checkpoint according to validation accuracy.

The training script currently writes:

```text
models/fusion_residual_attention_best.pt
```

The inference module and GUI currently expect:

```text
models/fusion_best.pt
```

These filenames must be kept consistent when preparing the final checkpoint for inference.

---

## Evaluation

The models are evaluated using a patient-level validation set containing 23,116 samples.

Metrics include:

- Accuracy
- Balanced accuracy
- Precision
- Recall
- Macro F1-score
- Weighted F1-score
- Confusion matrix

### Multimodal Model Results

The reported final residual-attention evaluation achieved:

| Metric | Result |
|---|---:|
| Accuracy | 53.88% |
| Balanced Accuracy | 51.98% |
| Macro Precision | 51.47% |
| Macro Recall | 51.98% |
| Macro F1-score | 51.42% |
| Weighted F1-score | 53.59% |

### Per-Class Performance

| Class | Precision | Recall | F1-score |
|---|---:|---:|---:|
| Seizure | 0.6535 | 0.6039 | 0.6277 |
| GPD | 0.7759 | 0.8307 | 0.8024 |
| LRDA | 0.4226 | 0.3630 | 0.3905 |
| Other | 0.4091 | 0.3303 | 0.3655 |
| GRDA | 0.3814 | 0.5052 | 0.4346 |
| LPD | 0.4454 | 0.4856 | 0.4646 |

GPD achieved the highest F1-score, followed by Seizure.

The results also show that LRDA and Other remain challenging categories.

**Note:** These are the reported evaluation results for the residual-attention experiment. Reproduce the evaluation using the matching checkpoint before treating them as independently reproducible benchmark results.

### Random Forest Results

The Random Forest baseline is evaluated using the same validation split.

Its performance is lower than the reported multimodal CNN results, illustrating the advantage of learning features from both raw EEG and spectrogram representations rather than relying exclusively on manually extracted band-power features.

---

## Inference Pipeline

The inference pipeline is implemented in:

```text
src/inference.py
src/assistant.py
```

The system accepts an EEG Parquet file and its corresponding spectrogram Parquet file.

### Single-Window Inference

The inference process:

1. Loads the EEG and spectrogram recordings.
2. Extracts the requested EEG window.
3. Extracts the corresponding spectrogram context.
4. Applies model preprocessing.
5. Runs the multimodal neural network.
6. Calculates class probabilities.
7. Identifies the predicted category.
8. Estimates uncertainty.
9. Assigns an attention level.

### Prediction Output

The system returns:

- Predicted EEG pattern.
- Confidence score.
- Six-class probability distribution.
- Uncertainty level.
- Attention assessment.
- Top alternative predictions.
- Natural-language interpretation.

### Uncertainty Estimation

Uncertainty is estimated using the highest class probability and the margin between the two most likely classes.

This helps identify cases where competing predictions have similar probabilities.

### Attention Assessment

Attention assessment is handled separately from uncertainty.

Seizure-related predictions receive elevated monitoring priority, including cases where the model is uncertain.

This is an experimental prioritization mechanism, not a validated clinical alert protocol.

---

## Continuous EEG Monitoring

The project includes a temporal monitoring pipeline in `src/monitor.py`.

Rather than analyzing only one window, the system processes an entire EEG recording sequentially.

### Monitoring Configuration

| Parameter | Value |
|---|---:|
| EEG window | 10 seconds |
| Monitoring step | 10 seconds |
| EEG sampling rate | 200 Hz |
| Spectrogram context | 120 seconds |

### Monitoring Workflow

```text
Full EEG Recording
       |
       v
Load EEG and Spectrogram
       |
       v
Extract First Window
       |
       v
Run Model Inference
       |
       v
Store Prediction
       |
       v
Advance Monitoring Window
       |
       v
Repeat Until Recording Ends
       |
       v
Group Consecutive Predictions
       |
       v
Detect Persistent Events
       |
       v
Generate Seizure-Related Alerts
```

### Temporal Event Detection

Consecutive windows with the same predicted category are grouped into continuous events.

Each event contains:

- Predicted pattern.
- Start time.
- End time.
- Duration.
- Average confidence.
- Maximum confidence.

### Alert Generation

Seizure-related events are assigned experimental alert levels based on average confidence and event duration.

| Condition | Alert Level |
|---|---|
| Confidence below 50% | REVIEW |
| Confidence from 50% to below 80% | ATTENTION |
| Confidence at least 80%, duration below 20 seconds | HIGH |
| Confidence at least 80%, duration at least 20 seconds | PERSISTENT HIGH |

These thresholds are heuristic research settings and require clinical validation before any real-world application.

---

## Graphical User Interface

The project includes a desktop application built with **PySide6**, using a Neka-inspired dark teal and frosted-glass visual design.

Three.js is integrated through Qt WebEngine to provide interactive 3D anatomical visualization.

### 1. Onboarding and Patient Profile

The onboarding interface collects basic session information and allows selection of a male or female anatomical profile.

### 2. Interactive 3D Anatomical Viewer

The body selection interface includes:

- Male and female anatomical models.
- Interactive 3D rotation.
- Anatomical region selection.
- Holographic display mode.
- Stylized anatomy mode.
- Brain selection to open EEG monitoring.

### 3. EEG Monitoring Dashboard

The dashboard includes:

- EEG recording selection.
- Spectrogram selection.
- Independent recording offsets.
- EEG waveform visualization.
- Spectrogram visualization.
- Inference execution.

### 4. Prediction Panel

The prediction interface displays:

- Predicted category.
- Model confidence.
- Uncertainty level.
- Attention assessment.
- Six-class probability bars.
- Alternative predictions.
- Interpretation messages.

### GUI Technologies

| Component | Technology |
|---|---|
| Desktop application | PySide6 |
| 3D rendering | Three.js |
| 3D model loading | GLTFLoader |
| Python–JavaScript communication | Qt WebChannel |
| EEG plotting | PyQtGraph |
| Model inference | PyTorch |
| GUI background processing | QThread |

The GUI uses the existing inference pipeline rather than maintaining a separate implementation of the model.

---

## Project Structure

```text
ICU_EEG_Monitoring_Assistant/
│
├── data/
│   ├── raw/
│   │   ├── train.csv
│   │   ├── test.csv
│   │   ├── train_eegs/
│   │   ├── test_eegs/
│   │   ├── train_spectrograms/
│   │   └── test_spectrograms/
│   │
│   └── processed/
│
├── models/
│   └── .gitkeep
│
├── notebooks/
│   └── EDA.ipynb
│
├── outputs/
│   ├── train_split.csv
│   ├── val_split.csv
│   └── features/
│
├── src/
│   ├── model.py
│   ├── dataset.py
│   ├── prepare_data.py
│   ├── prepare_spectrograms.py
│   ├── train.py
│   ├── evaluate.py
│   ├── evaluate_fusion.py
│   ├── random_forest.py
│   ├── inference.py
│   ├── assistant.py
│   ├── monitor.py
│   ├── visualize_eeg.py
│   │
│   └── gui/
│       ├── app.py
│       ├── main.py
│       ├── core/
│       ├── pages/
│       ├── services/
│       ├── workers/
│       ├── widgets/
│       ├── styles/
│       └── web/
│           ├── assets/
│           ├── index.html
│           ├── src/
│           └── styles.css
│
├── pyproject.toml
├── uv.lock
├── .python-version
├── .gitignore
└── README.md
```

Large datasets, generated feature caches, and trained model checkpoints are intentionally excluded from Git.

---

## Installation and Setup

### Prerequisites

- Python 3.13
- Git
- uv package manager
- NVIDIA GPU with compatible CUDA-enabled PyTorch, recommended for accelerated training
- HMS dataset downloaded from Kaggle

### 1. Clone the Repository

```bash
git clone https://github.com/mardhav-2008/ICU_EEG_Monitoring_Assistant.git

cd ICU_EEG_Monitoring_Assistant
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Prepare Dataset

Download the HMS Harmful Brain Activity Classification dataset from Kaggle.

Extract the required files into the expected directory structure:

```text
data/raw/
```

Ensure the EEG and spectrogram Parquet files are present.

### 4. Prepare EEG Data

```bash
uv run python src/prepare_data.py
```

### 5. Prepare Spectrograms

```bash
uv run python src/prepare_spectrograms.py
```

### 6. Train the Model

```bash
uv run python src/train.py
```

### 7. Evaluate the Model

```bash
uv run python src/evaluate_fusion.py
```

Ensure the evaluation script points to the checkpoint generated by the training run.

### 8. Run Random Forest Baseline

```bash
uv run python src/random_forest.py
```

### 9. Run the Desktop GUI

```bash
PYTHONPATH=src uv run python -m gui.main
```

The GUI requires the model checkpoint expected by `src/inference.py` to be available in the `models/` directory.

Three.js modules are currently loaded through jsDelivr, so the first launch requires internet access.

---

## Technologies Used

| Category | Technologies |
|---|---|
| Programming language | Python |
| Deep learning | PyTorch |
| Machine learning | Scikit-learn |
| Numerical computing | NumPy |
| Data processing | Pandas, PyArrow |
| Signal processing | SciPy |
| Desktop GUI | PySide6 |
| EEG visualization | PyQtGraph |
| 3D visualization | Three.js |
| Model formats | PyTorch checkpoints, Joblib |
| Environment management | uv |
| GPU acceleration | NVIDIA CUDA |

---

## Limitations and Future Improvements

Although the project demonstrates a complete research pipeline, several areas require further development.

### Current Limitations

- Validation accuracy does not establish clinical reliability.
- Some EEG categories remain difficult to distinguish.
- The model has not been independently validated on a separate external clinical dataset.
- Attention and alert thresholds are heuristic.
- The model currently relies on paired EEG and spectrogram inputs.
- Real-time acquisition from clinical EEG hardware has not been implemented.
- The graphical interface is a research prototype.

### Future Work

1. Evaluate the model using independent EEG datasets, including externally sourced recordings.
2. Improve classification performance for LRDA, Other, and LPD.
3. Investigate temporal models for sequential EEG classification.
4. Explore calibration techniques for more reliable confidence estimates.
5. Introduce explainability methods such as saliency maps and feature attribution.
6. Improve persistent event detection and temporal smoothing.
7. Integrate live EEG acquisition hardware.
8. Optimize inference latency and memory usage.
9. Conduct external validation and appropriate clinical evaluation.
10. Improve the monitoring dashboard and reporting functionality.

---

## Research and Development

**Project:** ICU EEG Monitoring Assistant

**Developer:** Mardhav Rayapati

**Institution:** Lovely Professional University, Punjab

**Repository:** https://github.com/mardhav-2008/ICU_EEG_Monitoring_Assistant

---

## License

No explicit open-source license is currently specified. All rights and permissions should be clarified before redistribution or commercial use.

Third-party anatomical assets and datasets remain subject to their respective licenses and terms of use.
