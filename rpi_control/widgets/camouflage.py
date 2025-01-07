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
        # Create layout without using QVBoxLayout
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Ensure the label takes up the full space
        self.image_label.setGeometry(0, 0, self.width(), self.height())

        # Set dark green background (#002103)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor('#002103'))
        self.setPalette(palette)

    def showEvent(self, event):
        """Called when widget becomes visible"""
        super().showEvent(event)
        self.load_latest_pattern()

    def resizeEvent(self, event):
        """Handle resize events to ensure the image stays fullscreen"""
        super().resizeEvent(event)
        self.image_label.setGeometry(0, 0, self.width(), self.height())
        self.load_latest_pattern()

    def load_latest_pattern(self):
        """Load the most recently generated pattern"""
        pattern_dir = Path("rpi_control/assets/camouflage")
        pattern_files = glob.glob(str(pattern_dir / "pattern_*"))

        if pattern_files:
            latest_pattern = max(pattern_files, key=os.path.getmtime)
            pixmap = QPixmap(latest_pattern)

            # Scale pixmap to fill the entire widget
            scaled_pixmap = pixmap.scaled(
                self.width(),
                self.height(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

    def mouseDoubleClickEvent(self, event):
        """Handle double click to toggle menu"""
        if hasattr(self.parent(), 'parent') and hasattr(self.parent().parent(), 'toggle_menu'):
            self.parent().parent().toggle_menu(event)
