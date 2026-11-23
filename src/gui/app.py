from __future__ import annotations

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QMainWindow

from gui.pages.onboarding import OnboardingPage
from gui.pages.body_selection import BodySelectionPage
from gui.pages.eeg_dashboard import EEGDashboardPage
from gui.pages.coming_soon import ComingSoonPage
from gui.styles.theme import APP_QSS
from gui.widgets.motion import AnimatedStack


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neural Interface — ICU EEG Monitoring Assistant")
        self.resize(1440, 900)
        self.setMinimumSize(1080, 700)
        self.setStyleSheet(APP_QSS)

        self.stack = AnimatedStack()
        self.setCentralWidget(self.stack)

        self.onboarding = OnboardingPage()
        self.body_page = BodySelectionPage()
        self.dashboard = EEGDashboardPage()
        self.coming_soon = ComingSoonPage()

        self.stack.addWidget(self.onboarding)
        self.stack.addWidget(self.body_page)
        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.coming_soon)

        self.onboarding.completed.connect(self._on_onboarding_complete)
        self.body_page.region_selected.connect(self._on_region_selected)
        self.body_page.open_dashboard.connect(self._open_dashboard)
        self.dashboard.back_requested.connect(self._back_to_body)
        self.coming_soon.back_requested.connect(self._back_to_body)

        self.stack.setCurrentWidget(self.onboarding)

    @Slot(str, int, str)
    def _on_onboarding_complete(self, sex: str, age: int, patient_id: str):
        self.body_page.set_patient(sex, age, patient_id)
        self.stack.show_page(self.body_page)

    @Slot(str)
    def _on_region_selected(self, region: str):
        if region.lower() == "brain":
            self._open_dashboard()
        else:
            self.coming_soon.set_region(region)
            self.stack.show_page(self.coming_soon)

    def _open_dashboard(self):
        self.stack.show_page(self.dashboard)

    def _back_to_body(self):
        self.stack.show_page(self.body_page)
