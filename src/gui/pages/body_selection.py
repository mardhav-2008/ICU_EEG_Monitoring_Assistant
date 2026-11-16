from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Signal, QUrl
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineSettings

from gui.core.bridge import BackendBridge


class BodySelectionPage(QWidget):
    region_selected = Signal(str)
    open_dashboard = Signal()
    profile_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.sex = "male"
        self.age = None
        self.patient_id = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        titlebox = QVBoxLayout()

        eyebrow = QLabel("NEURAL INTERFACE  /  BODY MAP")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("Select monitoring region")
        title.setObjectName("sectionTitle")

        titlebox.addWidget(eyebrow)
        titlebox.addWidget(title)
        header.addLayout(titlebox)
        header.addStretch()

        self.sex_label = QLabel("MALE PROFILE")
        self.sex_label.setObjectName("statusPill")
        header.addWidget(self.sex_label)

        self.male_button = QPushButton("Male")
        self.male_button.setCheckable(True)
        self.male_button.clicked.connect(lambda: self._change_profile("male"))

        self.female_button = QPushButton("Female")
        self.female_button.setCheckable(True)
        self.female_button.clicked.connect(lambda: self._change_profile("female"))

        self.profile_group = [self.male_button, self.female_button]
        header.addWidget(self.male_button)
        header.addWidget(self.female_button)

        self.stylized_button = QPushButton("Stylized anatomy")
        self.stylized_button.setCheckable(True)
        self.stylized_button.clicked.connect(
            lambda: self._set_style("stylized")
        )

        self.holo_button = QPushButton("Hologram")
        self.holo_button.setCheckable(True)
        self.holo_button.setChecked(True)
        self.holo_button.clicked.connect(
            lambda: self._set_style("hologram")
        )

        header.addWidget(self.stylized_button)
        header.addWidget(self.holo_button)
        layout.addLayout(header)

        content = QHBoxLayout()

        scene_panel = QFrame()
        scene_panel.setObjectName("scenePanel")
        scene_layout = QVBoxLayout(scene_panel)
        scene_layout.setContentsMargins(0, 0, 0, 0)

        self.web = QWebEngineView()
        settings = self.web.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
            True,
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls,
            True,
        )

        self.bridge = BackendBridge()
        self.channel = QWebChannel(self.web.page())
        self.channel.registerObject("backend", self.bridge)
        self.web.page().setWebChannel(self.channel)

        self.web.loadFinished.connect(self._on_web_loaded)
        self.web.load(
            QUrl.fromLocalFile(
                str(Path(__file__).parents[1] / "web" / "index.html")
            )
        )

        scene_layout.addWidget(self.web)
        content.addWidget(scene_panel, 4)

        side = QFrame()
        side.setObjectName("panel")
        side.setMinimumWidth(270)
        side.setMaximumWidth(340)

        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(22, 22, 22, 22)
        side_layout.setSpacing(14)

        side_layout.addWidget(self._small("PATIENT PROFILE"))
        self.patient_summary = QLabel("No patient profile configured.")
        self.patient_summary.setWordWrap(True)
        self.patient_summary.setObjectName("muted")
        side_layout.addWidget(self.patient_summary)

        side_layout.addWidget(self._small("ANATOMICAL OVERVIEW"))
        info = QLabel(
            "Choose the brain to open the EEG monitoring workspace. "
            "Other regions are reserved for future modules."
        )
        info.setWordWrap(True)
        info.setObjectName("muted")
        side_layout.addWidget(info)

        self.selection = QLabel("NO REGION SELECTED")
        self.selection.setObjectName("selectionCard")
        side_layout.addWidget(self.selection)

        brain = QPushButton("Open brain monitoring  →")
        brain.setObjectName("primary")
        brain.clicked.connect(self.open_dashboard.emit)
        side_layout.addWidget(brain)

        side_layout.addStretch()
        side_layout.addWidget(self._small("SYSTEM STATUS"))

        self.status = QLabel("●  3D ENGINE INITIALIZING")
        self.status.setObjectName("statusText")
        side_layout.addWidget(self.status)

        content.addWidget(side, 1)
        layout.addLayout(content, 1)

        self.bridge.region_selected.connect(self._region_from_scene)
        self.male_button.setChecked(True)

    def _small(self, text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _on_web_loaded(self, ok: bool):
        if not ok:
            self.status.setText("●  3D VIEW FAILED TO LOAD")
            return

        self.status.setText("●  3D ENGINE READY")
        self._apply_profile_to_scene()

    def set_patient(self, sex, age, patient_id):
        self.sex = sex if sex in {"male", "female"} else "male"
        self.age = age
        self.patient_id = patient_id
        self._update_profile_ui()
        self._apply_profile_to_scene()

    def _update_profile_ui(self):
        self.sex_label.setText(f"{self.sex.upper()} PROFILE")
        self.male_button.setChecked(self.sex == "male")
        self.female_button.setChecked(self.sex == "female")

        self.patient_summary.setText(
            f"Session: {self.patient_id}\n"
            f"Age: {self.age} years\n"
            f"Profile: {self.sex.title()}"
        )

    def _change_profile(self, sex):
        if sex not in {"male", "female"} or sex == self.sex:
            self._update_profile_ui()
            return

        self.sex = sex
        self._update_profile_ui()
        self._apply_profile_to_scene()
        self.profile_changed.emit(sex)

    def _apply_profile_to_scene(self):
        # loadFinished may fire before the JS module has defined the function.
        script = (
            "if (window.setPatientSex) {"
            f"window.setPatientSex({json.dumps(self.sex)});"
            "}"
        )
        self.web.page().runJavaScript(script)

    def _set_style(self, style):
        self.holo_button.setChecked(style == "hologram")
        self.stylized_button.setChecked(style == "stylized")

        script = (
            "if (window.setVisualStyle) {"
            f"window.setVisualStyle({json.dumps(style)});"
            "}"
        )
        self.web.page().runJavaScript(script)

    def _region_from_scene(self, region):
        self.selection.setText(f"SELECTED  /  {region.upper()}")
        self.region_selected.emit(region)
