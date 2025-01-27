"""
Camouflage pattern display widget for the RPI control system.

This module provides a Qt widget for displaying dynamically generated camouflage
patterns. It automatically scales patterns to fit the display area and handles
window resizing events. The widget monitors a specified directory for new pattern
files and displays the most recently generated pattern.

Double-click to toggle the main menu.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPixmap, QPalette, QColor
import pkg_resources
from pathlib import Path
import glob
import os


class CamouflageWidget(QWidget):
    """
    A widget for displaying full-screen camouflage patterns.

    This widget monitors a directory for generated camouflage patterns and
    displays them scaled to fit the window. It maintains a dark green background
    when no pattern is available and handles window resize events to ensure
    proper pattern display.
    """

    def __init__(self):
        """
        Initialize the camouflage widget.

        Sets up the image display label and configures the widget with a dark
        green background (#002103) for use when no pattern is loaded.
        """
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
        """
        Handle widget show events.

        Args:
            event: Qt show event object

        Loads and displays the most recent camouflage pattern when the widget
        becomes visible.
        """
        super().showEvent(event)
        self.load_latest_pattern()

    def resizeEvent(self, event):
        """
        Handle widget resize events.

        Args:
            event: Qt resize event object

        Ensures the image label maintains full widget coverage and reloads
        the pattern with proper scaling when the widget is resized.
        """
        super().resizeEvent(event)
        self.image_label.setGeometry(0, 0, self.width(), self.height())
        self.load_latest_pattern()

    def load_latest_pattern(self):
        """
        Load and display the most recently generated camouflage pattern.

        Searches the camouflage assets directory for pattern files and displays
        the most recent one, scaling it to fill the entire widget while
        maintaining smooth scaling transformation.
        """
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
        """
        Handle mouse double-click events.

        Args:
            event: Qt mouse event object

        Toggles the main application menu if the parent widget supports
        the toggle_menu functionality.
        """
        if hasattr(self.parent(), 'parent') and hasattr(self.parent().parent(), 'toggle_menu'):
            self.parent().parent().toggle_menu(event)
