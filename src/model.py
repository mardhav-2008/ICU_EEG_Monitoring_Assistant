import torch
import torch.nn as nn


class EEGBranch(nn.Module):
    def __init__(self):
        super().__init__()

        self.features = nn.Sequential(
            nn.Conv1d(20, 32, kernel_size=7, padding=3),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(32, 64, kernel_size=7, padding=3),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(64, 128, kernel_size=7, padding=3),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.AdaptiveAvgPool1d(1),
        )

    def forward(self, x):

        x = self.features(x)
        x = x.flatten(1)

        return x


class SpectrogramBranch(nn.Module):
    def __init__(self):
        super().__init__()

        self.features = nn.Sequential(
            nn.Conv2d(4, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
        )

    def forward(self, x):

        x = self.features(x)
        x = x.flatten(1)

        return x


class EEGClassifier(nn.Module):
    def __init__(
        self,
        num_channels=20,
        num_classes=6,
    ):
        super().__init__()

        self.eeg_branch = EEGBranch()
        self.spectrogram_branch = SpectrogramBranch()

        self.classifier = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes),
        )

    def forward(self, eeg, spectrogram):

        eeg_features = self.eeg_branch(eeg)

        spectrogram_features = self.spectrogram_branch(spectrogram)

        features = torch.cat([eeg_features, spectrogram_features], dim=1)

        return self.classifier(features)
