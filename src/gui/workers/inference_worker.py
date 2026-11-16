from PySide6.QtCore import QObject, Signal, Slot


class InferenceWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, service, eeg_window, spectrogram_context):
        super().__init__()
        self.service = service
        self.eeg_window = eeg_window
        self.spectrogram_context = spectrogram_context

    @Slot()
    def run(self):
        try:
            result = self.service.predict(self.eeg_window, self.spectrogram_context)
            self.finished.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))
