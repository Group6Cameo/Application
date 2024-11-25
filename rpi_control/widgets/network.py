from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox
from ..utils.wifi_manager import WifiManager


class NetworkConfigWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.wifi_manager = WifiManager()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.network_combo = QComboBox()
        self.refresh_btn = QPushButton('Refresh Networks')
        self.connect_btn = QPushButton('Connect')

        layout.addWidget(QLabel('Available Networks:'))
        layout.addWidget(self.network_combo)
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.connect_btn)

        self.refresh_btn.clicked.connect(self.refresh_networks)
        self.connect_btn.clicked.connect(self.connect_to_network)

        self.setLayout(layout)

    def refresh_networks(self):
        networks = self.wifi_manager.scan_networks()
        self.network_combo.clear()
        for network in networks:
            self.network_combo.addItem(network)

    def connect_to_network(self):
        selected_network = self.network_combo.currentText()
        self.wifi_manager.connect_to_network(selected_network)
