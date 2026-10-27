import torch
from torch import nn

# ============================================================
# Residual 1D block for raw EEG
# ============================================================


class EEGResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1, dropout=0.1):
        super().__init__()

        self.conv1 = nn.Conv1d(
            in_channels,
            out_channels,
            kernel_size=7,
            stride=stride,
            padding=3,
            bias=False,
        )
        self.bn1 = nn.BatchNorm1d(out_channels)

        self.conv2 = nn.Conv1d(
            out_channels,
            out_channels,
            kernel_size=7,
            padding=3,
            bias=False,
        )
        self.bn2 = nn.BatchNorm1d(out_channels)

        self.activation = nn.GELU()
        self.dropout = nn.Dropout(dropout)

        if in_channels != out_channels or stride != 1:
            self.shortcut = nn.Sequential(
                nn.Conv1d(
                    in_channels,
                    out_channels,
                    kernel_size=1,
                    stride=stride,
                    bias=False,
                ),
                nn.BatchNorm1d(out_channels),
            )
        else:
            self.shortcut = nn.Identity()

    def forward(self, x):
        residual = self.shortcut(x)

        x = self.conv1(x)
        x = self.bn1(x)
        x = self.activation(x)

        x = self.dropout(x)

        x = self.conv2(x)
        x = self.bn2(x)

        x = x + residual
        x = self.activation(x)

        return x


# ============================================================
# Raw EEG encoder
# ============================================================


class EEGEncoder(nn.Module):
    def __init__(self):
        super().__init__()

        self.stem = nn.Sequential(
            nn.Conv1d(
                20,
                64,
                kernel_size=15,
                stride=2,
                padding=7,
                bias=False,
            ),
            nn.BatchNorm1d(64),
            nn.GELU(),
        )

        self.blocks = nn.Sequential(
            # 2000 -> 1000
            EEGResidualBlock(64, 64),
            # 1000 -> 500
            EEGResidualBlock(64, 128, stride=2),
            # 500 -> 250
            EEGResidualBlock(128, 256, stride=2),
            # 250 -> 125
            EEGResidualBlock(256, 256, stride=2),
            EEGResidualBlock(256, 384),
        )

        self.pool = nn.AdaptiveAvgPool1d(1)

        self.projection = nn.Sequential(
            nn.Linear(384, 256),
            nn.GELU(),
            nn.Dropout(0.2),
        )

    def forward(self, x):
        x = self.stem(x)
        x = self.blocks(x)

        x = self.pool(x)
        x = x.flatten(1)

        x = self.projection(x)

        return x


# ============================================================
# Residual 2D block for spectrogram
# ============================================================


class SpectrogramResidualBlock(nn.Module):
    def __init__(
        self,
        in_channels,
        out_channels,
        stride=1,
        dropout=0.1,
    ):
        super().__init__()

        self.conv1 = nn.Conv2d(
            in_channels,
            out_channels,
            kernel_size=3,
            stride=stride,
            padding=1,
            bias=False,
        )
        self.bn1 = nn.BatchNorm2d(out_channels)

        self.conv2 = nn.Conv2d(
            out_channels,
            out_channels,
            kernel_size=3,
            padding=1,
            bias=False,
        )
        self.bn2 = nn.BatchNorm2d(out_channels)

        self.activation = nn.GELU()
        self.dropout = nn.Dropout2d(dropout)

        if in_channels != out_channels or stride != 1:
            self.shortcut = nn.Sequential(
                nn.Conv2d(
                    in_channels,
                    out_channels,
                    kernel_size=1,
                    stride=stride,
                    bias=False,
                ),
                nn.BatchNorm2d(out_channels),
            )
        else:
            self.shortcut = nn.Identity()

    def forward(self, x):
        residual = self.shortcut(x)

        x = self.conv1(x)
        x = self.bn1(x)
        x = self.activation(x)

        x = self.dropout(x)

        x = self.conv2(x)
        x = self.bn2(x)

        x = x + residual
        x = self.activation(x)

        return x


# ============================================================
# Spectrogram encoder
# ============================================================


class SpectrogramEncoder(nn.Module):
    def __init__(self):
        super().__init__()

        self.stem = nn.Sequential(
            nn.Conv2d(
                4,
                64,
                kernel_size=7,
                stride=1,
                padding=3,
                bias=False,
            ),
            nn.BatchNorm2d(64),
            nn.GELU(),
        )

        self.blocks = nn.Sequential(
            # 60 x 100
            SpectrogramResidualBlock(64, 64),
            # 30 x 50
            SpectrogramResidualBlock(
                64,
                128,
                stride=2,
            ),
            # 15 x 25
            SpectrogramResidualBlock(
                128,
                256,
                stride=2,
            ),
            # ~8 x 13
            SpectrogramResidualBlock(
                256,
                384,
                stride=2,
            ),
            SpectrogramResidualBlock(
                384,
                384,
            ),
        )

        self.pool = nn.AdaptiveAvgPool2d(1)

        self.projection = nn.Sequential(
            nn.Linear(384, 256),
            nn.GELU(),
            nn.Dropout(0.2),
        )

    def forward(self, x):
        x = self.stem(x)
        x = self.blocks(x)

        x = self.pool(x)
        x = x.flatten(1)

        x = self.projection(x)

        return x


# ============================================================
# Attention fusion
# ============================================================


class AttentionFusion(nn.Module):
    def __init__(self, feature_dim=256, num_heads=8):
        super().__init__()

        self.attention = nn.MultiheadAttention(
            embed_dim=feature_dim,
            num_heads=num_heads,
            dropout=0.1,
            batch_first=True,
        )

        self.norm1 = nn.LayerNorm(feature_dim)

        self.ffn = nn.Sequential(
            nn.Linear(feature_dim, feature_dim * 2),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(feature_dim * 2, feature_dim),
        )

        self.norm2 = nn.LayerNorm(feature_dim)

        # Learnable modality embeddings.
        self.eeg_embedding = nn.Parameter(torch.randn(1, 1, feature_dim) * 0.02)

        self.spec_embedding = nn.Parameter(torch.randn(1, 1, feature_dim) * 0.02)

    def forward(self, eeg_features, spec_features):
        batch_size = eeg_features.size(0)

        eeg_token = eeg_features.unsqueeze(1) + self.eeg_embedding.expand(
            batch_size, -1, -1
        )

        spec_token = spec_features.unsqueeze(1) + self.spec_embedding.expand(
            batch_size, -1, -1
        )

        tokens = torch.cat(
            [eeg_token, spec_token],
            dim=1,
        )

        attended, _ = self.attention(
            tokens,
            tokens,
            tokens,
        )

        tokens = self.norm1(tokens + attended)

        feedforward = self.ffn(tokens)

        tokens = self.norm2(tokens + feedforward)

        # Mean over modalities.
        fused = tokens.mean(dim=1)

        return fused


# ============================================================
# Final classifier
# ============================================================


class EEGClassifier(nn.Module):
    def __init__(
        self,
        num_channels=20,
        num_classes=6,
    ):
        super().__init__()

        self.eeg_encoder = EEGEncoder()
        self.spectrogram_encoder = SpectrogramEncoder()

        self.fusion = AttentionFusion(
            feature_dim=256,
            num_heads=8,
        )

        self.classifier = nn.Sequential(
            nn.Linear(256, 256),
            nn.LayerNorm(256),
            nn.GELU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(128, num_classes),
        )

    def forward(self, eeg, spectrogram):
        eeg_features = self.eeg_encoder(eeg)
        spec_features = self.spectrogram_encoder(spectrogram)

        fused = self.fusion(
            eeg_features,
            spec_features,
        )

        logits = self.classifier(fused)

        return logits
