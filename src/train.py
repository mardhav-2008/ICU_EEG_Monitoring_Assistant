from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from dataset import EEGDataset
from model import EEGClassifier


ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"
MODEL_DIR = ROOT / "models"

MODEL_DIR.mkdir(exist_ok=True)


BATCH_SIZE = 64
NUM_WORKERS = 4
LEARNING_RATE = 0.001
EPOCHS = 8
PATIENCE = 3


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print(f"Using device: {device}")

if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")


# -------------------------
# Datasets
# -------------------------

train_dataset = EEGDataset("train")
val_dataset = EEGDataset("val")


train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=NUM_WORKERS,
    pin_memory=True,
    persistent_workers=True,
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS,
    pin_memory=True,
    persistent_workers=True,
)


# -------------------------
# Model
# -------------------------

model = EEGClassifier(
    num_channels=20,
    num_classes=6,
).to(device)


# -------------------------
# Class weights
# -------------------------

class_counts = torch.tensor(
    [
        16101,  # Seizure
        11887,  # GPD
        12213,  # LRDA
        15414,  # Other
        15466,  # GRDA
        12603,  # LPD
    ],
    dtype=torch.float32,
)

class_weights = class_counts.sum() / (len(class_counts) * class_counts)

class_weights = class_weights.to(device)

print()
print("Class weights:")
print(class_weights)


criterion = nn.CrossEntropyLoss(weight=class_weights)


optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)


# -------------------------
# Training
# -------------------------

best_val_accuracy = 0.0
epochs_without_improvement = 0


for epoch in range(EPOCHS):
    # -------------------------
    # Training
    # -------------------------

    model.train()

    train_loss = 0.0
    train_correct = 0
    train_total = 0

    for eeg, spectrogram, y in train_loader:
        eeg = eeg.to(device, non_blocking=True)

        spectrogram = spectrogram.to(device, non_blocking=True)

        y = y.to(device, non_blocking=True)

        optimizer.zero_grad()

        output = model(eeg, spectrogram)

        loss = criterion(output, y)

        loss.backward()

        optimizer.step()

        train_loss += loss.item() * y.size(0)

        predictions = output.argmax(dim=1)

        train_correct += (predictions == y).sum().item()

        train_total += y.size(0)

    train_loss /= train_total

    train_accuracy = train_correct / train_total

    # -------------------------
    # Validation
    # -------------------------

    model.eval()

    val_loss = 0.0
    val_correct = 0
    val_total = 0

    with torch.no_grad():
        for eeg, spectrogram, y in val_loader:
            eeg = eeg.to(device, non_blocking=True)

            spectrogram = spectrogram.to(device, non_blocking=True)

            y = y.to(device, non_blocking=True)

            output = model(eeg, spectrogram)

            loss = criterion(output, y)

            val_loss += loss.item() * y.size(0)

            predictions = output.argmax(dim=1)

            val_correct += (predictions == y).sum().item()

            val_total += y.size(0)

    val_loss /= val_total

    val_accuracy = val_correct / val_total

    # -------------------------
    # Print results
    # -------------------------

    print(
        f"Epoch {epoch + 1}/{EPOCHS} | "
        f"loss: {train_loss:.4f} | "
        f"acc: {train_accuracy:.4f} | "
        f"val_loss: {val_loss:.4f} | "
        f"val_acc: {val_accuracy:.4f}"
    )

    # -------------------------
    # Save best model
    # -------------------------

    if val_accuracy > best_val_accuracy:
        best_val_accuracy = val_accuracy

        epochs_without_improvement = 0

        torch.save(
            {
                "model_state_dict": model.state_dict(),
                "num_channels": 20,
                "num_classes": 6,
                "best_val_accuracy": best_val_accuracy,
                "label_map": {
                    "Seizure": 0,
                    "GPD": 1,
                    "LRDA": 2,
                    "Other": 3,
                    "GRDA": 4,
                    "LPD": 5,
                },
            },
            MODEL_DIR / "fusion_best.pt",
        )

        print(f"Saved new best model ({best_val_accuracy:.4f})")

    else:
        epochs_without_improvement += 1

        print(f"No improvement ({epochs_without_improvement}/{PATIENCE})")

        if epochs_without_improvement >= PATIENCE:
            print("Early stopping.")
            break


print()

print(f"Best validation accuracy: {best_val_accuracy:.4f}")
