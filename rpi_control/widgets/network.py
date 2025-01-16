from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                             QComboBox, QHBoxLayout, QFrame, QScrollArea)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon
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
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Status Card
        status_card = QFrame()
        status_card.setObjectName("statusCard")
        status_card.setStyleSheet("""
            #statusCard {
                background-color: white;
                border-radius: 15px;
                padding: 15px;
                border: 1px solid #e0e0e0;
            }
        """)

        status_layout = QVBoxLayout(status_card)

        status_title = QLabel("Network Status")
        status_title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #333333;
                margin-bottom: 10px;
            }
        """)

        self.status_label = QLabel('Checking connection...')
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 15px;
                background-color: #f5f5f5;
                border-radius: 10px;
                font-size: 18px;
                color: #666666;
            }
        """)

        status_layout.addWidget(status_title)
        status_layout.addWidget(self.status_label)
        main_layout.addWidget(status_card)

        # Network Selection Card
        network_card = QFrame()
        network_card.setObjectName("networkCard")
        network_card.setStyleSheet("""
            #networkCard {
                background-color: white;
                border-radius: 15px;
                padding: 15px;
                border: 1px solid #e0e0e0;
            }
        """)

        network_layout = QVBoxLayout(network_card)

        network_title = QLabel("Available Networks")
        network_title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #333333;
                margin-bottom: 10px;
            }
        """)

        # Network Combo Box with custom styling
        self.network_combo = QComboBox()
        self.network_combo.setStyleSheet("""
            QComboBox {
                min-height: 60px;
                padding: 5px 15px;
                font-size: 18px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                background-color: #f8f9fa;
            }
            QComboBox::drop-down {
                border: none;
                width: 50px;
            }
            QComboBox::down-arrow {
                width: 25px;
                height: 25px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                selection-background-color: #4CAF50;
                font-size: 18px;
            }
        """)

        # Button Container
        button_container = QHBoxLayout()
        button_container.setSpacing(15)

        # Refresh Button
        self.refresh_btn = QPushButton('🔄 Refresh Networks')
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                min-height: 60px;
                padding: 10px 20px;
                font-size: 18px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 10px;
            }
            QPushButton:pressed {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)

        # Connect Button
        self.connect_btn = QPushButton('🔌 Connect')
        self.connect_btn.setStyleSheet("""
            QPushButton {
                min-height: 60px;
                padding: 10px 20px;
                font-size: 18px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 10px;
            }
            QPushButton:pressed {
                background-color: #388E3C;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)

        button_container.addWidget(self.refresh_btn)
        button_container.addWidget(self.connect_btn)

        network_layout.addWidget(network_title)
        network_layout.addWidget(self.network_combo)
        network_layout.addLayout(button_container)

        main_layout.addWidget(network_card)

        # Add stretch to push everything to the top
        main_layout.addStretch()

        self.refresh_btn.clicked.connect(self.refresh_networks)
        self.connect_btn.clicked.connect(self.connect_to_network)

        # Initial status update
        self.update_status()

        self.setLayout(main_layout)

    def update_status(self):
        try:
            current_network = self.wifi_manager.get_current_network()
            if current_network:
                self.status_label.setText(f'🌐 Connected to: {current_network}')
                self.status_label.setStyleSheet("""
                    QLabel {
                        padding: 15px;
                        background-color: #E8F5E9;
                        color: #2E7D32;
                        border-radius: 10px;
                        font-size: 18px;
                        font-weight: bold;
                    }
                """)
            else:
                self.status_label.setText('📡 Not connected to any network')
                self.status_label.setStyleSheet("""
                    QLabel {
                        padding: 15px;
                        background-color: #FFEBEE;
                        color: #C62828;
                        border-radius: 10px;
                        font-size: 18px;
                        font-weight: bold;
                    }
                """)
        except Exception as e:
            self.status_label.setText(f'⚠️ Error checking status: {str(e)}')
            self.status_label.setStyleSheet("""
                QLabel {
                    padding: 15px;
                    background-color: #FFF3E0;
                    color: #E65100;
                    border-radius: 10px;
                    font-size: 18px;
                    font-weight: bold;
                }
            """)

    def refresh_networks(self):
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText('🔄 Scanning...')

        networks = self.wifi_manager.scan_networks()
        self.network_combo.clear()
        for network in networks:
            self.network_combo.addItem(network)

        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText('🔄 Refresh Networks')

    def connect_to_network(self):
        selected_network = self.network_combo.currentText()
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText('🔌 Connecting...')

        success = self.wifi_manager.connect_to_network(selected_network)

        self.connect_btn.setEnabled(True)
        self.connect_btn.setText('🔌 Connect')
        self.update_status()
