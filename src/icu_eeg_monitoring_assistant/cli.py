"""Console entry points for ICU EEG Monitoring Assistant."""

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"


def run_script(script):
    """Execute an existing project script as __main__."""
    import sys

    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))

    runpy.run_path(str(SRC / script), run_name="__main__")


def prepare():
    run_script("prepare_data.py")


def prepare_spectrograms():
    run_script("prepare_spectrograms.py")


def train():
    run_script("train.py")


def evaluate():
    run_script("evaluate.py")


def evaluate_fusion():
    run_script("evaluate_fusion.py")


def random_forest():
    run_script("random_forest.py")


def assistant():
    run_script("assistant.py")


def monitor():
    run_script("monitor.py")


def gui():
    run_script("gui/main.py")
