from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox
from PyQt6.QtCore import QTimer
from ..utils.wifi_manager import WifiManager


class NetworkConfigWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.wifi_manager = WifiManager()
        self.initUI()

        # Create timer to update status periodically
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Update every 5 seconds

    def initUI(self):
        layout = QVBoxLayout()

        # Status section
        self.status_label = QLabel('Connection Status: Checking...')
        self.status_label.setStyleSheet(
            "padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(self.status_label)

        # Network selection section
        layout.addWidget(QLabel('Available Networks:'))
        self.network_combo = QComboBox()
        layout.addWidget(self.network_combo)

        # Buttons
        self.refresh_btn = QPushButton('Refresh Networks')
        self.connect_btn = QPushButton('Connect')

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
        self.connect_btn.setText('Connecting...')

        success = self.wifi_manager.connect_to_network(selected_network)

        self.connect_btn.setEnabled(True)
        self.connect_btn.setText('Connect')
        self.update_status()

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
