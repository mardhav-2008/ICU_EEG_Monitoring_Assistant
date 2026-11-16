# ICU EEG Monitoring Assistant — GUI

A PySide6 desktop GUI scaffold with a Neka-inspired dark teal interface, a Three.js body viewer, male/female model selection, EEG visualization placeholders, and a clean adapter boundary for the existing inference pipeline.

## Included

- PySide6 desktop shell and onboarding page
- Male/female patient profile selection
- Three.js WebEngine body viewer
- Separate stylized anatomy and hologram display modes
- Brain selection bridge to the Python application
- EEG waveform, spectrogram, and prediction display placeholders
- Worker/service adapter scaffolding

## Required assets

Copy your existing model assets into `gui/web/assets/`:

```text
gui/web/assets/
├── anatomy-male.glb
├── anatomy-female.glb
└── HumanModels.glb
```

The two anatomy files are loaded by sex. The hologram GLB is expected to contain nodes named `Man (Rig)` and `Woman (Rig)` (with static `NonRig` fallback). If the downloaded GLB uses different names, inspect the node names and update `loadHumanModels()` in `web/src/body.js`.

The GUI archive does not redistribute these model files. Keep their original license and attribution with the assets. The selected Sketchfab model is CC BY 4.0 according to its listing; verify the current listing and retain creator/title/source/license attribution in your project.

## Install

From the project root:

```bash
uv add pyside6 pyside6-addons pyqtgraph numpy
```

Three.js is loaded from jsDelivr at runtime, so the first launch requires internet access. For an offline deployment, vendor the Three.js modules locally and update the import map in `web/index.html`.

## Run

From the project root, assuming this folder is at `src/gui`:

```bash
PYTHONPATH=src uv run python -m gui.main
```

## Important integration note

The GUI is deliberately not coupled to guessed backend function names. The current project inference API should be connected in `services/inference_service.py` and then invoked through `workers/inference_worker.py`. Do not duplicate preprocessing, model loading, or inference logic in the GUI.

The EEG plot and spectrogram currently show illustrative placeholder data. They are not live patient signals. The prediction panel is not connected to the model yet.

## Research-use notice

This is a research prototype, not a medical device. It is not clinically validated and must not be used for diagnosis or treatment decisions.
