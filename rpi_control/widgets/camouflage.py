from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPixmap, QPalette, QColor
import pkg_resources
from pathlib import Path
import glob
import os


class CamouflageWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        # Create image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)

        # Set dark green background (#002103)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor('#002103'))
        self.setPalette(palette)

        self.setLayout(layout)

    def showEvent(self, event):
        """Called when widget becomes visible"""
        super().showEvent(event)
        self.load_latest_pattern()

    def load_latest_pattern(self):
        """Load the most recently generated pattern"""
        pattern_dir = Path("rpi_control/assets/camouflage")
        pattern_files = glob.glob(str(pattern_dir / "pattern_*"))

        if pattern_files:
            # Get most recent file by modification time
            latest_pattern = max(pattern_files, key=os.path.getmtime)
            pixmap = QPixmap(latest_pattern)

            # Scale pixmap to fit widget while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
