from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel,
                             QHBoxLayout, QComboBox, QSizePolicy)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer, QEvent
from PyQt6.QtGui import QImage, QPixmap
from adafruit_servokit import ServoKit
import cv2
import time
import csv
import subprocess
import os
import zmq
import json

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
ZMQ_FACE_IDS_PORT = "5525"


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
        target_file = os.path.join(
            self.project_root, 'rpi_control', 'utils', 'tmp', 'target_face.txt')
        os.makedirs(os.path.join(self.project_root,
                    'rpi_control', 'utils', 'tmp'), exist_ok=True)
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
                self.project_root, 'rpi_control', 'utils', 'tmp', 'target_face.txt')
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


class FaceTrackingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Add project root path
        self.project_root = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))

        layout = QVBoxLayout()

        # Add spacer to keep buttons at bottom
        spacer = QWidget()
        spacer.setMinimumHeight(400)  # Adjust height as needed
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding,
                             QSizePolicy.Policy.Expanding)
        layout.addWidget(spacer)

        # Style definitions
        self.button_style = """
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

        self.combo_style = """
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
        """

        # Update button layout with more spacing
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)  # Increase spacing between elements

        self.start_button = QPushButton("Start tracking")
        self.start_button.setStyleSheet(self.button_style)
        self.start_button.clicked.connect(self.start_tracking)

        self.stop_button = QPushButton("Stop tracking")
        self.stop_button.setStyleSheet(self.button_style)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_tracking)

        # Style the face selection combo box
        self.face_select = QComboBox()
        self.face_select.setStyleSheet(self.combo_style)

        # Style the label
        face_label = QLabel("Track Face:")
        face_label.setStyleSheet("font-size: 16px; padding: 5px;")

        button_layout.addWidget(face_label)
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

        # Add timer for updating face list from CSV
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_face_list)

        # Connect face selection change signal
        self.face_select.currentTextChanged.connect(
            self.on_face_selection_changed)

        self.is_tracking = False

        self.window_timer = QTimer()
        self.window_timer.timeout.connect(self.activate_gst_window)
        self.window_timer.setInterval(500)
        self.gst_window_id = None

        # Install event filter to catch user interactions
        self.installEventFilter(self)

        # Also install event filter on all child widgets
        for child in self.findChildren(QWidget):
            child.installEventFilter(self)

    def get_gst_window_id(self):
        """Get the window ID of gst-launch-1.0"""
        try:
            # Get window ID using wmctrl
            result = subprocess.check_output(['wmctrl', '-l']).decode()
            for line in result.split('\n'):
                if 'gst-launch-1.0' in line:
                    return line.split()[0]  # Get the window ID (first column)
        except Exception as e:
            print(f"Error getting gst window ID: {e}")
        return None

    def eventFilter(self, obj, event):
        """Handle events for user interaction detection"""
        if self.isVisible() and self.is_tracking:
            # List of events that indicate user interaction
            user_events = [
                QEvent.Type.MouseButtonPress,
                QEvent.Type.MouseButtonRelease,
                QEvent.Type.MouseButtonDblClick,
                QEvent.Type.KeyPress,
                QEvent.Type.KeyRelease,
                QEvent.Type.Wheel,
                QEvent.Type.FocusIn,
                QEvent.Type.FocusOut
            ]

            if event.type() in user_events:
                # Delay the activation slightly to ensure it happens after the user action
                QTimer.singleShot(100, self.activate_gst_window)

        # Always return False to allow the event to be handled by other handlers
        return False

    def activate_gst_window(self):
        """Activate the gst-launch window if it exists"""
        if self.gst_window_id and self.isVisible() and self.is_tracking:
            try:
                subprocess.run(['xdotool', 'windowactivate',
                               self.gst_window_id], check=False)
            except Exception as e:
                print(f"Error activating window: {e}")

    def update_face_list(self):
        """Update face list from CSV file"""
        if not self.is_tracking:
            return

        try:
            csv_path = os.path.join(
                self.project_root, 'rpi_control', 'utils', 'tmp', 'face_info_log.csv')
            if not os.path.exists(csv_path):
                print(f"CSV file not found at: {csv_path}")
                return

            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                # Skip header row
                next(reader, None)
                # Read all rows
                rows = list(reader)

                # Get unique gallery IDs from column 3 (index 3), excluding 'nd'
                face_ids = set()
                for row in rows:
                    if len(row) > 3 and row[3] != 'nd' and row[3].isdigit():
                        face_ids.add(int(row[3]))

                # If we found any valid IDs
                if face_ids:
                    # Sort the IDs numerically
                    unique_ids = sorted(list(face_ids))

                    # Get current selection
                    current_text = self.face_select.currentText()

                    # Only update if the list has changed
                    current_items = [self.face_select.itemText(
                        i) for i in range(self.face_select.count())]
                    new_items = [str(id) for id in unique_ids]

                    if current_items != new_items:
                        print(f"Updating face list with IDs: {unique_ids}")
                        self.face_select.clear()
                        self.face_select.addItems(new_items)

                        # Restore previous selection if it still exists
                        if current_text:
                            index = self.face_select.findText(current_text)
                            if index >= 0:
                                self.face_select.setCurrentIndex(index)
                            else:
                                # If previous selection is gone, select first item
                                self.face_select.setCurrentIndex(0)

        except Exception as e:
            print(f"Error updating face list: {e}")
            import traceback
            traceback.print_exc()

    def change_tracked_face(self, index):
        if self.face_tracker and index >= 0:
            face_id = int(self.face_select.currentText().split()[-1])
            self.face_tracker.face_to_track = face_id

    def start_tracking(self):
        """Start the face tracking process"""
        try:
            # Initialize the kit if not already done
            if not hasattr(self, 'kit'):
                self.kit = ServoKit(channels=16)
                self.kit.servo[0].set_pulse_width_range(400, 2600)
                self.kit.servo[1].set_pulse_width_range(400, 2600)
                self.kit.servo[2].set_pulse_width_range(400, 2600)
                self.kit.servo[3].set_pulse_width_range(400, 2600)

            # Initialize face tracker if needed
            if not hasattr(self, 'face_tracker'):
                self.face_tracker = MotorTrackingSystem(self.kit)

            # Create and start worker if not already running
            if not hasattr(self, 'worker') or not self.worker:
                self.worker = FaceTrackingWorker(self.face_tracker)
                self.worker.finished.connect(self.on_tracking_finished)
                self.worker.start()

            # Update UI
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            print("Face tracking started successfully")

        except Exception as e:
            print(f"Error starting face tracking: {e}")
            import traceback
            traceback.print_exc()

    def stop_tracking(self):
        """Stop the face tracking process"""
        try:
            if hasattr(self, 'face_tracker'):
                self.face_tracker.stop()
                self.face_tracker.cleanup()
                self.face_tracker = None

            if hasattr(self, 'worker') and self.worker:
                self.worker.quit()
                self.worker.wait()
                self.worker = None

            # Update UI
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            print("Face tracking stopped successfully")

        except Exception as e:
            print(f"Error stopping face tracking: {e}")
            import traceback
            traceback.print_exc()

    def on_tracking_finished(self):
        """Handle completion of tracking"""
        try:
            if hasattr(self, 'face_tracker'):
                self.face_tracker.cleanup()
                self.face_tracker = None

            self.worker = None
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            print("Face tracking finished successfully")

        except Exception as e:
            print(f"Error in tracking finished handler: {e}")
            import traceback
            traceback.print_exc()

    def on_face_selection_changed(self, text):
        """Handle face ID selection change"""
        try:
            if not text:  # Handle empty selection
                return

            face_id = text

            # Write the new target face ID to file
            target_file = os.path.join(
                self.project_root, 'rpi_control', 'utils', 'tmp', 'target_face.txt')
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
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

    def hideEvent(self, event):
        """Called when widget is hidden"""
        self.window_timer.stop()
        super().hideEvent(event)

    def showEvent(self, event):
        """Called when widget is shown"""
        if self.is_tracking and self.gst_window_id:
            self.window_timer.start()  # Uses the 1-second interval
            # Immediate activation when showing
            QTimer.singleShot(100, self.activate_gst_window)
        super().showEvent(event)
