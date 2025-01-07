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
        layout.setContentsMargins(0, 0, 0, 0)  # Remove all margins
        layout.setSpacing(0)  # Remove spacing between widgets

        # Create image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setContentsMargins(0, 0, 0, 0)  # Remove label margins
        layout.addWidget(self.image_label)

        # Set dark green background (#002103)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor('#002103'))
        self.setPalette(palette)

        # Remove any margins for the widget itself
        self.setContentsMargins(0, 0, 0, 0)

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
            latest_pattern = max(pattern_files, key=os.path.getmtime)
            pixmap = QPixmap(latest_pattern)

            # Scale pixmap to fill the entire widget
            scaled_pixmap = pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        """Handle resize events to ensure the image stays fullscreen"""
        super().resizeEvent(event)
        self.load_latest_pattern()

    def mouseDoubleClickEvent(self, event):
        """Handle double click to toggle menu"""
        # This will be connected to the main window's toggle_menu method
        if hasattr(self.parent(), 'parent') and hasattr(self.parent().parent(), 'toggle_menu'):
            self.parent().parent().toggle_menu(event)
