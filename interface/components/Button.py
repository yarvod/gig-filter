from PyQt6 import QtGui, QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QPushButton


class Button(QPushButton):
    def __init__(self, parent):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._animation = QtCore.QVariantAnimation(
            startValue=QtGui.QColor("white"),
            endValue=QtGui.QColor("#6d72c3"),
            valueChanged=self._on_value_changed,
            duration=300,
        )
        self._update_stylesheet(QtGui.QColor("#6d72c3"), QtGui.QColor("white"))

    def _on_value_changed(self, color):
        foreground = (
            QtGui.QColor("white")
            if self._animation.direction()
            == QtCore.QAbstractAnimation.Direction.Forward
            else QtGui.QColor("#6d72c3")
        )
        self._update_stylesheet(color, foreground)

    def _update_stylesheet(self, background, foreground):
        self.setStyleSheet(
            """
        QPushButton{
            padding: 2px 10px;
            background: %s;
            color: %s;
            text-align: center;
            font: bold;
            font-size: 15px;
            border: 1px solid #6d72c3;
            border-radius: 5px;
        }
        QPushButton:disabled {
            border: 1px solid #514f59;
            color: #514f59;
            background: white;
        }
        """
            % (background.name(), foreground.name())
        )

    def enterEvent(self, event):
        self._animation.setDirection(QtCore.QAbstractAnimation.Direction.Backward)
        self._animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animation.setDirection(QtCore.QAbstractAnimation.Direction.Forward)
        self._animation.start()
        super().leaveEvent(event)
