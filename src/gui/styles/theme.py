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
QLabel#eyebrow, QLabel#fieldLabel {
    color: #9AB6A4;
    font-size: 10px;
    font-weight: 750;
    letter-spacing: 1.7px;
}
QLabel#heroTitle { color: #F0F5F1; font-size: 40px; font-weight: 650; }
QLabel#sectionTitle { color: #F0F5F1; font-size: 23px; font-weight: 700; }
QLabel#muted, QLabel#footnote { color: #9AA9A5; }
QLabel#footnote { font-size: 10px; letter-spacing: .5px; }
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
QPushButton#choice { min-width: 100px; padding: 14px; }
QLineEdit, QSpinBox, QDoubleSpinBox {
    color: #E9F1EC;
    background: rgba(4, 13, 17, 150);
    border: 1px solid rgba(177, 207, 190, 78);
    border-top: 1px solid rgba(219, 238, 224, 95);
    border-radius: 9px;
    padding: 10px;
    selection-background-color: #718F76;
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
        stop:0 #9DBDA0, stop:1 #69866C);
    border-radius: 4px;
}
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
