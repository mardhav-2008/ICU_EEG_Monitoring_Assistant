from pathlib import Path
from PySide6.QtCore import Signal, QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineSettings

from gui.core.bridge import BackendBridge


class BodySelectionPage(QWidget):
    region_selected = Signal(str)
    open_dashboard = Signal()

    def __init__(self):
        super().__init__()
        self.sex = "male"
        self.bridge = BackendBridge()
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
        self.stylized_button = QPushButton("Stylized anatomy")
        self.stylized_button.setCheckable(True)
        self.stylized_button.clicked.connect(lambda: self._set_style("stylized"))
        self.holo_button = QPushButton("Hologram")
        self.holo_button.setCheckable(True)
        self.holo_button.setChecked(True)
        self.holo_button.clicked.connect(lambda: self._set_style("hologram"))
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
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        channel = QWebChannel(self.web.page())
        channel.registerObject("backend", self.bridge)
        self.web.page().setWebChannel(channel)
        self.web.load(QUrl.fromLocalFile(str(Path(__file__).parents[1] / "web" / "index.html")))
        scene_layout.addWidget(self.web)
        content.addWidget(scene_panel, 4)

        side = QFrame()
        side.setObjectName("panel")
        side.setMinimumWidth(270)
        side.setMaximumWidth(340)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(22, 22, 22, 22)
        side_layout.setSpacing(14)
        side_layout.addWidget(self._small("ANATOMICAL OVERVIEW"))
        info = QLabel("Choose the brain to open the EEG monitoring workspace. Other regions are reserved for future modules.")
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

    def _small(self, text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def set_patient(self, sex, age, patient_id):
        self.sex = sex
        self.sex_label.setText(f"{sex.upper()} PROFILE")
        self.web.page().runJavaScript(f"window.setPatientSex && window.setPatientSex({json_string(sex)});")

    def _set_style(self, style):
        self.holo_button.setChecked(style == "hologram")
        self.stylized_button.setChecked(style == "stylized")
        self.web.page().runJavaScript(f"window.setVisualStyle && window.setVisualStyle({json_string(style)});")

    def _region_from_scene(self, region):
        self.selection.setText(f"SELECTED  /  {region.upper()}")
        self.region_selected.emit(region)


def json_string(value):
    import json
    return json.dumps(value)
