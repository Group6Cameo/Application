from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor


class BrightnessOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.brightness = 100  # Start at full brightness (0 opacity)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background-color: transparent;")

    def paintEvent(self, event):
        painter = QPainter(self)
        # Convert brightness to opacity
        opacity = (100 - self.brightness) / 100.0
        painter.fillRect(self.rect(), QColor(0, 0, 0, int(opacity * 255)))

    def setBrightness(self, value):
        self.brightness = max(0, min(100, value))  # Clamp between 0 and 100
        self.update()


class BrightnessControls(QWidget):
    def __init__(self, overlay, parent=None):
        super().__init__(parent)
        self.overlay = overlay
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()

        decrease_btn = QPushButton("-")
        increase_btn = QPushButton("+")

        decrease_btn.clicked.connect(self.decreaseBrightness)
        increase_btn.clicked.connect(self.increaseBrightness)

        layout.addWidget(decrease_btn)
        layout.addWidget(increase_btn)

        self.setLayout(layout)

    def decreaseBrightness(self):
        current = self.overlay.brightness
        self.overlay.setBrightness(current - 10)

    def increaseBrightness(self):
        current = self.overlay.brightness
        self.overlay.setBrightness(current + 10)
