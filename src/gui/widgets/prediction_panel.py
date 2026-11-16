from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel


class PredictionPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        label = QLabel("MODEL OUTPUT")
        label.setObjectName("fieldLabel")
        layout.addWidget(label)
        self.result = QLabel("AWAITING EEG INPUT")
        self.result.setObjectName("prediction")
        layout.addWidget(self.result)
        self.detail = QLabel("No inference has been requested.")
        self.detail.setObjectName("muted")
        self.detail.setWordWrap(True)
        layout.addWidget(self.detail)
        layout.addStretch()

    def set_prediction(self, label, confidence=None):
        self.result.setText(str(label).upper())
        self.detail.setText(f"Confidence: {confidence:.1%}" if confidence is not None else "Prediction received.")
