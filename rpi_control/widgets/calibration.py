from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton


class CalibrationWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Calibration Screen"))

        calibrate_btn = QPushButton("Start Calibration")
        calibrate_btn.clicked.connect(self.start_calibration)
        layout.addWidget(calibrate_btn)

        self.setLayout(layout)

    def start_calibration(self):
        # Placeholder for calibration logic
        pass
