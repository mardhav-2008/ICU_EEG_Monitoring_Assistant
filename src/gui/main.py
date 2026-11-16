from __future__ import annotations
import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from gui.app import MainWindow


def main() -> int:
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--enable-webgl --ignore-gpu-blocklist")
    app = QApplication(sys.argv)
    app.setApplicationName("Neural Interface")
    app.setOrganizationName("ICU EEG Monitoring Assistant")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
