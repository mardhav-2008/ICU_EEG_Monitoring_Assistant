from pathlib import Path


class RecordingService:
    """File-selection and recording metadata helper; no clinical storage policy implied."""
    SUPPORTED_SUFFIXES = {".edf", ".bdf", ".csv", ".npy", ".npz"}

    @classmethod
    def is_supported(cls, path: str) -> bool:
        return Path(path).suffix.lower() in cls.SUPPORTED_SUFFIXES
