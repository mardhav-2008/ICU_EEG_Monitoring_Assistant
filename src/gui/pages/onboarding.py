from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QSpinBox, QFrame,
)

from gui.widgets.motion import Segmented, stagger_in


class OnboardingPage(QWidget):
    completed = Signal(str, int, str)

    def __init__(self):
        super().__init__()
        self._entered = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(56, 36, 56, 32)
        outer.setSpacing(0)

        top = QHBoxLayout()
        brand = QLabel("Neural Interface")
        brand.setObjectName("brand")
        product = QLabel("ICU EEG Monitoring Assistant")
        product.setObjectName("muted")
        top.addWidget(brand)
        top.addStretch()
        top.addWidget(product)
        outer.addLayout(top)

        outer.addStretch(1)

        # Centered column: the form is short, so it reads as one block
        # instead of stretching edge to edge.
        column = QWidget()
        column.setMaximumWidth(520)
        column_layout = QVBoxLayout(column)
        column_layout.setContentsMargins(0, 0, 0, 0)
        column_layout.setSpacing(10)

        self.title = QLabel("Initialize patient profile")
        self.title.setObjectName("heroTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.subtitle = QLabel(
            "Configure a session before entering the monitoring environment."
        )
        self.subtitle.setObjectName("muted")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        column_layout.addWidget(self.title)
        column_layout.addWidget(self.subtitle)
        column_layout.addSpacing(22)

        self.panel = QFrame()
        self.panel.setObjectName("panel")
        form = QVBoxLayout(self.panel)
        form.setContentsMargins(28, 26, 28, 26)
        form.setSpacing(8)

        form.addWidget(self._label("Biological sex"))
        self.sex = Segmented([("male", "Male"), ("female", "Female")])
        form.addWidget(self.sex)
        form.addSpacing(10)

        fields = QHBoxLayout()
        fields.setSpacing(14)
        age_box = QVBoxLayout()
        age_box.setSpacing(8)
        age_box.addWidget(self._label("Age"))
        self.age = QSpinBox()
        self.age.setRange(0, 120)
        self.age.setValue(30)
        self.age.setSuffix(" years")
        self.age.setFixedWidth(130)
        self.age.lineEdit().setTextMargins(10, 0, 0, 0)
        age_box.addWidget(self.age)
        fields.addLayout(age_box)

        id_box = QVBoxLayout()
        id_box.setSpacing(8)
        id_box.addWidget(self._label("Patient / session ID"))
        self.patient_id = QLineEdit()
        self.patient_id.setPlaceholderText("e.g. EEG-SESSION-001")
        self.patient_id.returnPressed.connect(self._submit)
        id_box.addWidget(self.patient_id)
        fields.addLayout(id_box, 1)
        form.addLayout(fields)

        hint = QLabel("Leave the ID empty to start a demo session.")
        hint.setObjectName("footnote")
        form.addWidget(hint)
        form.addSpacing(14)

        start = QPushButton("Initialize environment  →")
        start.setObjectName("primary")
        start.setCursor(Qt.CursorShape.PointingHandCursor)
        start.clicked.connect(self._submit)
        form.addWidget(start)
        column_layout.addWidget(self.panel)

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(column, 1)
        row.addStretch()
        outer.addLayout(row)

        outer.addStretch(1)

        note = QLabel("Research prototype  ·  Not for clinical decision-making")
        note.setObjectName("footnote")
        note.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        outer.addWidget(note)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._entered:
            self._entered = True
            stagger_in([self.title, self.subtitle, self.panel], step=90)

    def _label(self, text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _submit(self):
        patient_id = self.patient_id.text().strip() or "DEMO-SESSION"
        self.completed.emit(self.sex.current(), self.age.value(), patient_id)
