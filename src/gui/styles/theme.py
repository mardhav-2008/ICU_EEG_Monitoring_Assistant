APP_QSS = """
/* Dark liquid-glass research workstation */
QMainWindow, QWidget {
    background: #080F13;
    color: #E7F0EC;
    font-family: Inter, "Noto Sans", sans-serif;
    font-size: 13px;
}
QWidget#centralwidget {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0A1419, stop:0.48 #111D20, stop:1 #101719);
}
QLabel { color: #E7F0EC; background: transparent; }
QLabel#brand { color: #DCE9E1; font-size: 14px; font-weight: 700; }
QLabel#eyebrow, QLabel#fieldLabel {
    color: #9AB6A4;
    font-size: 12px;
    font-weight: 650;
}
QLabel#panelTitle { color: #E3EEE6; font-size: 14px; font-weight: 700; }
QLabel#metricValue { color: #E7F0EC; font-size: 15px; font-weight: 700; }
QLabel#emptyState {
    color: #8FA29A;
    background: rgba(4, 13, 17, 90);
    border: 1px dashed rgba(177, 207, 190, 55);
    border-radius: 12px;
    padding: 18px;
}
QLabel#heroTitle { color: #F0F5F1; font-size: 36px; font-weight: 700; }
QLabel#sectionTitle { color: #F0F5F1; font-size: 23px; font-weight: 700; }
QLabel#muted, QLabel#footnote { color: #9AA9A5; }
QLabel#footnote { font-size: 11px; }
QLabel#error { color: #F0A18E; }
QLabel#statusPill {
    color: #C5D9C8;
    background: rgba(139, 169, 143, 35);
    border: 1px solid rgba(184, 211, 188, 75);
    border-radius: 14px;
    padding: 7px 12px;
    font-size: 10px;
    font-weight: 750;
}
QLabel#statusText { color: #A7C9A8; font-weight: 650; }
QLabel#selectionCard {
    color: #DDECE0;
    background: rgba(125, 159, 132, 28);
    border: 1px solid rgba(171, 204, 176, 70);
    border-radius: 12px;
    padding: 16px;
    font-weight: 700;
}
QLabel#prediction { color: #C4E1C5; font-size: 27px; font-weight: 750; }
QFrame#metric {
    background: rgba(4, 13, 17, 110);
    border: 1px solid rgba(177, 207, 190, 40);
    border-radius: 10px;
}
QFrame#panel, QFrame#scenePanel {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(39, 57, 59, 224),
        stop:0.52 rgba(20, 34, 38, 232),
        stop:1 rgba(13, 24, 29, 240));
    border: 1px solid rgba(195, 220, 207, 66);
    border-top: 1px solid rgba(226, 241, 231, 105);
    border-radius: 16px;
}
QFrame#scenePanel {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(20, 39, 43, 226),
        stop:0.5 rgba(8, 21, 27, 238),
        stop:1 rgba(16, 31, 34, 226));
    border: 1px solid rgba(148, 190, 174, 95);
    border-top: 1px solid rgba(210, 237, 220, 125);
    border-radius: 18px;
}
QPushButton {
    color: #DCE9E1;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(100, 126, 111, 82), stop:1 rgba(42, 62, 58, 112));
    border: 1px solid rgba(191, 216, 199, 78);
    border-radius: 10px;
    padding: 10px 15px;
    font-weight: 600;
}
QPushButton:hover {
    background: rgba(136, 170, 145, 105);
    border: 1px solid rgba(220, 242, 225, 155);
}
QPushButton:checked {
    color: #F5FBF5;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #829E82, stop:1 #58745F);
    border: 1px solid #B4D0B5;
    font-weight: 750;
}
QPushButton#primary {
    color: #F8FCF7;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #8BA98D, stop:1 #58785F);
    border: 1px solid rgba(220, 242, 220, 145);
    border-radius: 11px;
    padding: 12px 18px;
    font-weight: 750;
}
QPushButton#primary:hover { background: #9AB99A; }
QPushButton:disabled, QPushButton#primary:disabled {
    color: rgba(220, 233, 225, 110);
    background: rgba(60, 80, 72, 90);
    border: 1px solid rgba(191, 216, 199, 40);
}
QPushButton:focus { border: 1px solid rgba(220, 242, 225, 190); }
QPushButton#ghost {
    background: transparent;
    border: 1px solid rgba(191, 216, 199, 55);
    padding: 8px 14px;
}
QPushButton#ghost:hover { background: rgba(136, 170, 145, 45); }
QFrame#segmented {
    background: rgba(4, 13, 17, 150);
    border: 1px solid rgba(177, 207, 190, 60);
    border-radius: 11px;
}
QFrame#segmentPill {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #829E82, stop:1 #58745F);
    border: 1px solid rgba(220, 242, 220, 120);
    border-radius: 8px;
}
QPushButton#segment {
    color: #A9BDB0;
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton#segment:hover { color: #E7F0EC; }
QPushButton#segment:checked { color: #F8FCF7; background: transparent; border: none; }
QLineEdit, QSpinBox, QDoubleSpinBox {
    color: #E9F1EC;
    background: rgba(4, 13, 17, 150);
    border: 1px solid rgba(177, 207, 190, 78);
    border-top: 1px solid rgba(219, 238, 224, 95);
    border-radius: 9px;
    padding: 10px;
    selection-background-color: #718F76;
}
QSpinBox, QDoubleSpinBox { padding: 0; min-height: 40px; max-height: 40px; }
/* Arrows are hidden through zero-width subcontrols: NoButtons combined with
   a stylesheet collapses the spin box's editor to 1px in Qt 6. */
QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {
    width: 0px;
    border: none;
}
QLineEdit { min-height: 20px; }
/* The editor inside a spin box must not inherit the field chrome above,
   or its padding leaves no room for the value. */
QAbstractSpinBox QLineEdit {
    padding: 0;
    border: none;
    background: transparent;
    min-height: 0;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid rgba(188, 226, 192, 190);
    background: rgba(8, 21, 23, 205);
}
QProgressBar {
    background: rgba(3, 12, 15, 170);
    border: 1px solid rgba(185, 210, 193, 42);
    border-radius: 5px;
    min-height: 9px;
    max-height: 9px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7E9A82, stop:1 #5C7861);
    border-radius: 4px;
}
QProgressBar[top="true"]::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #C9E6C6, stop:1 #8BA98D);
}
QProgressBar#busy {
    min-height: 3px;
    max-height: 3px;
    border: none;
    border-radius: 1px;
    background: rgba(3, 12, 15, 120);
}
QProgressBar#busy::chunk { background: #9DBDA0; border-radius: 1px; }
QToolTip {
    color: #F3F8F3;
    background: #1B2B2B;
    border: 1px solid #8EA991;
    padding: 5px;
}
QScrollBar:vertical { background: transparent; width: 9px; margin: 2px; }
QScrollBar::handle:vertical {
    background: rgba(173, 202, 181, 100);
    border-radius: 4px;
    min-height: 25px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""
