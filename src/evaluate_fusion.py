from pathlib import Path

import torch
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from torch.utils.data import DataLoader

from dataset import EEGDataset
from model import EEGClassifier

ROOT = Path(__file__).resolve().parent.parent

MODEL_PATH = ROOT / "models" / "fusion_best.pt"


LABELS = [
    "Seizure",
    "GPD",
    "LRDA",
    "Other",
    "GRDA",
    "LPD",
]


BATCH_SIZE = 64
NUM_WORKERS = 4


# -------------------------
# Device
# -------------------------

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print(f"Using device: {device}")

if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")


# -------------------------
# Load checkpoint
# -------------------------

checkpoint = torch.load(MODEL_PATH, map_location=device)

print()
print(f"Model: {MODEL_PATH}")
print(f"Saved validation accuracy: {checkpoint['best_val_accuracy']:.4f}")


# -------------------------
# Load model
# -------------------------

model = EEGClassifier(
    num_channels=checkpoint["num_channels"],
    num_classes=checkpoint["num_classes"],
).to(device)

model.load_state_dict(checkpoint["model_state_dict"])

model.eval()


# -------------------------
# Validation dataset
# -------------------------

dataset = EEGDataset("val")

loader = DataLoader(
    dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS,
    pin_memory=True,
)


# -------------------------
# Run evaluation
# -------------------------

all_predictions = []
all_labels = []


with torch.no_grad():
    for eeg, spectrogram, y in loader:
        eeg = eeg.to(device, non_blocking=True)

        spectrogram = spectrogram.to(device, non_blocking=True)

        output = model(eeg, spectrogram)

        predictions = output.argmax(dim=1)

        all_predictions.extend(predictions.cpu().numpy())

        all_labels.extend(y.numpy())


# -------------------------
# Metrics
# -------------------------

accuracy = accuracy_score(all_labels, all_predictions)

balanced_accuracy = balanced_accuracy_score(all_labels, all_predictions)

macro_f1 = f1_score(all_labels, all_predictions, average="macro")

weighted_f1 = f1_score(all_labels, all_predictions, average="weighted")


print()
print("=" * 60)
print("FINAL MODEL EVALUATION")
print("=" * 60)

print(f"Accuracy:           {accuracy:.4f}")

print(f"Balanced accuracy:  {balanced_accuracy:.4f}")

print(f"Macro F1:            {macro_f1:.4f}")

print(f"Weighted F1:         {weighted_f1:.4f}")


# -------------------------
# Classification report
# -------------------------

print()
print("Classification Report")
print()

print(classification_report(all_labels, all_predictions, target_names=LABELS, digits=4))


# -------------------------
# Confusion matrix
# -------------------------

matrix = confusion_matrix(all_labels, all_predictions)

print("Confusion Matrix")
print()

print(" " * 12 + " ".join(f"{label[:6]:>7}" for label in LABELS))

for label, row in zip(LABELS, matrix):
    values = " ".join(f"{value:7d}" for value in row)

    print(f"{label[:10]:>10}  {values}")
