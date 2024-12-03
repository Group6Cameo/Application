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

        self.start_button = QPushButton("Start tracking")
        self.start_button.pressed.connect(self.start_tracking)

        self.stop_button = QPushButton("Stop tracking")
        self.stop_button.pressed.connect(self.stop_tracking)
        self.stop_button.setEnabled(False)  # Initially disabled

        layout.addWidget(self.video_label)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        self.setLayout(layout)

        # Initialize servos
        self.kit = ServoKit(channels=16)

        self.kit.servo[0].set_pulse_width_range(400, 2500)
        self.kit.servo[2].set_pulse_width_range(400, 2600)
        self.servo0_angle = 90
        self.servo2_angle = 90
        self.servo_min_angle = 0
        self.servo_max_angle = 180
        self.kit.servo[0].angle = self.servo0_angle
        self.kit.servo[2].angle = self.servo2_angle

        self.face_tracker = None
        self.worker = None

    def update_frame(self, qimage):
        self.video_label.setPixmap(QPixmap.fromImage(qimage))

    def start_tracking(self):
        # Create a new face tracker instance if needed
        if not self.face_tracker:
            self.face_tracker = FaceTrackingSystem(self.kit)

        self.worker = FaceTrackingWorker(self.face_tracker)
        self.worker.frame_ready.connect(self.update_frame)
        self.worker.finished.connect(self.on_tracking_finished)
        self.worker.start()

        # Update button states
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_tracking(self):
        if self.worker and self.worker.isRunning():
            self.face_tracker.stop()
            self.worker.wait()
            self.video_label.clear()

            # Clean up the face tracker
            if self.face_tracker:
                self.face_tracker.cleanup()
            self.face_tracker = None
            self.worker = None

            # Update button states
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            print("Face tracking stopped.")

    def on_tracking_finished(self):
        # Clean up the face tracker
        if self.face_tracker:
            self.face_tracker.cleanup()
        self.face_tracker = None
        self.worker = None

        # Update button states
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        print("Face tracking has completed.")
