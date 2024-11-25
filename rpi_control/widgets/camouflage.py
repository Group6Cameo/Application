from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPixmap, QPalette, QColor
import os
import pkg_resources


class CamouflageWidget(QWidget):
    def __init__(self):
        super().__init__()
        # Get the absolute path to the assets directory
        assets_path = pkg_resources.resource_filename(
            'rpi_control', 'assets/camouflage.png')
        self.image = QPixmap(assets_path)

        # Set dark green background (#002103)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor('#002103'))
        self.setPalette(palette)

        # Remove any margins
        self.setContentsMargins(0, 0, 0, 0)

    def paintEvent(self, event):
        painter = QPainter(self)

        # Ensure no antialiasing or other effects
        painter.setRenderHint(QPainter.SmoothPixmapTransform, False)

        # Fill background with dark green first
        painter.fillRect(0, 0, self.width(), self.height(), QColor('#002103'))

        # Scale and draw image
        scaled_image = self.image.scaled(self.width(), self.height(),
                                         Qt.IgnoreAspectRatio,
                                         Qt.FastTransformation)
        painter.drawPixmap(0, 0, scaled_image)
