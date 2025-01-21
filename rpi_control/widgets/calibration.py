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
    def __init__(self, url):
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
        """Handle events to keep dialog on top"""
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
        """Helper method to ensure window stays on top"""
        self.activateWindow()
        self.raise_()
        self.show()

    def closeEvent(self, event):
        if event.spontaneous():
            event.ignore()
        else:
            super().closeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        x = (self.width() - self.qr_pixmap.width()) // 2
        y = (self.height() - self.qr_pixmap.height() - 60) // 2
        painter.drawPixmap(x, y, self.qr_pixmap)


class CalibrationWidget(QWidget):
    def __init__(self):
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

        # Start polling for server
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.check_server_status)
        self.poll_timer.start(5000)  # Check every 5 seconds
        self.check_server_status()  # Initial check

    async def _check_server_ready(self, url: str) -> bool:
        """Check if the server is responding"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return response.status == 200
        except:
            return False

    def check_server_status(self):
        """Poll the server and update UI accordingly"""
        url = f"{get_backend_url()}"

        async def check():
            is_ready = await self._check_server_ready(url)
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
        """Show the ready state UI"""
        self.loading_label.hide()
        self.progress_bar.hide()
        self.qr_button.show()

    def show_qr_code(self):
        url = f"{get_public_url()}/static/upload.html"
        dialog = QRDialog(url)
        dialog.exec()

    def paintEvent(self, event):
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
