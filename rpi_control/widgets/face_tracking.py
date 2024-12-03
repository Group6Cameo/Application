from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPixmap
from ..utils.motor_tracking_impr import FaceTrackingSystem
from adafruit_servokit import ServoKit
import time


class FaceTrackingWorker(QThread):
    frame_ready = pyqtSignal(QImage)
    finished = pyqtSignal()

    def __init__(self, face_tracker):
        super().__init__()
        self.face_tracker = face_tracker

    def run(self):
        self.face_tracker.run(self.frame_ready)
        self.finished.emit()


class FaceTrackingWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        # Create video display label
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        start_button = QPushButton("Start tracking")
        start_button.pressed.connect(self.start_tracking)

        stop_button = QPushButton("Stop tracking")
        stop_button.pressed.connect(self.stop_tracking)

        layout.addWidget(self.video_label)
        layout.addWidget(start_button)
        self.setLayout(layout)

        # Initialize servos
        self.kit = ServoKit(channels=16)
        self.kit.servo[0].angle = 90
        self.kit.servo[2].angle = 90
        time.sleep(1)

        self.kit.servo[0].set_pulse_width_range(400, 2500)
        self.kit.servo[2].set_pulse_width_range(400, 2600)
        self.servo0_angle = 90
        self.servo2_angle = 90
        self.servo_min_angle = 0
        self.servo_max_angle = 180
        self.kit.servo[0].angle = self.servo0_angle
        self.kit.servo[2].angle = self.servo2_angle

        self.face_tracker = FaceTrackingSystem(self.kit)
        self.worker = None

    def update_frame(self, qimage):
        self.video_label.setPixmap(QPixmap.fromImage(qimage))

    def start_tracking(self):
        self.worker = FaceTrackingWorker(self.face_tracker)
        self.worker.frame_ready.connect(self.update_frame)
        self.worker.finished.connect(self.on_tracking_finished)
        self.worker.start()

    def on_tracking_finished(self):
        print("Face tracking has completed.")
