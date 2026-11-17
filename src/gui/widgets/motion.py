"""Small motion toolkit shared by the GUI pages.

Every animation here is short, eases out, and removes its graphics effect when
it finishes so idle widgets render without extra cost.
"""
from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve, QPoint, QPropertyAnimation, QRect, QTimer, QVariantAnimation,
    Qt, Signal,
)
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QGraphicsOpacityEffect, QHBoxLayout, QPushButton,
    QStackedWidget, QWidget,
)

EASE_OUT = QEasingCurve.Type.OutCubic


def fade_in(widget: QWidget, duration: int = 360, delay: int = 0) -> None:
    """Fade a widget from transparent to opaque, then drop the effect."""
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(0.0)
    widget.setGraphicsEffect(effect)

    animation = QPropertyAnimation(effect, b"opacity", widget)
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(EASE_OUT)

    def finish():
        if widget.graphicsEffect() is effect:
            widget.setGraphicsEffect(None)

    animation.finished.connect(finish)
    QTimer.singleShot(delay, animation.start)


def stagger_in(widgets, step: int = 70, duration: int = 380) -> None:
    for index, widget in enumerate(widgets):
        fade_in(widget, duration=duration, delay=index * step)


class AnimatedStack(QStackedWidget):
    """Stacked widget whose page changes rise in from slightly below.

    Pages holding a QWebEngineView set the ``noFade`` property: a graphics
    effect on a web view breaks its compositing, so those pages only slide.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._slide = None

    def show_page(self, page: QWidget) -> None:
        if page is self.currentWidget():
            return
        self.setCurrentWidget(page)

        self._slide = QPropertyAnimation(page, b"pos", self)
        self._slide.setDuration(380)
        self._slide.setStartValue(QPoint(0, 22))
        self._slide.setEndValue(QPoint(0, 0))
        self._slide.setEasingCurve(EASE_OUT)
        self._slide.start()

        if not page.property("noFade"):
            fade_in(page, duration=300)


class PulseDot(QWidget):
    """Status dot; while active a soft ring expands from it."""

    def __init__(self, color: str = "#A7C9A8", parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self._color = QColor(color)
        self._phase = 0.0
        self._animation = QVariantAnimation(self)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setDuration(1600)
        self._animation.setLoopCount(-1)
        self._animation.valueChanged.connect(self._tick)

    def _tick(self, value):
        self._phase = float(value)
        self.update()

    def set_state(self, color: str, active: bool = False) -> None:
        self._color = QColor(color)
        if active:
            self._animation.start()
        else:
            self._animation.stop()
            self._phase = 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        center = self.rect().center()
        if self._animation.state() == QVariantAnimation.State.Running:
            ring = QColor(self._color)
            ring.setAlphaF(0.45 * (1.0 - self._phase))
            painter.setBrush(ring)
            radius = 3.5 + 4.5 * self._phase
            painter.drawEllipse(center, radius, radius)
        painter.setBrush(self._color)
        painter.drawEllipse(center, 3.5, 3.5)


class Segmented(QFrame):
    """Joined toggle group with a sliding selection pill."""

    changed = Signal(str)

    def __init__(self, options, parent=None):
        super().__init__(parent)
        self.setObjectName("segmented")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)

        self._pill = QFrame(self)
        self._pill.setObjectName("segmentPill")
        self._pill.lower()
        self._pill_animation = QPropertyAnimation(self._pill, b"geometry", self)
        self._pill_animation.setDuration(260)
        self._pill_animation.setEasingCurve(EASE_OUT)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons = {}
        for key, label in options:
            button = QPushButton(label)
            button.setObjectName("segment")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _=False, k=key: self._on_click(k))
            self._group.addButton(button)
            self._buttons[key] = button
            layout.addWidget(button)
        self._current = options[0][0]
        self._buttons[self._current].setChecked(True)

    def current(self) -> str:
        return self._current

    def set_current(self, key: str, animate: bool = True) -> None:
        if key not in self._buttons:
            return
        self._current = key
        self._buttons[key].setChecked(True)
        self._move_pill(animate)

    def _on_click(self, key):
        changed = key != self._current
        self.set_current(key)
        if changed:
            self.changed.emit(key)

    def _move_pill(self, animate):
        target = self._buttons[self._current].geometry()
        if not animate or not self.isVisible() or self._pill.width() == 0:
            self._pill_animation.stop()
            self._pill.setGeometry(target)
            return
        self._pill_animation.stop()
        self._pill_animation.setStartValue(self._pill.geometry())
        self._pill_animation.setEndValue(QRect(target))
        self._pill_animation.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._move_pill(False)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, lambda: self._move_pill(False))
