from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineSettings

from gui.core.bridge import BackendBridge
from gui.widgets.motion import PulseDot, Segmented, fade_in


class BodySelectionPage(QWidget):
    region_selected = Signal(str)
    open_dashboard = Signal()
    profile_changed = Signal(str)

    def __init__(self):
        super().__init__()
        # Holds a web view: page transitions slide it but never fade it.
        self.setProperty("noFade", True)
        self.sex = "male"
        self.age = None
        self.patient_id = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(12)
        titlebox = QVBoxLayout()
        titlebox.setSpacing(4)

        title = QLabel("Select monitoring region")
        title.setObjectName("sectionTitle")
        self.header_meta = QLabel("No patient profile configured")
        self.header_meta.setObjectName("muted")

        titlebox.addWidget(title)
        titlebox.addWidget(self.header_meta)
        header.addLayout(titlebox)
        header.addStretch()

        # Plain captions name each toggle group, so nothing that is only
        # information is drawn like a button.
        header.addWidget(self._small("Profile"))
        self.profile_toggle = Segmented([("male", "Male"), ("female", "Female")])
        self.profile_toggle.changed.connect(self._change_profile)
        header.addWidget(self.profile_toggle)
        header.addSpacing(14)

        header.addWidget(self._small("View"))
        self.style_toggle = Segmented(
            [("hologram", "Hologram"), ("stylized", "Stylized anatomy")]
        )
        self.style_toggle.changed.connect(self._set_style)
        header.addWidget(self.style_toggle)
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

        side_layout.addWidget(self._small("Patient profile"))
        self.patient_summary = QLabel("No patient profile configured.")
        self.patient_summary.setWordWrap(True)
        self.patient_summary.setObjectName("muted")
        side_layout.addWidget(self.patient_summary)

        side_layout.addWidget(self._small("Anatomical overview"))
        info = QLabel(
            "Choose the brain to open the EEG monitoring workspace. "
            "Other regions are reserved for future modules."
        )
        info.setWordWrap(True)
        info.setObjectName("muted")
        side_layout.addWidget(info)

        self.selection = QLabel("No region selected")
        self.selection.setObjectName("selectionCard")
        side_layout.addWidget(self.selection)

        brain = QPushButton("Open brain monitoring  →")
        brain.setObjectName("primary")
        brain.setCursor(Qt.CursorShape.PointingHandCursor)
        brain.clicked.connect(self.open_dashboard.emit)
        side_layout.addWidget(brain)

        side_layout.addStretch()
        side_layout.addWidget(self._small("System status"))

        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        self.status_dot = PulseDot("#D2B77B")
        self.status_dot.set_state("#D2B77B", active=True)
        self.status = QLabel("3D engine initializing")
        self.status.setObjectName("statusText")
        status_row.addWidget(self.status_dot)
        status_row.addWidget(self.status)
        status_row.addStretch()
        side_layout.addLayout(status_row)

        content.addWidget(side, 1)
        layout.addLayout(content, 1)

        self.bridge.region_selected.connect(self._region_from_scene)

    def _small(self, text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _on_web_loaded(self, ok: bool):
        if not ok:
            self.status.setText("3D view failed to load")
            self.status_dot.set_state("#F0A18E")
            return

        self.status.setText("3D engine ready")
        self.status_dot.set_state("#A7C9A8")
        self._apply_profile_to_scene()

    def set_patient(self, sex, age, patient_id):
        self.sex = sex if sex in {"male", "female"} else "male"
        self.age = age
        self.patient_id = patient_id
        self._update_profile_ui()
        self._apply_profile_to_scene()

    def _update_profile_ui(self):
        self.profile_toggle.set_current(self.sex)
        self.header_meta.setText(
            f"Session {self.patient_id}  ·  {self.age} years  ·  {self.sex.title()}"
        )

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

        script = (
            "if (window.setVisualStyle) {"
            f"window.setVisualStyle({json.dumps(style)});"
            "}"
        )
        self.web.page().runJavaScript(script)

    def _region_from_scene(self, region):
        self.selection.setText(f"Selected  ·  {region.replace('_', ' ').title()}")
        fade_in(self.selection, duration=280)
        self.region_selected.emit(region)
