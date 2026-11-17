from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout,
)

from gui.widgets.motion import fade_in

LABELS = ("Seizure", "GPD", "LRDA", "Other", "GRDA", "LPD")

LEVEL_COLORS = {
    "LOW": "#A7C9A8",
    "MODERATE": "#D2B77B",
    "HIGH": "#E3A57A",
    "CRITICAL": "#F0A18E",
}


class PredictionPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        self._animations = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)

        heading = QLabel("Model interpretation")
        heading.setObjectName("panelTitle")
        layout.addWidget(heading)

        self.result = QLabel("Awaiting EEG input")
        self.result.setObjectName("prediction")
        layout.addWidget(self.result)

        metrics = QHBoxLayout()
        metrics.setSpacing(10)
        self.confidence = self._metric(metrics, "Confidence")
        self.uncertainty = self._metric(metrics, "Uncertainty")
        self.attention = self._metric(metrics, "Attention")
        layout.addLayout(metrics)

        self.interpretation = QLabel(
            "Select an EEG recording and its spectrogram, then run inference."
        )
        self.interpretation.setWordWrap(True)
        self.interpretation.setObjectName("muted")
        layout.addWidget(self.interpretation)

        layout.addSpacing(4)
        divider = QLabel("Class probabilities")
        divider.setObjectName("fieldLabel")
        layout.addWidget(divider)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(7)
        self.probability_rows = {}
        for row, label in enumerate(LABELS):
            name = QLabel(label)
            name.setMinimumWidth(62)
            bar = QProgressBar()
            bar.setRange(0, 1000)
            bar.setValue(0)
            bar.setTextVisible(False)
            value = QLabel("—")
            value.setMinimumWidth(52)
            value.setObjectName("muted")
            grid.addWidget(name, row, 0)
            grid.addWidget(bar, row, 1)
            grid.addWidget(value, row, 2)
            self.probability_rows[label] = (bar, value)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        self.detail = QLabel("")
        self.detail.setWordWrap(True)
        self.detail.setObjectName("footnote")
        layout.addWidget(self.detail)
        layout.addStretch()

    def _metric(self, row, caption):
        box = QFrame()
        box.setObjectName("metric")
        inner = QVBoxLayout(box)
        inner.setContentsMargins(12, 9, 12, 9)
        inner.setSpacing(2)
        label = QLabel(caption)
        label.setObjectName("fieldLabel")
        value = QLabel("—")
        value.setObjectName("metricValue")
        inner.addWidget(label)
        inner.addWidget(value)
        row.addWidget(box, 1)
        return value

    def _reset_bars(self):
        for animation in self._animations:
            animation.stop()
        self._animations.clear()
        for bar, value in self.probability_rows.values():
            bar.setValue(0)
            self._set_top(bar, False)
            value.setText("—")

    @staticmethod
    def _set_top(bar, top):
        bar.setProperty("top", top)
        bar.style().unpolish(bar)
        bar.style().polish(bar)

    def _clear_metrics(self):
        for label in (self.confidence, self.uncertainty, self.attention):
            label.setText("—")
            label.setStyleSheet("")

    def set_status(self, message):
        self.result.setText(str(message))
        self._clear_metrics()
        self._reset_bars()
        self.interpretation.setText("Reading the 10-second EEG window and spectrogram…")
        self.detail.setText("")

    def set_error(self, message):
        self.result.setText("Inference failed")
        self._clear_metrics()
        self._reset_bars()
        self.interpretation.setText(str(message))
        self.detail.setText("Check the selected files and the local model checkpoint.")
        fade_in(self.result, duration=260)

    def set_prediction(self, result):
        label = result["prediction"]
        confidence = float(result["confidence"])
        self.result.setText(label)
        self.confidence.setText(f"{confidence:.1%}")

        uncertainty = str(result["uncertainty"])
        attention = str(result["attention"])
        self.uncertainty.setText(uncertainty.title())
        self.attention.setText(attention.title())
        for widget, level in ((self.uncertainty, uncertainty), (self.attention, attention)):
            color = LEVEL_COLORS.get(level.upper())
            widget.setStyleSheet(f"color: {color};" if color else "")

        self.interpretation.setText(result["interpretation"])
        fade_in(self.result, duration=320)

        self._reset_bars()
        for index, name in enumerate(LABELS):
            if name not in result["probabilities"]:
                continue
            bar, value = self.probability_rows[name]
            probability = float(result["probabilities"][name])
            value.setText(f"{probability:.1%}")
            self._set_top(bar, name == label)

            animation = QPropertyAnimation(bar, b"value", self)
            animation.setDuration(720)
            animation.setStartValue(0)
            animation.setEndValue(round(probability * 1000))
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._animations.append(animation)
            QTimer.singleShot(120 + index * 60, animation.start)

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
