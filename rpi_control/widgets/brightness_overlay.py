"""
Screen brightness control module for the RPI control system (currently inactive).

This module provides a workaround solution for controlling screen brightness on
Raspberry Pi systems where direct OS-level brightness control is not available.
It implements a semi-transparent black overlay that simulates brightness adjustment
by controlling the opacity of a full-screen dark layer.

Note:
    This module is currently not in active use but remains as a potential solution
    for systems where hardware brightness control is unavailable through the
    Raspberry Pi OS.

Technical approach:
- Uses a transparent Qt widget as an overlay
- Controls perceived brightness through black overlay opacity
- Provides a simple +/- control interface for testing purposes
- Maintains brightness values between 0-100%
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor


class BrightnessOverlay(QWidget):
    """
    A transparent overlay widget that simulates screen brightness control.

    This widget creates a full-screen black overlay with adjustable opacity
    to simulate brightness changes. It's designed to be placed on top of
    other widgets while allowing mouse events to pass through to underlying
    components.
    """

    def __init__(self, parent=None):
        """
        Initialize the brightness overlay widget.

        Args:
            parent (QWidget, optional): Parent widget. Defaults to None.

        The overlay starts at 100% brightness (0% opacity) and is configured
        to be transparent to mouse events.
        """
        super().__init__(parent)
        self.brightness = 100  # Start at full brightness (0 opacity)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background-color: transparent;")

    def paintEvent(self, event):
        """
        Handle paint events for the overlay.

        Args:
            event: The paint event being processed

        Draws a black rectangle with opacity determined by the current
        brightness setting. Opacity is inversely proportional to brightness
        (e.g., 0% brightness = 100% opacity).
        """
        painter = QPainter(self)
        # Convert brightness (0-100) to opacity (255-0)
        opacity = int((100 - self.brightness) * 2.55)  # Map 0-100 to 0-255
        painter.fillRect(self.rect(), QColor(0, 0, 0, opacity))

    def setBrightness(self, value):
        """
        Set the simulated brightness level.

        Args:
            value (int): Brightness value between 0 and 100

        The brightness value is clamped between 0 (darkest) and 100 (brightest),
        where brightness controls the opacity of the black overlay.
        """
        self.brightness = max(0, min(100, value))  # Clamp between 0 and 100
        self.update()


class BrightnessControls(QWidget):
    """
    Widget providing user controls for brightness adjustment.

    Provides simple +/- buttons for incrementally adjusting the brightness
    level of the associated overlay widget. Each button press changes
    brightness by 5%.
    """

    def __init__(self, overlay, parent=None):
        """
        Initialize the brightness control widget.

        Args:
            overlay (BrightnessOverlay): The overlay widget to control
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.overlay = overlay
        self.initUI()

    def initUI(self):
        """
        Initialize the user interface components.

        Creates and arranges the increase/decrease buttons in a horizontal
        layout, connecting them to the brightness adjustment functionality.
        """
        layout = QHBoxLayout()

        decrease_btn = QPushButton("-")
        increase_btn = QPushButton("+")

        # Use smaller steps for finer control
        decrease_btn.clicked.connect(lambda: self.adjustBrightness(-5))
        increase_btn.clicked.connect(lambda: self.adjustBrightness(5))

        layout.addWidget(decrease_btn)
        layout.addWidget(increase_btn)

        self.setLayout(layout)

    def adjustBrightness(self, delta):
        """
        Adjust the brightness level by the specified amount.

        Args:
            delta (int): The amount to change brightness (-5 or +5)

        Updates the overlay's brightness setting while maintaining the
        value within the valid 0-100 range.
        """
        current = self.overlay.brightness
        self.overlay.setBrightness(current + delta)
