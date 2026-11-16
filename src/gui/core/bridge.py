from __future__ import annotations
from PySide6.QtCore import QObject, Signal, Slot


class BackendBridge(QObject):
    """Small, safe bridge between the WebGL scene and the Qt application.

    The current GUI scaffold does not assume a particular inference API.
    Connect your existing inference service in services/inference_service.py.
    """
    region_selected = Signal(str)

    def __init__(self):
        super().__init__()
        self.patient = {"sex": "male", "age": None, "patient_id": ""}

    def configure_patient(self, sex: str, age: int, patient_id: str):
        self.patient = {"sex": sex, "age": age, "patient_id": patient_id}

    @Slot(str)
    def selectRegion(self, region: str):
        self.region_selected.emit(region)
