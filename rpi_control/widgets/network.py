"""
Widget containing the network configuration and connection functionality.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
from ..utils.wifi_manager import WifiManager


# Add new ConnectionWorker class
class ConnectionWorker(QThread):
    """
    A worker thread for handling network connection operations asynchronously.

    This thread prevents the GUI from freezing during network connection attempts.
    """

    finished = pyqtSignal(bool)

    def __init__(self, wifi_manager, ssid):
        """
        Initialize the connection worker.

        Args:
            wifi_manager (WifiManager): Instance of WifiManager to handle network operations
            ssid (str): The SSID of the network to connect to
        """
        super().__init__()
        self.wifi_manager = wifi_manager
        self.ssid = ssid

    def run(self):
        """
        Execute the network connection operation in a separate thread.

        Emits:
            finished (bool): Signal emitted with True if connection successful, False otherwise
        """
        success = self.wifi_manager.connect_to_network(self.ssid)
        self.finished.emit(success)


class NetworkConfigWidget(QWidget):
    """
    A widget for managing network configuration and WiFi connections.

    Provides a user interface for scanning available networks, displaying connection
    status, and managing network connections.
    """

    def __init__(self):
        super().__init__()
        self.wifi_manager = WifiManager()
        self.initUI()

        # Create timer to update status periodically
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Update every 5 seconds

        self.connection_worker = None

    def initUI(self):
        """
        Initialize and set up the user interface components.

        Creates and arranges all UI elements including status labels, network selection
        combo box, and action buttons with appropriate styling.
        """
        layout = QVBoxLayout()
        layout.setSpacing(20)

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
        """
        Scan and update the list of available wireless networks.

        Temporarily disables the refresh button during scanning and updates
        the network combo box with newly discovered networks.
        """
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText('Scanning...')

        networks = self.wifi_manager.scan_networks()
        self.network_combo.clear()
        for network in networks:
            self.network_combo.addItem(network)

        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText('Refresh Networks')

    def connect_to_network(self):
        """
        Initiate connection to the selected wireless network.

        Creates a ConnectionWorker thread to handle the connection process
        asynchronously while updating the UI to reflect the connection attempt.
        """
        selected_network = self.network_combo.currentText()
        self.connect_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.connect_btn.setText('Connecting...')

        # Update status to show connecting
        self.status_label.setText(f'Connecting to: {selected_network}...')
        self.status_label.setStyleSheet(
            "padding: 10px; background-color: #fff3e0; border-radius: 5px;")

        # Create and start connection worker
        self.connection_worker = ConnectionWorker(
            self.wifi_manager, selected_network)
        self.connection_worker.finished.connect(self.on_connection_complete)
        self.connection_worker.start()

    def on_connection_complete(self, success):
        """
        Handle the completion of a network connection attempt.

        Args:
            success (bool): Whether the connection attempt was successful

        Re-enables UI elements and updates the connection status display.
        """
        self.connect_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.connect_btn.setText('Connect')
        self.update_status()
        self.connection_worker = None

    def update_status(self):
        """
        Update the display of the current network connection status.

        Queries the current network connection and updates the status label
        with appropriate text and styling based on the connection state.
        Handles and displays any errors that occur during the status check.
        """
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
