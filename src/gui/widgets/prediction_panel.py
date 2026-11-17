from __future__ import annotations

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar


class PredictionPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(9)

        heading = QLabel("MODEL INTERPRETATION")
        heading.setObjectName("fieldLabel")
        layout.addWidget(heading)

        self.result = QLabel("AWAITING EEG INPUT")
        self.result.setObjectName("prediction")
        layout.addWidget(self.result)

        self.confidence = QLabel("Model confidence: —")
        self.confidence.setObjectName("muted")
        layout.addWidget(self.confidence)
        self.uncertainty = QLabel("Uncertainty: —")
        self.uncertainty.setObjectName("muted")
        layout.addWidget(self.uncertainty)
        self.attention = QLabel("Attention assessment: —")
        self.attention.setObjectName("muted")
        layout.addWidget(self.attention)

        self.interpretation = QLabel("Select an EEG and corresponding spectrogram recording.")
        self.interpretation.setWordWrap(True)
        self.interpretation.setObjectName("muted")
        layout.addWidget(self.interpretation)

        divider = QLabel("CLASS PROBABILITIES")
        divider.setObjectName("fieldLabel")
        layout.addWidget(divider)

        self.probability_rows = {}
        for label in ("Seizure", "GPD", "LRDA", "Other", "GRDA", "LPD"):
            row = QHBoxLayout()
            name = QLabel(label)
            name.setMinimumWidth(66)
            bar = QProgressBar()
            bar.setRange(0, 1000)
            bar.setValue(0)
            bar.setTextVisible(False)
            value = QLabel("0.0%")
            value.setMinimumWidth(48)
            value.setObjectName("muted")
            row.addWidget(name)
            row.addWidget(bar, 1)
            row.addWidget(value)
            layout.addLayout(row)
            self.probability_rows[label] = (bar, value)

        self.detail = QLabel("")
        self.detail.setWordWrap(True)
        self.detail.setObjectName("muted")
        layout.addWidget(self.detail)
        layout.addStretch()

    def set_status(self, message):
        self.result.setText(str(message).upper())

    def set_error(self, message):
        self.result.setText("INFERENCE FAILED")
        self.confidence.setText("")
        self.uncertainty.setText("")
        self.attention.setText("")
        self.interpretation.setText(str(message))
        self.detail.setText("Check the selected files and local model checkpoint.")

    def set_prediction(self, result):
        label = result["prediction"]
        confidence = float(result["confidence"])
        self.result.setText(label.upper())
        self.confidence.setText(f"Model confidence: {confidence:.1%}")
        self.uncertainty.setText(f"Uncertainty: {result['uncertainty']}")
        self.attention.setText(f"Attention assessment: {result['attention']}")
        self.interpretation.setText(result["interpretation"])

        for name, probability in result["probabilities"].items():
            bar, value = self.probability_rows[name]
            value_float = float(probability)
            bar.setValue(round(value_float * 1000))
            value.setText(f"{value_float:.1%}")

        alternatives = ", ".join(
            f"{name} ({probability:.1%})"
            for name, probability in result["alternatives"]
        )
        self.detail.setText(
            f"Alternatives: {alternatives}\n"
            f"{result['uncertainty_message']}\n"
            f"{result['attention_message']}\n"
            f"Device: {result['device']}"
        )
