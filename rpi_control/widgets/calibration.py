"""
Calibration widget module for the RPI control system.

This module provides the widget for generating the camouflage pattern, including:
- Qr code to upload cameo's surroundings
- Calibration pattern display, used to automatically detect cameo in its surroundings
- Asynchronous serverhealth checks

To generate camouflage, scan the QR code and take a picture of the surroundings. Cameo will automatically
display the camouflage pattern once received form the server.
"""

from PyQt6.QtWidgets import (QWidget, QPushButton, QVBoxLayout,
                             QLabel, QProgressBar)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QPixmap, QPalette, QColor
import pkg_resources
import qrcode
from ..utils.network_info import get_ip_address, get_public_url
from ..utils.url_store import get_backend_url
from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import QEvent
import aiohttp
import asyncio
from functools import partial


class QRDialog(QDialog):
    """
    Modal dialog for displaying QR codes.

    A specialized dialog that displays a QR code for remote access URLs. The dialog
    remains on top of other windows and includes forced modal behavior to ensure
    visibility. It handles window focus and state changes to maintain visibility.
    """

    def __init__(self, url):
        """
        Initialize the QR code dialog.

        Args:
            url (str): The URL to encode in the QR code

        Creates a modal dialog with a QR code and close button, ensuring the
        dialog stays on top of other windows.
        """
        super().__init__()
        self.setWindowTitle("Scan QR Code")

        # Make dialog modal and force it to stay on top
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setModal(True)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")

        # Convert PIL image to QPixmap
        qr_image.save("/tmp/temp_qr.png")
        self.qr_pixmap = QPixmap("/tmp/temp_qr.png")

        # Set fixed size for dialog
        self.setFixedSize(self.qr_pixmap.width() + 40,
                          self.qr_pixmap.height() + 40)

        # Create main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # Add spacer above button
        layout.addStretch()

        # Add close button
        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            QPushButton {
                min-height: 50px;
                padding: 10px;
                font-size: 16px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                margin: 5px;
            }
            QPushButton:pressed {
                background-color: #45a049;
            }
        """)
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.setLayout(layout)

        # Install event filter
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        """
        Filter window events to maintain dialog visibility.

        Args:
            obj: The object that triggered the event
            event: The event being processed

        Returns:
            bool: True if the event was handled, False otherwise

        Ensures the dialog stays on top by intercepting window state
        and focus change events.
        """
        if event.type() in [
            QEvent.Type.WindowDeactivate,
            QEvent.Type.FocusOut,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
            QEvent.Type.MouseButtonDblClick,
            QEvent.Type.WindowStateChange  # Added this event
        ]:
            # Use timer to ensure window activation
            QTimer.singleShot(100, self._ensure_on_top)
            return True
        return super().eventFilter(obj, event)

    def _ensure_on_top(self):
        """
        Force the dialog to remain the topmost window.

        Activates the window, raises it to the top of the window stack,
        and ensures it's visible to the user.
        """
        self.activateWindow()
        self.raise_()
        self.show()

    def closeEvent(self, event):
        """
        Handle window close events.

        Args:
            event: The close event being processed

        Prevents spontaneous closing of the dialog while allowing
        programmatic closure.
        """
        if event.spontaneous():
            event.ignore()
        else:
            super().closeEvent(event)

    def paintEvent(self, event):
        """
        Handle paint events for the dialog.

        Args:
            event: The paint event being processed

        Draws the QR code pixmap centered in the dialog window with
        appropriate spacing for the close button.
        """
        painter = QPainter(self)
        x = (self.width() - self.qr_pixmap.width()) // 2
        y = (self.height() - self.qr_pixmap.height() - 60) // 2
        painter.drawPixmap(x, y, self.qr_pixmap)


class CalibrationWidget(QWidget):
    """
    Widget for system calibration and setup status display.

    Provides a user interface for:
    - Displaying calibration patterns
    - Monitoring server initialization
    - Providing QR code access to upload functionality
    - Visual feedback during system startup

    The widget automatically transitions from loading state to ready state
    once the server becomes available.
    """

    def __init__(self):
        """
        Initialize the calibration widget.

        Sets up the UI components including:
        - Loading indicator
        - Progress bar
        - QR code access button
        - Calibration pattern display
        """
        super().__init__()
        self.layout = QVBoxLayout()

        # Get the absolute path to the assets directory
        assets_path = pkg_resources.resource_filename(
            'rpi_control', 'assets/YOLOcalibration.png')
        self.image = QPixmap(assets_path)

        # Set dark green background (#002103)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor('#002103'))
        self.setPalette(palette)

        # Create loading message
        self.loading_label = QLabel("Initializing camouflage engine...")
        self.loading_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # Infinite progress bar

        # Create QR code button (initially hidden)
        self.qr_button = QPushButton("Show Upload QR Code")
        self.qr_button.clicked.connect(self.show_qr_code)
        self.qr_button.setFixedSize(200, 40)
        self.qr_button.hide()  # Initially hidden

        # Add widgets to layout
        self.layout.addWidget(self.loading_label)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(
            self.qr_button,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
        )

        # Remove margins
        self.setContentsMargins(0, 0, 0, 0)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(self.layout)

        # Check if backend URL exists and show ready state immediately if it does
        if get_backend_url():
            self.show_ready_state()
        else:
            # Only start polling if we don't have a backend URL
            self.poll_timer = QTimer()
            self.poll_timer.timeout.connect(self.check_server_status)
            self.poll_timer.start(5000)  # Check every 5 seconds
            self.check_server_status()  # Initial check

    async def _check_server_ready(self, url: str) -> bool:
        """
        Check if the server is responding and healthy.

        Args:
            url (str): The server URL to check

        Returns:
            bool: True if server is healthy, False otherwise

        Performs an asynchronous health check request to the server
        and verifies the response status.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("status") == "healthy"
        except:
            return False

    def check_server_status(self):
        """
        Poll the server status and update the UI accordingly.

        Periodically checks server health and transitions to ready state
        when the server becomes available. Creates an event loop if
        necessary for async operations.
        """
        backend_url = get_backend_url()
        if not backend_url:
            return  # Keep polling if backend URL isn't set yet

        async def check():
            is_ready = await self._check_server_ready(backend_url)
            # Use partial to safely call from async context
            if is_ready:
                self.poll_timer.stop()
                QTimer.singleShot(0, partial(self.show_ready_state))

        # Create event loop if necessary
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(check())

    def show_ready_state(self):
        """
        Transition the widget to its ready state.

        Hides the loading indicators and displays the QR code access
        button once the server is confirmed to be operational.
        """
        self.loading_label.hide()
        self.progress_bar.hide()
        self.qr_button.show()

    def show_qr_code(self):
        """
        Display the QR code dialog for remote access.

        Creates and shows a modal QR code dialog containing the public
        upload URL for remote access to the system.
        """
        url = f"{get_public_url()}/static/upload.html"
        dialog = QRDialog(url)
        dialog.exec()

    def paintEvent(self, event):
        """
        Handle paint events for the widget.

        Args:
            event: The paint event being processed

        Draws the background and calibration pattern (when in ready state)
        scaled to fit the widget dimensions.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.fillRect(0, 0, self.width(), self.height(), QColor('#002103'))

        # Only draw the calibration image if we're in ready state
        if not self.loading_label.isVisible():
            scaled_image = self.image.scaled(
                self.width(),
                self.height(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.FastTransformation
            )
            painter.drawPixmap(0, 0, scaled_image)
