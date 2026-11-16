from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QSpinBox, QFrame, QButtonGroup
)


class OnboardingPage(QWidget):
    completed = Signal(str, int, str)

    def __init__(self):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(72, 48, 72, 48)
        outer.setSpacing(22)

        top = QHBoxLayout()
        brand = QLabel("N E U R A L   /   I N T E R F A C E")
        brand.setObjectName("eyebrow")
        top.addWidget(brand)
        top.addStretch()
        top.addWidget(QLabel("ICU EEG MONITORING ASSISTANT"))
        outer.addLayout(top)

        outer.addStretch(1)
        title = QLabel("Initialize patient\\nprofile")
        title.setObjectName("heroTitle")
        subtitle = QLabel("Configure a session before entering the monitoring environment.")
        subtitle.setObjectName("muted")
        outer.addWidget(title)
        outer.addWidget(subtitle)

        panel = QFrame()
        panel.setObjectName("panel")
        form = QVBoxLayout(panel)
        form.setContentsMargins(28, 26, 28, 26)
        form.setSpacing(16)

        form.addWidget(self._label("BIOLOGICAL SEX"))
        sex_row = QHBoxLayout()
        self.sex_group = QButtonGroup(self)
        self.male = QPushButton("Male")
        self.female = QPushButton("Female")
        for button, value in ((self.male, "male"), (self.female, "female")):
            button.setCheckable(True)
            button.setObjectName("choice")
            self.sex_group.addButton(button)
            button.setProperty("sex", value)
            sex_row.addWidget(button)
        self.male.setChecked(True)
        form.addLayout(sex_row)

        form.addWidget(self._label("AGE"))
        self.age = QSpinBox()
        self.age.setRange(0, 120)
        self.age.setValue(30)
        self.age.setSuffix(" years")
        form.addWidget(self.age)

        form.addWidget(self._label("PATIENT / SESSION IDENTIFIER"))
        self.patient_id = QLineEdit()
        self.patient_id.setPlaceholderText("e.g. EEG-SESSION-001")
        form.addWidget(self.patient_id)

        self.error = QLabel("")
        self.error.setObjectName("error")
        form.addWidget(self.error)

        start = QPushButton("Initialize environment  →")
        start.setObjectName("primary")
        start.clicked.connect(self._submit)
        form.addWidget(start)
        outer.addWidget(panel)
        outer.addStretch(1)

        note = QLabel("RESEARCH PROTOTYPE  •  NOT FOR CLINICAL DECISION-MAKING")
        note.setObjectName("footnote")
        outer.addWidget(note)

    def _label(self, text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _submit(self):
        patient_id = self.patient_id.text().strip() or "DEMO-SESSION"
        selected = self.sex_group.checkedButton()
        sex = selected.property("sex") if selected else "male"
        self.completed.emit(sex, self.age.value(), patient_id)
