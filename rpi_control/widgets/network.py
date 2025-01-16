from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
from ..utils.wifi_manager import WifiManager


# Add new ConnectionWorker class
class ConnectionWorker(QThread):
    finished = pyqtSignal(bool)

    def __init__(self, wifi_manager, ssid):
        super().__init__()
        self.wifi_manager = wifi_manager
        self.ssid = ssid

    def run(self):
        success = self.wifi_manager.connect_to_network(self.ssid)
        self.finished.emit(success)


class NetworkConfigWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.wifi_manager = WifiManager()
        self.initUI()

        # Create timer to update status periodically
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Update every 5 seconds

        self.connection_worker = None  # Add this line

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)  # Increase spacing between elements

        # Status section
        self.status_label = QLabel('Connection Status: Checking...')
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 15px;
                background-color: #f0f0f0;
                border-radius: 8px;
                font-size: 16px;
            }
        """)
        layout.addWidget(self.status_label)

        # Network selection section
        network_label = QLabel('Available Networks:')
        network_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(network_label)

        self.network_combo = QComboBox()
        self.network_combo.setStyleSheet("""
            QComboBox {
                min-height: 45px;
                padding: 5px;
                font-size: 16px;
                border: 2px solid #ccc;
                border-radius: 8px;
            }
            QComboBox::drop-down {
                width: 40px;
            }
            QComboBox::down-arrow {
                width: 20px;
                height: 20px;
            }
        """)
        layout.addWidget(self.network_combo)

        # Buttons
        button_style = """
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
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """

        self.refresh_btn = QPushButton('Refresh Networks')
        self.refresh_btn.setStyleSheet(button_style)

        self.connect_btn = QPushButton('Connect')
        self.connect_btn.setStyleSheet(button_style)

        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.connect_btn)

        self.refresh_btn.clicked.connect(self.refresh_networks)
        self.connect_btn.clicked.connect(self.connect_to_network)

        # Initial status update
        self.update_status()

        self.setLayout(layout)

    def refresh_networks(self):
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText('Scanning...')

        networks = self.wifi_manager.scan_networks()
        self.network_combo.clear()
        for network in networks:
            self.network_combo.addItem(network)

        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText('Refresh Networks')

    def connect_to_network(self):
        selected_network = self.network_combo.currentText()
        self.connect_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.connect_btn.setText('Connecting...')

        # Update status to show connecting
        self.status_label.setText(f'Connecting to: {selected_network}...')
        self.status_label.setStyleSheet(
            "padding: 10px; background-color: #fff3e0; border-radius: 5px;")  # Orange background

        # Create and start connection worker
        self.connection_worker = ConnectionWorker(
            self.wifi_manager, selected_network)
        self.connection_worker.finished.connect(self.on_connection_complete)
        self.connection_worker.start()

    def on_connection_complete(self, success):
        self.connect_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.connect_btn.setText('Connect')
        self.update_status()
        self.connection_worker = None

    def update_status(self):
        try:
            current_network = self.wifi_manager.get_current_network()
            if current_network:
                self.status_label.setText(f'Connected to: {current_network}')
                self.status_label.setStyleSheet(
                    "padding: 10px; background-color: #c8e6c9; border-radius: 5px;")  # Green background
            else:
                self.status_label.setText('Not connected to any network')
                self.status_label.setStyleSheet(
                    "padding: 10px; background-color: #ffcdd2; border-radius: 5px;")  # Red background
        except Exception as e:
            self.status_label.setText(f'Error checking status: {str(e)}')
            self.status_label.setStyleSheet(
                "padding: 10px; background-color: #ffcdd2; border-radius: 5px;")  # Red background
