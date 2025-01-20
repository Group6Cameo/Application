from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QPixmap, QPalette, QColor
import pkg_resources
import qrcode
from ..utils.network_info import get_ip_address, get_public_url
from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import QEvent


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
        self.setFixedSize(self.qr_pixmap.width() + 40, self.qr_pixmap.height() + 40)

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
            QTimer.singleShot(100, self._ensure_on_top)  # Use timer to ensure window activation
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
        # Create layout
        layout = QVBoxLayout()

        # Get the absolute path to the assets directory
        assets_path = pkg_resources.resource_filename(
            'rpi_control', 'assets/YOLOcalibration.png')
        self.image = QPixmap(assets_path)

        # Set dark green background (#002103)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor('#002103'))
        self.setPalette(palette)

        # Create QR code button
        self.qr_button = QPushButton("Show Upload QR Code")
        self.qr_button.clicked.connect(self.show_qr_code)
        self.qr_button.setFixedSize(200, 40)  # Set fixed size for button

        # Add button to layout
        layout.addWidget(
            self.qr_button, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        # Remove any margins for the widget itself
        self.setContentsMargins(0, 0, 0, 0)

        # Set layout margins to position button
        layout.setContentsMargins(10, 10, 10, 10)

        self.setLayout(layout)

    def show_qr_code(self):
        url = f"{get_public_url()}/static/upload.html"
        dialog = QRDialog(url)
        dialog.exec()

    def paintEvent(self, event):
        painter = QPainter(self)

        # Ensure no antialiasing or other effects
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)

        # Fill background with dark green first
        painter.fillRect(0, 0, self.width(), self.height(), QColor('#002103'))

        # Scale and draw image
        scaled_image = self.image.scaled(self.width(), self.height(),
                                         Qt.AspectRatioMode.IgnoreAspectRatio,
                                         Qt.TransformationMode.FastTransformation)
        painter.drawPixmap(0, 0, scaled_image)
