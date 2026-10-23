from pathlib import Path

import torch
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, confusion_matrix

from dataset import EEGDataset
from model import EEGClassifier


ROOT = Path(__file__).resolve().parent.parent

MODEL_PATH = ROOT / "models" / "fusion_model.pt"


LABELS = [
    "Seizure",
    "GPD",
    "LRDA",
    "Other",
    "GRDA",
    "LPD",
]


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print(f"Using device: {device}")


checkpoint = torch.load(MODEL_PATH, map_location=device)


model = EEGClassifier(
    num_channels=checkpoint["num_channels"],
    num_classes=checkpoint["num_classes"],
).to(device)


model.load_state_dict(checkpoint["model_state_dict"])

model.eval()


dataset = EEGDataset("val")

loader = DataLoader(
    dataset,
    batch_size=64,
    shuffle=False,
    num_workers=4,
    pin_memory=True,
)


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


print()
print("Classification Report")
print()

print(classification_report(all_labels, all_predictions, target_names=LABELS, digits=4))


matrix = confusion_matrix(all_labels, all_predictions)


print("Confusion Matrix")
print()

print(" " * 12 + " ".join(f"{label[:6]:>7}" for label in LABELS))


for label, row in zip(LABELS, matrix):
    values = " ".join(f"{value:7d}" for value in row)

    print(f"{label[:10]:>10}  {values}")
