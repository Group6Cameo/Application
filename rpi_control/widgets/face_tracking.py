from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from ..utils.motor_tracking_impr import FaceTrackingSystem


class FaceTrackingWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        start_button = QPushButton("Start tracking")
        start_button.pressed.connect(self.run)
        layout.addWidget(start_button)
        self.setLayout(layout)
        # init face tracking
        self.face_tracker = FaceTrackingSystem()

    def run(self):
        self.face_tracker.run()
