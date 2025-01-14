import threading
from gi.repository import Gst, GstVideo, GLib
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel,
                             QHBoxLayout, QComboBox, QSizePolicy)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from adafruit_servokit import ServoKit
import cv2
import time
import csv
import subprocess
import os
import zmq
import json
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')

# Constants from tracking_motors.py
IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480  # Changed to match camera resolution
INITIAL_SERVO0_ANGLE = 120
INITIAL_SERVO1_ANGLE = 95
INITIAL_ARM_ANGLE = 90
DEADZONE_X = 60
DEADZONE_Y = 40
K_P = 0.5
SERVO_STEP = 1.5
CSV_PATH = 'tmp/face_info_log.csv'


class MotorTrackingSystem:
    def __init__(self, servo_kit):
        # Get the absolute path to the project root directory
        self.project_root = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))

        # Initialize servo positions and angles
        self.servo0_angle = INITIAL_SERVO0_ANGLE
        self.servo1_angle = INITIAL_SERVO1_ANGLE
        self.arm_angle = INITIAL_ARM_ANGLE

        # Set initial positions
        self.kit = servo_kit
        self.kit.servo[0].angle = self.servo0_angle
        self.kit.servo[1].angle = self.servo1_angle
        self.set_arm_position(self.arm_angle)

        # Tracking variables
        self.is_running = False
        self.face_to_track = 1  # Default face ID

        # Deadzone settings
        self.deadzones = {
            'servo0': (999, -1),
            'servo1': (999, -1),
            'arm': (999, -1)
        }

        # Process handlers
        self.tracking_process = None
        self.monitor_process = None

        # Create target face file if it doesn't exist
        target_file = os.path.join(self.project_root, 'tmp', 'target_face.txt')
        os.makedirs(os.path.join(self.project_root, 'tmp'), exist_ok=True)
        if not os.path.exists(target_file):
            with open(target_file, 'w') as f:
                f.write('1')  # Default face ID

    def in_deadzone(self, angle, deadzone):
        dz_min, dz_max = deadzone
        if dz_min <= dz_max:
            return dz_min <= angle <= dz_max
        return False

    def set_servo_angle_with_deadzone(self, servo_index, angle, deadzone_key):
        angle = max(0, min(180, angle))
        if not self.in_deadzone(angle, self.deadzones[deadzone_key]):
            self.kit.servo[servo_index].angle = angle

    def set_arm_angle_with_deadzone(self, angle):
        angle = max(0, min(180, angle))
        if not self.in_deadzone(angle, self.deadzones['arm']):
            self.set_arm_position(angle)

    def set_arm_position(self, angle):
        if angle < 0 or angle > 180:
            raise ValueError("Angle must be between 0 and 180 degrees.")
        self.kit.servo[3].angle = angle
        self.kit.servo[2].angle = 180 - angle

    def start_tracking_motors(self):
        # Get the utils directory path
        utils_dir = os.path.join(self.project_root, 'rpi_control', 'utils')

        # Start the monitor_detections.py script first
        monitor_script = os.path.join(utils_dir, 'monitor_detections.py')
        print(f"Starting monitor_detections.py from: {monitor_script}")
        self.monitor_process = subprocess.Popen(
            ['python3', monitor_script], cwd=utils_dir)
        time.sleep(2)  # Give monitor_detections time to start

        # Then start tracking_motors.py
        tracking_script = os.path.join(utils_dir, 'tracking_motors.py')
        print(f"Starting tracking_motors.py from: {tracking_script}")
        self.tracking_process = subprocess.Popen(
            ['python3', tracking_script], cwd=utils_dir)

        # Update TARGET_GALLERY_ID in tracking_motors
        if hasattr(self, 'face_to_track'):
            target_file = os.path.join(
                self.project_root, 'tmp', 'target_face.txt')
            with open(target_file, 'w') as f:
                f.write(str(self.face_to_track))

    def stop_tracking_motors(self):
        try:
            # Kill tracking Python processes
            subprocess.run(['pkill', '-f', 'tracking_motors.py'], check=False)
            subprocess.run(
                ['pkill', '-f', 'monitor_detections.py'], check=False)

            # Kill GStreamer pipeline processes
            subprocess.run(['pkill', '-f', 'gst-launch-1.0'], check=False)
            subprocess.run(['pkill', '-f', 'libcamerasrc'], check=False)

            # Clean up process references
            if self.tracking_process:
                self.tracking_process = None
            if self.monitor_process:
                self.monitor_process = None

            print("Successfully stopped all tracking and camera processes")

        except Exception as e:
            print(f"Error stopping processes: {e}")

    def run(self, frame_signal):
        self.is_running = True
        self.start_tracking_motors()

        while self.is_running:
            time.sleep(0.1)  # Keep the thread alive

    def stop(self):
        self.is_running = False
        self.stop_tracking_motors()

    def cleanup(self):
        self.stop_tracking_motors()
        # Move servos back to neutral positions smoothly
        target0, target1, targetA = 90, 90, 90
        steps = 10
        delay = 0.01

        for i in range(steps):
            self.servo0_angle += (target0 - self.servo0_angle) / (steps - i)
            self.servo1_angle += (target1 - self.servo1_angle) / (steps - i)
            self.arm_angle += (targetA - self.arm_angle) / (steps - i)

            self.set_servo_angle_with_deadzone(0, self.servo0_angle, 'servo0')
            self.set_servo_angle_with_deadzone(1, self.servo1_angle, 'servo1')
            self.set_arm_angle_with_deadzone(self.arm_angle)
            time.sleep(delay)

    def get_active_faces(self):
        """Read unique gallery IDs from CSV, excluding 'nd' values"""
        try:
            csv_path = os.path.join(
                self.project_root, 'tmp', 'face_info_log.csv')
            with open(csv_path, 'r') as f:
                rows = list(csv.reader(f))[1:]  # Skip header
                # Get unique gallery IDs, excluding 'nd', directly from rows
                face_ids = set(row[3] for row in rows if len(
                    row) > 3 and row[3] != 'nd')
                if face_ids:  # Only process if there are valid IDs
                    # Convert to integers and sort
                    return sorted([int(id) for id in face_ids if id.isdigit()])
                else:
                    return [0]  # Return default face ID if no valid IDs
        except Exception as e:
            # Silently handle file not found error
            if isinstance(e, FileNotFoundError):
                return [1]
            # Print other errors
            print(f"Error reading face IDs: {e}")
            return [0]  # Return default face ID if reading fails


class FaceTrackingWorker(QThread):
    finished = pyqtSignal()

    def __init__(self, face_tracker):
        super().__init__()
        self.face_tracker = face_tracker

    def run(self):
        self.face_tracker.run(None)
        self.finished.emit()


class VideoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self.image_label)

        # Set minimum size for the video widget
        self.setMinimumSize(640, 360)  # Match camera resolution

    def update_frame(self, image):
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(
            self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        self.image_label.setPixmap(scaled_pixmap)


class FaceTrackingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize GStreamer
        Gst.init(None)

        layout = QVBoxLayout()

        # Create video widget
        self.video_widget = VideoWidget()
        layout.addWidget(self.video_widget)

        # Create button layout
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("Start tracking")
        self.start_button.pressed.connect(self.start_tracking)

        self.stop_button = QPushButton("Stop tracking")
        self.stop_button.pressed.connect(self.stop_tracking)
        self.stop_button.setEnabled(False)

        # Add face selection combo box
        self.face_select = QComboBox()
        self.face_select.currentIndexChanged.connect(self.change_tracked_face)

        button_layout.addWidget(QLabel("Track Face:"))
        button_layout.addWidget(self.face_select)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Initialize servos
        self.kit = ServoKit(channels=16)

        self.kit.servo[0].set_pulse_width_range(400, 2600)
        self.kit.servo[1].set_pulse_width_range(400, 2600)
        self.kit.servo[2].set_pulse_width_range(400, 2600)
        self.kit.servo[3].set_pulse_width_range(400, 2600)

        self.face_tracker = None
        self.worker = None

        # Add ZMQ context for receiving face IDs
        self.zmq_context = zmq.Context()
        self.face_ids_socket = self.zmq_context.socket(zmq.SUB)
        self.face_ids_socket.connect(
            "tcp://localhost:5556")  # Use a different port
        self.face_ids_socket.setsockopt_string(zmq.SUBSCRIBE, "")

        # Timer for updating face list
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_face_list)

        self.retry_count = 0
        self.max_retries = 5

        # Connect face selection change signal
        self.face_select.currentTextChanged.connect(
            self.on_face_selection_changed)

        self.is_tracking = False  # Add tracking state flag

        # Setup GLib main loop
        self.loop = GLib.MainLoop()
        self.thread = threading.Thread(target=self.loop.run)
        self.thread.daemon = True

    def update_face_list(self):
        # Only try to update if tracking is active
        if not self.is_tracking:
            return

        try:
            if self.face_ids_socket.poll(50):
                data = self.face_ids_socket.recv_string()
                unique_ids = json.loads(data)

                if unique_ids:
                    current_text = self.face_select.currentText()
                    self.face_select.clear()
                    self.face_select.addItems(
                        [str(id) for id in sorted(unique_ids)])

                    if current_text:
                        index = self.face_select.findText(current_text)
                        if index >= 0:
                            self.face_select.setCurrentIndex(index)

                    self.retry_count = 0
                else:
                    self.handle_empty_ids()
            else:
                self.handle_empty_ids()

        except Exception as e:
            print(f"Error in update_face_list: {e}")
            self.handle_empty_ids()

    def handle_empty_ids(self):
        """Handle cases where no IDs are received"""
        if not self.is_tracking:
            return

        self.retry_count += 1
        if self.retry_count >= self.max_retries:
            print("Retrying ZMQ connection...")
            self.reinit_zmq_connection()
            self.retry_count = 0

    def reinit_zmq_connection(self):
        """Reinitialize ZMQ connection if needed"""
        try:
            # Close existing connection
            self.face_ids_socket.close()

            # Create new connection
            self.face_ids_socket = self.zmq_context.socket(zmq.SUB)
            self.face_ids_socket.connect("tcp://localhost:5556")
            self.face_ids_socket.setsockopt_string(zmq.SUBSCRIBE, "")
            print("ZMQ connection reinitialized")
        except Exception as e:
            print(f"Error reinitializing ZMQ connection: {e}")

    def change_tracked_face(self, index):
        if self.face_tracker and index >= 0:
            face_id = int(self.face_select.currentText().split()[-1])
            self.face_tracker.face_to_track = face_id

    def setup_gstreamer_pipeline(self):
        # Create pipeline similar to face_recognition.sh but with appsink
        pipeline_str = f'''
            libcamerasrc name=src_0 !
            video/x-raw,format=NV12,width=1920,height=1080,framerate=15/1 !
            queue max-size-buffers=50 max-size-bytes=0 max-size-time=0 !
            videoconvert !
            video/x-raw,format=YUY2 !
            videoscale method=1 add-borders=false !
            video/x-raw,width=640,height=360,pixel-aspect-ratio=1/1 !
            tee name=t
            t. ! queue ! videoconvert ! appsink name=preview emit-signals=true
            t. ! queue ! {self.create_detection_pipeline()}
        '''

        self.pipeline = Gst.parse_launch(pipeline_str)

        # Setup appsink for preview
        appsink = self.pipeline.get_by_name('preview')
        appsink.connect('new-sample', self.on_new_sample)

        # Setup bus
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self.on_bus_message)

    def create_detection_pipeline(self):
        # Return the detection and tracking part of the pipeline
        # (This is the same as in face_recognition.sh, but without the display sink)
        return '''videoconvert ! ... ! hailoexportzmq address="tcp://*:5555"'''

    def on_new_sample(self, appsink):
        sample = appsink.pull_sample()
        buffer = sample.get_buffer()
        caps = sample.get_caps()

        # Get width and height from caps
        caps_struct = caps.get_structure(0)
        width = caps_struct.get_value('width')
        height = caps_struct.get_value('height')

        # Create QImage from buffer
        buffer_data = buffer.extract_dup(0, buffer.get_size())
        image = QImage(buffer_data, width, height, QImage.Format.Format_RGB888)

        # Update the video widget
        self.video_widget.update_frame(image)

        return Gst.FlowReturn.OK

    def on_bus_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"Error: {err}, Debug: {debug}")
            self.stop_tracking()
        elif t == Gst.MessageType.EOS:
            print("End of stream")
            self.stop_tracking()

    def start_tracking(self):
        if not self.pipeline:
            self.setup_gstreamer_pipeline()

        # Start GLib main loop if not running
        if not self.thread.is_alive():
            self.thread.start()

        # Start pipeline
        self.pipeline.set_state(Gst.State.PLAYING)

        # Update button states
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        # Start face tracking
        if not self.face_tracker:
            self.face_tracker = MotorTrackingSystem(self.kit)

        self.worker = FaceTrackingWorker(self.face_tracker)
        self.worker.finished.connect(self.on_tracking_finished)
        self.worker.start()

        # Set tracking flag and start timer
        self.is_tracking = True
        self.retry_count = 0
        self.update_timer.start(100)

    def stop_tracking(self):
        # Stop GStreamer pipeline
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)

        # Stop GLib main loop
        if self.loop.is_running():
            self.loop.quit()

        # Rest of existing stop_tracking code...
        self.is_tracking = False
        self.update_timer.stop()
        self.retry_count = 0
        self.face_select.clear()

        if self.face_tracker:
            self.face_tracker.stop_tracking_motors()

        if self.worker and self.worker.isRunning():
            self.face_tracker.stop()
            self.worker.wait()

            if self.face_tracker:
                self.face_tracker.cleanup()
            self.face_tracker = None
            self.worker = None

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

    def on_face_selection_changed(self, text):
        """Handle face ID selection change"""
        try:
            if not text:  # Handle empty selection
                return

            # 直接使用选择的数字ID
            face_id = text  # 不再需要分割字符串

            # Write the new target face ID to file
            target_file = os.path.join(
                self.project_root, 'tmp', 'target_face.txt')
            os.makedirs(os.path.dirname(target_file), exist_ok=True)  # 确保目录存在
            with open(target_file, 'w') as f:
                f.write(face_id)

            print(f"Updated target face ID to: {face_id}")

            # Update the tracker's target face if it exists
            if hasattr(self, 'face_tracker') and self.face_tracker:
                self.face_tracker.face_to_track = int(face_id)

        except Exception as e:
            print(f"Error updating target face ID: {e}")
            import traceback
            traceback.print_exc()

    def cleanup(self):
        """Called when widget is being closed"""
        self.is_tracking = False
        self.update_timer.stop()
        self.stop_tracking()
        if hasattr(self, 'face_ids_socket'):
            self.face_ids_socket.close()
