from __future__ import annotations


class InferenceService:
    """Adapter boundary for the repository's existing inference pipeline.

    Keep model loading and preprocessing in the existing project modules.
    Implement this adapter against their actual public API rather than
    duplicating model logic in the GUI.
    """
    def __init__(self):
        self.ready = False

    def load(self):
        raise NotImplementedError(
            "Connect this adapter to the existing src/inference.py API."
        )

    def predict(self, eeg_window, spectrogram_context):
        raise NotImplementedError(
            "Call the existing inference pipeline and return its prediction."
        )
