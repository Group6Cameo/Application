import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QStackedWidget
from .widgets.screensaver import ScreenSaverWidget
from .widgets.network import NetworkConfigWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Raspberry Pi Control')
        self.setGeometry(0, 0, 800, 480)

        self.stacked_widget = QStackedWidget()
        self.network_widget = NetworkConfigWidget()
        self.screensaver_widget = ScreenSaverWidget()

        self.stacked_widget.addWidget(self.network_widget)
        self.stacked_widget.addWidget(self.screensaver_widget)

        self.menu_btn = QPushButton('Toggle Menu')
        self.menu_btn.clicked.connect(self.toggle_menu)

        main_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.menu_btn)
        layout.addWidget(self.stacked_widget)
        main_widget.setLayout(layout)

        self.setCentralWidget(main_widget)

    def toggle_menu(self):
        current_index = self.stacked_widget.currentIndex()
        new_index = 1 if current_index == 0 else 0
        self.stacked_widget.setCurrentIndex(new_index)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
