from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton


class ComingSoonPage(QWidget):
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(12)
        layout.addStretch()

        self.title = QLabel("Module reserved")
        self.title.setObjectName("heroTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.title)

        self.description = QLabel("This anatomical region is not yet implemented.")
        self.description.setObjectName("muted")
        self.description.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.description)
        layout.addSpacing(16)

        button = QPushButton("←  Return to body map")
        button.setObjectName("ghost")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(self.back_requested.emit)
        layout.addWidget(button, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()

    def set_region(self, region):
        self.title.setText(region.replace("_", " ").title())
        self.description.setText(
            "Not yet implemented. This module is reserved for a future release."
        )
