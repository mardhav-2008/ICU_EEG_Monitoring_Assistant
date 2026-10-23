# ICU EEG Monitoring Assistant

A multimodal deep-learning system for classifying harmful brain activity
patterns from ICU EEG recordings.

The project combines **raw EEG signals** and **EEG-derived
spectrograms** to classify six clinically relevant EEG patterns:

-   Seizure
-   Generalized Periodic Discharges (GPD)
-   Lateralized Rhythmic Delta Activity (LRDA)
-   Other
-   Generalized Rhythmic Delta Activity (GRDA)
-   Lateralized Periodic Discharges (LPD)

The system includes dataset analysis, patient-level splitting, EEG and
spectrogram preprocessing, multimodal model training, evaluation,
single-window inference, uncertainty estimation, and continuous
monitoring with temporal event detection.

> **Clinical disclaimer:** This is a research and decision-support
> project. Model predictions are not medical diagnoses and should not be
> used autonomously for clinical decision-making.

------------------------------------------------------------------------

## Project Overview

The goal is to build a practical ICU EEG monitoring pipeline that can
analyze EEG segments and identify the most likely harmful brain activity
pattern.

The final system follows this pipeline:

``` text
Raw EEG + Spectrogram
        │
        ▼
Preprocessing
        │
        ├── Raw EEG → 20-channel normalized signal
        │
        └── Spectrogram → 4 × 60 × 100 normalized representation
        │
        ▼
Multimodal CNN
        │
        ▼
Six-class prediction
        │
        ├── Confidence
        ├── Uncertainty
        └── Attention level
        │
        ▼
Continuous Monitoring
        │
        ├── Temporal event grouping
        ├── Alerts
        └── Monitoring dashboard
```

------------------------------------------------------------------------

## Dataset

This project uses the **HMS Harmful Brain Activity Classification**
dataset from Kaggle.

The training dataset contains:

-   **106,800 labeled rows**
-   **17,089 unique EEG recordings**
-   20-channel raw EEG recordings
-   EEG-derived spectrograms
-   Expert consensus labels
-   Individual vote counts for each target class

The target variable is:

``` text
expert_consensus
```

### Classes

  Class     Description
  --------- ---------------------------------------------------
  Seizure   Seizure-related EEG activity
  GPD       Generalized Periodic Discharges
  LRDA      Lateralized Rhythmic Delta Activity
  Other     EEG patterns outside the primary named categories
  GRDA      Generalized Rhythmic Delta Activity
  LPD       Lateralized Periodic Discharges

### Class Distribution

  Class       Samples   Percentage
  --------- --------- ------------
  Seizure      20,933       19.60%
  GRDA         18,861       17.66%
  Other        18,808       17.61%
  GPD          16,702       15.64%
  LRDA         16,640       15.58%
  LPD          14,856       13.91%

The class distribution is moderately imbalanced, so class-weighted
cross-entropy was used during the final training experiment.

------------------------------------------------------------------------

## Dataset Structure

The raw dataset is organized as:

``` text
data/raw/
├── train.csv
├── test.csv
├── sample_submission.csv
├── train_eegs/
├── test_eegs/
├── train_spectrograms/
├── test_spectrograms/
└── example_figures/
```

Processed arrays are stored under:

``` text
data/processed/
```

------------------------------------------------------------------------

## Train/Validation Split

A **patient-level split** is used rather than a random row-level split.

This prevents recordings belonging to the same patient from appearing in
both training and validation sets.

``` python
from sklearn.model_selection import train_test_split

patients = train["patient_id"].unique()

train_patients, val_patients = train_test_split(
    patients,
    test_size=0.2,
    random_state=42
)

train_df = train[train["patient_id"].isin(train_patients)].copy()
val_df = train[train["patient_id"].isin(val_patients)].copy()
```

The resulting split contains:

  Split            Rows
  ------------ --------
  Training       83,684
  Validation     23,116

There is no patient overlap between the two sets.

The split files are saved as:

``` text
outputs/train_split.csv
outputs/val_split.csv
```

------------------------------------------------------------------------

# Input Modalities

The final model uses two complementary input modalities.

## Raw EEG

Raw EEG recordings are sampled at:

``` text
200 Hz
```

Each inference window contains:

``` text
10 seconds × 200 Hz = 2,000 samples
```

The recordings contain **20 channels**.

Each channel is normalized independently before being passed to the
neural network.

The resulting EEG tensor has the shape:

``` text
20 × 2,000
```

------------------------------------------------------------------------

## Spectrogram

The spectrogram representation contains four channel groups:

``` text
LL
RL
LP
RP
```

Each group contains 100 frequency features.

The spectrogram is sampled every two seconds.

The model uses a 120-second context window:

``` text
120 seconds / 2 seconds = 60 time bins
```

Therefore, each spectrogram input has the shape:

``` text
4 × 60 × 100
```

The four channels are normalized independently.

Spectrogram windows are zero-padded when insufficient context is
available.

### EEG/Spectrogram Alignment

The dataset contains separate EEG and spectrogram label offsets:

``` text
eeg_label_offset_seconds
spectrogram_label_offset_seconds
```

These offsets are not assumed to be identical in the preprocessing
pipeline.

------------------------------------------------------------------------

# Preprocessing

## Raw EEG preprocessing

`src/prepare_data.py` performs the raw EEG preprocessing.

The process includes:

1.  Loading the EEG parquet files.
2.  Selecting the appropriate EEG segment.
3.  Extracting a 10-second window.
4.  Handling missing values.
5.  Normalizing each channel independently.
6.  Converting the result to `float16`.
7.  Saving the processed arrays.

The resulting cache contains:

``` text
20 × 2,000
```

per sample.

------------------------------------------------------------------------

## Spectrogram preprocessing

`src/prepare_spectrograms.py` prepares the spectrogram inputs.

The process includes:

1.  Loading the raw spectrogram parquet files.
2.  Selecting the LL/RL/LP/RP feature groups.
3.  Aligning the window using the spectrogram label offset.
4.  Extracting 120 seconds of context.
5.  Resampling/selecting the two-second time grid.
6.  Normalizing each channel.
7.  Zero-padding missing context.
8.  Saving the processed arrays.

The final representation is:

``` text
4 × 60 × 100
```

------------------------------------------------------------------------

# Model Architecture

The final model is a multimodal convolutional neural network.

``` text
                  ┌──────────────────┐
                  │     Raw EEG      │
                  │   20 × 2,000     │
                  └────────┬─────────┘
                           │
                           ▼
                    EEG CNN Branch
                           │
                           ▼
                     128 features
                           │
                           │
                           │     ┌─────────────────────┐
                           │     │    Spectrogram      │
                           │     │     4 × 60 × 100    │
                           │     └──────────┬──────────┘
                           │                │
                           │                ▼
                           │         Spectrogram CNN
                           │                │
                           │                ▼
                           │          128 features
                           │                │
                           └───────┬────────┘
                                   ▼
                            Feature Concatenation
                                   │
                              256 features
                                   │
                                   ▼
                              Dense Layer
                                   │
                              128 features
                                   │
                                   ▼
                            Dropout (0.5)
                                   │
                                   ▼
                            6-Class Output
```

## EEG Branch

The raw EEG branch uses three 1D convolutional blocks:

``` text
Conv1D(20 → 32)
BatchNorm
ReLU
MaxPool

Conv1D(32 → 64)
BatchNorm
ReLU
MaxPool

Conv1D(64 → 128)
BatchNorm
ReLU
MaxPool

Adaptive Average Pooling
```

Output:

``` text
128 features
```

## Spectrogram Branch

The spectrogram branch uses three 2D convolutional blocks:

``` text
Conv2D(4 → 32)
BatchNorm
ReLU
MaxPool

Conv2D(32 → 64)
BatchNorm
ReLU
MaxPool

Conv2D(64 → 128)
BatchNorm
ReLU

Adaptive Average Pooling
```

Output:

``` text
128 features
```

The two feature vectors are concatenated:

``` text
128 + 128 = 256 features
```

The classifier is:

``` text
Linear(256 → 128)
ReLU
Dropout(0.5)
Linear(128 → 6)
```

------------------------------------------------------------------------

# Training

The final model was trained using:

  Parameter                 Value
  ------------------------- ------------------------
  Optimizer                 Adam
  Learning rate             0.001
  Batch size                64
  Epochs                    8
  Early stopping patience   3
  Loss                      Weighted Cross Entropy
  DataLoader workers        4
  Pin memory                Enabled
  Persistent workers        Enabled
  Input EEG window          10 seconds
  Spectrogram context       120 seconds

### Class Weighting

Class weights were calculated from the training class counts:

``` python
class_counts = torch.tensor(
    [
        16101,
        11887,
        12213,
        15414,
        15466,
        12603,
    ],
    dtype=torch.float32,
)

class_weights = class_counts.sum() / (
    len(class_counts) * class_counts
)
```

This gives relatively higher weight to less frequent classes.

------------------------------------------------------------------------

# Model Comparison

Several experiments were performed to evaluate the contribution of the
multimodal approach.

  Model / Experiment                Best Validation Accuracy
  ------------------------------- --------------------------
  EEG-only                                            46.17%
  EEG-only + class weighting                          45.89%
  Fusion, weighted, 120 s                         **51.02%**
  Fusion, weighted, LR = 0.0003                       50.17%
  Fusion, unweighted                                  50.36%
  Fusion, weighted, 60 s                              50.83%
  Projection-based fusion                             47.73%

The final multimodal model improved validation accuracy over the
original EEG-only model by approximately:

``` text
51.02% - 46.17% = 4.85 percentage points
```

------------------------------------------------------------------------

# Final Evaluation

The final checkpoint is:

``` text
models/fusion_best.pt
```

Validation performance:

  Metric                     Score
  ------------------- ------------
  Accuracy              **51.02%**
  Balanced Accuracy         47.54%
  Macro F1                  46.45%
  Weighted F1               49.43%

## Classification Report

  Class       Precision   Recall       F1
  --------- ----------- -------- --------
  Seizure        0.4838   0.7130   0.5765
  GPD            0.8120   0.7329   0.7704
  LRDA           0.5991   0.2464   0.3492
  Other          0.3426   0.3332   0.3379
  GRDA           0.3764   0.6424   0.4746
  LPD            0.5675   0.1846   0.2786

The strongest classes were **GPD** and **Seizure**.

The weakest recalls were observed for **LRDA**, **Other**, and **LPD**.

------------------------------------------------------------------------

# Confusion Matrix

``` text
             Seizur     GPD    LRDA   Other    GRDA     LPD
Seizure       3445      189     163     553     442      40
GPD            653     3529      26     212     262     133
LRDA           685      138    1091     562    1895      56
Other         1057      200     164    1131     770      72
GRDA           521      125     225     327    2181      16
LPD            759      165     152     516     245     416
```

The largest confusion was:

``` text
LRDA → GRDA = 1,895 samples
```

Other notable confusions include:

``` text
Other → Seizure = 1,057
LPD   → Seizure =   759
```

------------------------------------------------------------------------

# Inference

The main inference implementation is:

``` text
src/inference.py
```

It supports both single-window prediction and repeated monitoring.

The model automatically uses CUDA when available.

Run a basic inference test with:

``` bash
uv run python src/inference.py
```

The inference pipeline performs:

``` text
Raw EEG
    │
    ▼
10-second window
    │
    ▼
Channel normalization
    │
    ▼
EEG tensor
    │
    ├──────────────┐
    │              │
    ▼              ▼
Spectrogram     EEG CNN
preprocessing      │
    │              │
    ▼              │
Spectrogram CNN    │
    │              │
    └──────┬───────┘
           ▼
       Fusion model
           │
           ▼
    Class probabilities
```

------------------------------------------------------------------------

# Confidence, Uncertainty, and Attention

The monitoring assistant does not treat every prediction equally.

It reports three separate concepts:

### Confidence

How strongly the model favors the predicted class.

Thresholds:

``` text
High       ≥ 80%
Moderate   ≥ 60%
Low        < 60%
```

### Uncertainty

Uncertainty is estimated from both:

-   the top predicted probability
-   the margin between the top two classes

The system uses:

``` text
High uncertainty
Moderate uncertainty
Low uncertainty
```

A prediction can therefore have a relatively high confidence score but
still receive additional attention if competing classes are close.

### Attention

Attention represents how urgently the result should be reviewed.

The current system uses higher attention for:

-   seizure predictions
-   highly uncertain predictions
-   GPD/LRDA/LPD predictions requiring closer review

The system intentionally uses terms such as **review**, **attention**,
and **model-detected pattern** rather than presenting the output as a
diagnosis.

------------------------------------------------------------------------

# Continuous Monitoring

The monitoring pipeline is implemented in:

``` text
src/monitor.py
```

It efficiently loads the EEG and spectrogram once and then analyzes
consecutive EEG windows.

Each window represents:

``` text
10 seconds
```

The spectrogram provides:

``` text
120 seconds of context
```

For each window, the monitor records:

-   start time
-   end time
-   predicted pattern
-   confidence
-   uncertainty
-   attention level
-   class probabilities

Example timeline:

``` text
00:00 - 00:10  GRDA     75.96%  LOW      MODERATE
00:10 - 00:20  GRDA     82.50%  LOW      LOW
00:20 - 00:30  GRDA     90.67%  LOW      LOW
00:30 - 00:40  GRDA     90.42%  LOW      LOW
00:40 - 00:50  GRDA     93.78%  LOW      LOW
00:50 - 00:56  GRDA     70.03%  LOW      MODERATE
```

------------------------------------------------------------------------

# Temporal Event Detection

Individual predictions are grouped into continuous events when
consecutive windows predict the same pattern.

For example:

``` text
GRDA
GRDA
GRDA
GRDA
GRDA
GRDA
```

is grouped into one event:

``` text
00:00 - 00:56  GRDA
```

For each event, the monitor reports:

-   start time
-   end time
-   duration
-   average confidence
-   maximum confidence

Example:

``` text
Event:
00:00 - 00:56 GRDA
Duration: 56 seconds
Average confidence: 83.89%
Maximum confidence: 93.78%
```

The final event is clipped to the actual recording duration so that
monitoring results do not extend beyond the available EEG.

------------------------------------------------------------------------

# Alerts

The monitoring system includes rule-based alert generation.

For seizure events:

  Condition                   Alert
  --------------------------- -----------------
  Average confidence \< 50%   REVIEW
  50%--\<80%                  ATTENTION
  ≥80%, duration \<20 s       HIGH
  ≥80%, duration ≥20 s        PERSISTENT HIGH

These alerts are intended to prioritize review of model outputs.

They are **not clinical alarms or diagnoses**.

------------------------------------------------------------------------

# Monitoring Dashboard

The monitor produces a compact dashboard containing:

-   recording duration
-   number of analyzed windows
-   current pattern
-   current confidence
-   uncertainty
-   attention level
-   dominant pattern
-   number of detected events
-   number of alerts
-   pattern distribution

Example:

``` text
Recording duration: 00:56
Windows analyzed:   6
Current pattern:    GRDA
Confidence:         70.0%
Uncertainty:        LOW
Attention:          MODERATE
Dominant pattern:   GRDA
Events detected:    1
Alerts:             0

Pattern distribution:
GRDA 100%

ALERTS: NONE
```

------------------------------------------------------------------------

# Generated Outputs

Monitoring runs can produce:

``` text
outputs/
├── monitoring_<eeg_id>.csv
└── monitoring_<eeg_id>.png
```

The CSV contains the per-window monitoring results.

The PNG contains a visualization of confidence over time, predicted
classes, and confidence thresholds.

Example output:

``` text
outputs/monitoring_4281533846.csv
outputs/monitoring_4281533846.png
```

------------------------------------------------------------------------

# Project Structure

``` text
ICU_EEG_Monitoring_Assistant/
│
├── data/
│   ├── raw/
│   │   ├── train.csv
│   │   ├── test.csv
│   │   ├── sample_submission.csv
│   │   ├── train_eegs/
│   │   ├── test_eegs/
│   │   ├── train_spectrograms/
│   │   ├── test_spectrograms/
│   │   └── example_figures/
│   │
│   └── processed/
│
├── models/
│   └── fusion_best.pt
│
├── notebooks/
│   └── EDA.ipynb
│
├── outputs/
│   ├── train_split.csv
│   ├── val_split.csv
│   ├── monitoring_*.csv
│   └── monitoring_*.png
│
├── src/
│   ├── __init__.py
│   ├── dataset.py
│   ├── model.py
│   ├── prepare_data.py
│   ├── prepare_spectrograms.py
│   ├── train.py
│   ├── evaluate.py
│   ├── evaluate_fusion.py
│   ├── inference.py
│   ├── assistant.py
│   └── monitor.py
│
├── README.md
├── pyproject.toml
└── uv.lock
```

------------------------------------------------------------------------

# Installation

The project uses `uv` for environment and dependency management.

Create the virtual environment:

``` bash
uv venv
```

Install/synchronize dependencies:

``` bash
uv sync
```

Run Python through the project environment:

``` bash
uv run python <script>
```

For example:

``` bash
uv run python src/monitor.py
```

------------------------------------------------------------------------

# Usage

## 1. Prepare EEG data

``` bash
uv run python src/prepare_data.py
```

## 2. Prepare spectrograms

``` bash
uv run python src/prepare_spectrograms.py
```

## 3. Train the model

``` bash
uv run python src/train.py
```

## 4. Evaluate the trained model

``` bash
uv run python src/evaluate_fusion.py
```

## 5. Run single-window inference

``` bash
uv run python src/inference.py
```

## 6. Run continuous monitoring

``` bash
uv run python src/monitor.py
```

------------------------------------------------------------------------

# Reproducibility

The project uses:

-   a fixed random seed for the patient-level train/validation split
-   a locked dependency environment through `uv.lock`
-   a fixed model architecture
-   a fixed preprocessing pipeline
-   a saved final checkpoint

The final reported validation model is:

``` text
models/fusion_best.pt
```

with validation accuracy:

``` text
51.02%
```

------------------------------------------------------------------------

# Key Findings

The main findings from the project are:

1.  **Patient-level splitting is important** to avoid leakage between
    recordings from the same patient.
2.  **The dataset is imbalanced**, motivating class-weighted training.
3.  **Raw EEG alone provides useful signal**, but the multimodal model
    performs better.
4.  **Combining EEG and spectrogram representations improved validation
    accuracy from 46.17% to 51.02%.**
5.  **GPD and Seizure were the strongest classes** in the final
    evaluation.
6.  **LRDA, Other, and LPD remain difficult classes**, with substantial
    confusion between related patterns.
7.  **Confidence alone is insufficient**, so the monitoring system also
    considers uncertainty and attention.
8.  **Temporal grouping makes repeated predictions easier to interpret**
    during continuous monitoring.

------------------------------------------------------------------------

# Limitations

The current system has several important limitations.

### Model Performance

The final validation accuracy is approximately 51%, so the model is not
sufficiently reliable for autonomous clinical diagnosis.

### Class Confusion

Some EEG patterns are difficult to distinguish. In particular:

``` text
LRDA ↔ GRDA
Other ↔ Seizure
LPD ↔ Seizure
```

show substantial confusion.

### Limited Temporal Modeling

The classifier operates on individual 10-second EEG windows with
spectrogram context. It does not use a recurrent or transformer-based
temporal model to explicitly model long-range dependencies.

### Dataset Dependence

Performance is dependent on the characteristics of the HMS dataset and
may not generalize directly to other hospitals, EEG systems, patient
populations, or acquisition protocols.

### Monitoring Rules

The alert system is rule-based and designed for research demonstration.
Its thresholds have not been clinically validated.

### Clinical Use

The system should not be used as an autonomous diagnostic system or as a
replacement for qualified EEG interpretation.

------------------------------------------------------------------------

# Future Improvements

Potential future improvements include:

-   stronger temporal modeling
-   transformer-based EEG architectures
-   improved spectrogram encoders
-   more sophisticated multimodal fusion
-   calibration of confidence scores
-   patient-specific adaptation
-   external validation on independent EEG datasets
-   clinically validated alert thresholds
-   richer temporal event modeling
-   real-time streaming input support
-   clinician-facing visualization and review tools

------------------------------------------------------------------------

# Conclusion

This project implements an end-to-end ICU EEG monitoring pipeline using
multimodal deep learning.

The final system combines:

``` text
Raw EEG
   +
Spectrogram
   ↓
Multimodal CNN
   ↓
Six-class EEG pattern classification
   ↓
Confidence + uncertainty + attention
   ↓
Continuous monitoring
   ↓
Temporal event detection
   ↓
Research-oriented alerts
```

The multimodal approach achieved a validation accuracy of **51.02%**,
improving on the EEG-only baseline of **46.17%**.

The project demonstrates how raw physiological signals and
time-frequency representations can be combined into a practical
monitoring pipeline while explicitly communicating model uncertainty and
maintaining appropriate clinical limitations.

------------------------------------------------------------------------

## Disclaimer

This project is intended for **research and educational purposes only**.

The predictions, confidence scores, uncertainty estimates, attention
levels, and alerts generated by this system are model outputs and should
not be interpreted as medical diagnoses.

Any real clinical deployment would require extensive clinical
validation, calibration, regulatory review, safety testing, and
integration with qualified clinical oversight.
