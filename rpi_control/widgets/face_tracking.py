from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import QThread, pyqtSignal
from ..utils.motor_tracking_impr import FaceTrackingSystem


class FaceTrackingWorker(QThread):
    finished = pyqtSignal()

    def __init__(self, face_tracker):
        super().__init__()
        self.face_tracker = face_tracker

    def run(self):
        self.face_tracker.run()
        self.finished.emit()


class FaceTrackingWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        start_button = QPushButton("Start tracking")
        start_button.pressed.connect(self.start_tracking)
        layout.addWidget(start_button)
        self.setLayout(layout)
        self.face_tracker = FaceTrackingSystem()
        self.worker = None

    def start_tracking(self):
        print("function ran")
        self.worker = FaceTrackingWorker(self.face_tracker)
        self.worker.finished.connect(self.on_tracking_finished)
        print("here???")
        self.worker.start()

    def on_tracking_finished(self):
        print("Face tracking has completed.")
