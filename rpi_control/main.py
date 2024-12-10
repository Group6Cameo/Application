import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QStackedWidget, QHBoxLayout, QFrame)
from PyQt6.QtCore import Qt
from .widgets.screensaver import ScreenSaverWidget
from .widgets.network import NetworkConfigWidget
from .widgets.face_tracking import FaceTrackingWidget
from .widgets.calibration import CalibrationWidget
from .widgets.camouflage import CamouflageWidget


class MenuWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()

        # Create menu buttons
        self.wifi_btn = QPushButton("WiFi Settings")
        self.face_track_btn = QPushButton("Face Tracking")
        self.calibration_btn = QPushButton("Calibration")
        self.camouflage_btn = QPushButton("Camouflage")
        self.screensaver_btn = QPushButton("Screensaver")
        self.close_btn = QPushButton("Close")

        # Add buttons to layout
        for btn in [self.wifi_btn, self.face_track_btn,
                    self.calibration_btn, self.camouflage_btn,
                    self.screensaver_btn, self.close_btn]:
            btn.setMinimumHeight(50)
            layout.addWidget(btn)

        layout.addStretch()
        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Raspberry Pi Control')
        self.setGeometry(0, 0, 800, 480)
        self.setStyleSheet("background-color: #002103; color: #62DE00;")

        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QHBoxLayout()

        # Create menu
        self.menu_widget = MenuWidget()
        self.menu_widget.setMaximumWidth(200)
        self.menu_widget.hide()  # Initially hidden

        # Create stacked widget for different screens
        self.stacked_widget = QStackedWidget()

        # Create all screen widgets
        self.network_widget = NetworkConfigWidget()
        self.face_tracking_widget = FaceTrackingWidget()
        self.calibration_widget = CalibrationWidget()
        self.camouflage_widget = CamouflageWidget()
        self.screensaver_widget = ScreenSaverWidget()

        # Add widgets to stacked widget
        self.stacked_widget.addWidget(self.screensaver_widget)  # Index 0
        self.stacked_widget.addWidget(self.network_widget)      # Index 1
        self.stacked_widget.addWidget(self.face_tracking_widget)  # Index 2
        self.stacked_widget.addWidget(self.calibration_widget)  # Index 3
        self.stacked_widget.addWidget(self.camouflage_widget)   # Index 4

        # Connect menu buttons
        self.menu_widget.wifi_btn.clicked.connect(
            lambda: self.switch_screen(1))
        self.menu_widget.face_track_btn.clicked.connect(
            lambda: self.switch_screen(2))
        self.menu_widget.calibration_btn.clicked.connect(
            lambda: self.switch_screen(3))
        self.menu_widget.camouflage_btn.clicked.connect(
            lambda: self.switch_screen(4))
        self.menu_widget.screensaver_btn.clicked.connect(
            lambda: self.switch_screen(0))
        self.menu_widget.close_btn.clicked.connect(self.close_app)
        

        # Add widgets to main layout
        main_layout.addWidget(self.menu_widget)
        main_layout.addWidget(self.stacked_widget)
        main_widget.setLayout(main_layout)

        self.setCentralWidget(main_widget)

        # Setup double-click event for screensaver
        self.screensaver_widget.mouseDoubleClickEvent = self.toggle_menu
        self.calibration_widget.mouseDoubleClickEvent = self.toggle_menu

    def switch_screen(self, index):
        self.stacked_widget.setCurrentIndex(index)
        if index == 0:  # If switching to screensaver
            self.menu_widget.hide()

    def toggle_menu(self, event=None):
        if self.menu_widget.isHidden():
            self.menu_widget.show()
        else:
            self.menu_widget.hide()
    def close_app(self):
        sys.exit(0)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
