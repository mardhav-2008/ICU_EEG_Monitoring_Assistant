from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


class InferenceService:
    """Thin GUI adapter around the repository's existing inference modules.

    The neural network, preprocessing and class definitions remain in
    src/inference.py. This class adds validation and GUI-friendly metadata.
    """

    def __init__(self) -> None:
        self._inference = None
        self._assistant = None

    @property
    def model_path(self) -> Path:
        # src/gui/services/inference_service.py -> project root
        return Path(__file__).resolve().parents[3] / "models" / "fusion_best.pt"

    def load(self) -> None:
        if self._inference is not None:
            return

        if not self.model_path.is_file():
            raise FileNotFoundError(
                f"Model checkpoint not found: {self.model_path}\n"
                "Place fusion_best.pt in the project's models/ directory. "
                "The checkpoint is intentionally excluded from Git."
            )

        # Imports are lazy so the GUI can open without loading a large model.
        # The project is launched with PYTHONPATH=src, matching its CLI imports.
        import inference
        import assistant

        self._inference = inference
        self._assistant = assistant

        loaded_device = str(inference.device)
        print(f"[GUI INFERENCE] Loaded fusion model on {loaded_device}")

    def predict_recording(
        self,
        eeg_path: str | Path,
        spectrogram_path: str | Path,
        eeg_offset_seconds: float = 0.0,
        spectrogram_offset_seconds: float = 0.0,
    ) -> dict[str, Any]:
        eeg_path = Path(eeg_path).expanduser().resolve()
        spectrogram_path = Path(spectrogram_path).expanduser().resolve()

        if not eeg_path.is_file():
            raise FileNotFoundError(f"EEG file not found: {eeg_path}")
        if not spectrogram_path.is_file():
            raise FileNotFoundError(
                f"Spectrogram file not found: {spectrogram_path}"
            )
        if eeg_offset_seconds < 0 or spectrogram_offset_seconds < 0:
            raise ValueError("Offsets must be zero or greater.")

        self.load()
        inference = self._inference
        assistant = self._assistant

        prediction, probability_array = inference.predict(
            eeg_path,
            spectrogram_path,
            float(eeg_offset_seconds),
            float(spectrogram_offset_seconds),
        )

        probabilities = {
            label: float(probability_array[index])
            for index, label in enumerate(inference.LABELS)
        }
        confidence = probabilities[prediction]

        uncertainty = assistant.get_uncertainty_level(
            confidence,
            probabilities,
        )
        attention = assistant.get_attention_level(
            prediction,
            confidence,
            uncertainty,
        )

        # Prepare exactly the model's input representations for visualization.
        eeg_tensor = inference.prepare_eeg(
            eeg_path,
            float(eeg_offset_seconds),
        )
        spectrogram_tensor = inference.prepare_spectrogram(
            spectrogram_path,
            float(spectrogram_offset_seconds),
        )

        # Read a display window from the original EEG file. This is a visual
        # representation only; model preprocessing remains in inference.py.
        eeg_frame = pd.read_parquet(eeg_path)
        sample_rate = inference.EEG_SAMPLING_RATE
        window_samples = inference.EEG_WINDOW_SAMPLES
        start = int(float(eeg_offset_seconds) * sample_rate)
        display_frame = eeg_frame.iloc[start:start + window_samples]

        if display_frame.empty:
            raise ValueError(
                "The selected EEG offset is beyond the end of the recording."
            )

        eeg_signal = np.nan_to_num(
            display_frame.to_numpy(dtype=np.float32),
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        ).T

        spec_array = spectrogram_tensor.detach().cpu().numpy()

        alternatives = assistant.get_top_alternatives(
            probabilities,
            prediction,
            n=2,
        )

        return {
            "prediction": prediction,
            "confidence": confidence,
            "probabilities": probabilities,
            "uncertainty": uncertainty,
            "attention": attention,
            "alternatives": alternatives,
            "interpretation": assistant.get_interpretation(prediction),
            "uncertainty_message": assistant.get_uncertainty_message(
                prediction, confidence, probabilities
            ),
            "attention_message": assistant.get_attention_message(
                prediction, confidence, uncertainty, attention
            ),
            "eeg_signal": eeg_signal,
            "eeg_channels": list(display_frame.columns),
            "eeg_sampling_rate": sample_rate,
            "spectrogram": spec_array,
            "eeg_offset_seconds": float(eeg_offset_seconds),
            "spectrogram_offset_seconds": float(spectrogram_offset_seconds),
            "device": str(inference.device),
        }
