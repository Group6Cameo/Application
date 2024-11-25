from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPixmap
import os
import pkg_resources


class ScreenSaverWidget(QWidget):
    def __init__(self):
        super().__init__()
        # Get the absolute path to the assets directory
        assets_path = pkg_resources.resource_filename(
            'rpi_control', 'assets/screensaver.png')
        self.image = QPixmap(assets_path)

    def paintEvent(self, event):
        painter = QPainter(self)

        # Get current widget dimensions
        width = self.width()
        height = self.height()

        # Scale image to fit screen while maintaining aspect ratio
        scaled_image = self.image.scaled(width, height,
                                         Qt.KeepAspectRatio,
                                         Qt.SmoothTransformation)

        # Calculate position to center the image
        x = (width - scaled_image.width()) // 2
        y = (height - scaled_image.height()) // 2

        # Draw the image
        painter.drawPixmap(x, y, scaled_image)
