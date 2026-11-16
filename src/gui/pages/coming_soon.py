from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton


class ComingSoonPage(QWidget):
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.addWidget(QLabel("NEURAL INTERFACE  /  MODULE"))
        self.title = QLabel("Module reserved")
        self.title.setObjectName("heroTitle")
        layout.addWidget(self.title)
        self.description = QLabel("This anatomical region is not yet implemented.")
        self.description.setObjectName("muted")
        layout.addWidget(self.description)
        button = QPushButton("← Return to body map")
        button.clicked.connect(self.back_requested.emit)
        layout.addWidget(button)
        layout.addStretch()

    def set_region(self, region):
        self.title.setText(region.replace("_", " ").title())
        self.description.setText("NOT YET IMPLEMENTED  ·  This module is reserved for a future release.")
