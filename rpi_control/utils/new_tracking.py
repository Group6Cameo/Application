import cv2
import dlib
import numpy as np
import face_recognition
from picamera2 import Picamera2
import time
from adafruit_servokit import ServoKit
from PyQt6.QtGui import QImage


def set_arm_position(kit, angle):
    # angle: 0 to 180
    # Motor 2 and 3 are linked: one forward, one backward
    if angle < 0 or angle > 180:
        raise ValueError("Angle must be between 0 and 180 degrees.")
    kit.servo[3].angle = angle
    kit.servo[2].angle = 180 - angle


class FaceTrackingSystem:
    def __init__(self, servo_kit):
        # Initialize camera
        try:
            self.picam2 = Picamera2()
            camera_config = self.picam2.create_video_configuration(
                main={"size": (640, 480), "format": "RGB888"},
                controls={"FrameRate": 30}
            )
            self.picam2.configure(camera_config)
            self.picam2.start()
            time.sleep(0.1)  # Give camera time to initialize
        except Exception as e:
            print(f"Camera initialization error: {e}")
            if hasattr(self, 'picam2'):
                self.picam2.close()
            raise

         # Initialize tracking variables
        self.known_face_encodings = []
        self.known_face_ids = []
        self.current_id = 1
        self.active_faces = {}  # {face_id: {'encoding': encoding, 'last_seen': timestamp}}
        self.face_to_track = 1

        # Initialize face detection and recognition models
        self.face_detector = dlib.get_frontal_face_detector()
        self.shape_predictor = dlib.shape_predictor(
            'rpi_control/utils/models/shape_predictor_68_face_landmarks.dat')
        # Parameters
        self.recognition_threshold = 0.6
        self.process_every_n_frames = 3
        self.frame_count = 0
        self.max_faces = 10

        # FPS calculation
        self.fps_frames = []
        self.fps_window = 30
        self.target_fps = 30
        self.frame_time = 1.0 / self.target_fps

        # Performance optimization
        self.process_every_n_frames = 3
        self.frame_count = 0
        self.last_process_time = time.time()

        # Frame smoothing
        self.last_frame = None
        self.smoothing_factor = 0.5

        # Frame smself.kit.servo[0].set_pulse_width_range(400, 2600)
        self.kit = servo_kit

        # Servo angles
        # Motor 1: Horizontal control (left-right), 90 is center
        self.servo1_angle = 90
        # Motor 0: Vertical partial controlPicamera2, 90 is center
        self.servo0_angle = 90
        # Arm angle for motor 2 & 3: vertical extension, 90 is center
        self.arm_angle = 90

        # Initialize servo positions
        self.kit.servo[0].angle = self.servo0_angle
        self.kit.servo[1].angle = self.servo1_angle
        set_arm_position(self.kit, self.arm_angle)

        # Deadzone parameters for each servo or arm.
        # If angle falls within this range, do not move that servo.
        # Example: 'servo0': (170,180) means angles between 170 and 180 is deadzone
        self.deadzones = {
            'servo0': (999, -1),
            'servo1': (999, -1),
            'arm': (999, -1),     # deadzone for arm angle
        }

        # Deadzone parameters for face tracking error (pixel)
        self.deadzone_x = 50
        self.deadzone_y = 50

        # Proportional control constant (adjust to change tracking speed)
        self.k_p = 0.05

        # Maximum change in angle per update (adjust to change tracking speed)
        self.servo_step = 1

    def in_deadzone(self, angle, deadzone):
        """Check if angle is within given deadzone range."""
        # If min > max, it means deadzone disabled.
        dz_min, dz_max = deadzone
        if dz_min <= dz_max:
            return dz_min <= angle <= dz_max
        return False

    def set_servo_angle_with_deadzone(self, servo_index, angle, deadzone_key):
        """Set servo angle considering the deadzone."""
        # Clamp angle to [0,180]
        angle = max(0, min(180, angle))
        if not self.in_deadzone(angle, self.deadzones[deadzone_key]):
            self.kit.servo[servo_index].angle = angle
        # If in deadzone, just do nothing (remain last angle)

    def set_arm_angle_with_deadzone(self, angle):
        """Set arm angle (servo2 & servo3) with deadzone check."""
        angle = max(0, min(180, angle))
        if not self.in_deadzone(angle, self.deadzones['arm']):
            set_arm_position(self.kit, angle)
        # If in deadzone, do not move

    def detect_faces(self, frame):
        """Use dlib to detect faces"""
        return self.face_detector(frame, 1)

    def get_face_encoding(self, frame, face):
        """Get face encoding"""
        try:
            shape = self.shape_predictor(frame, face)
            face_locations = [
                (face.top(), face.right(), face.bottom(), face.left())]
            encoding = face_recognition.face_encodings(
                frame, face_locations)[0]
            return encoding
        except:
            return None

    def find_best_match(self, encoding):
        """Find the best matching face ID"""
        if not self.known_face_encodings:
            return None

        distances = face_recognition.face_distance(
            self.known_face_encodings, encoding)
        min_distance = min(distances)

        if min_distance < self.recognition_threshold:
            return self.known_face_ids[np.argmin(distances)]
        return None

    def calculate_fps(self, current_time):
        """Calculate smooth FPS using moving average"""
        if self.fps_frames:
            time_diff = current_time - self.fps_frames[-1]
            if time_diff > 0:
                current_fps = 1.0 / time_diff
                self.fps_frames.append(current_time)

                while len(self.fps_frames) > self.fps_window:
                    self.fps_frames.pop(0)

                if len(self.fps_frames) > 1:
                    avg_fps = (len(self.fps_frames) - 1) / \
                        (self.fps_frames[-1] - self.fps_frames[0])
                    return int(avg_fps)

        self.fps_frames.append(current_time)
        return 0

    def process_frame(self):
        current_time = time.time()
        frame = self.picam2.capture_array()
        displayed_info = []

        if self.last_frame is not None:
            frame = cv2.addWeighted(frame, self.smoothing_factor,
                                    self.last_frame, 1 - self.smoothing_factor, 0)
        self.last_frame = frame.copy()

        time_since_last_process = current_time - self.last_process_time
        should_process = (self.frame_count % self.process_every_n_frames == 0 and
                          time_since_last_process >= self.frame_time)

        active_ids = set()

        if should_process:
            self.last_process_time = current_time

            faces = self.detect_faces(frame)

            for face in faces:
                x1, y1, x2, y2 = face.left(), face.top(), face.right(), face.bottom()

                encoding = self.get_face_encoding(frame, face)
                if encoding is None:
                    continue

                face_id = self.find_best_match(encoding)

                if face_id is None:
                    if len(self.known_face_encodings) < self.max_faces:
                        face_id = self.current_id
                        self.current_id += 1
                        self.known_face_encodings.append(encoding)
                        self.known_face_ids.append(face_id)
                        print(f"New face detected: ID {face_id}")

                if face_id is not None:
                    shape = self.shape_predictor(frame, face)
                    left_eye = np.mean([(shape.part(36).x, shape.part(36).y),
                                        (shape.part(37).x, shape.part(37).y),
                                        (shape.part(38).x, shape.part(38).y),
                                        (shape.part(39).x, shape.part(39).y),
                                        (shape.part(40).x, shape.part(40).y),
                                        (shape.part(41).x, shape.part(41).y)], axis=0)
                    right_eye = np.mean([(shape.part(42).x, shape.part(42).y),
                                         (shape.part(43).x, shape.part(43).y),
                                         (shape.part(44).x, shape.part(44).y),
                                         (shape.part(45).x, shape.part(45).y),
                                         (shape.part(46).x, shape.part(46).y),
                                         (shape.part(47).x, shape.part(47).y)], axis=0)

                    midpoint = ((left_eye[0] + right_eye[0]) // 2,
                                (left_eye[1] + right_eye[1]) // 2)

                    self.active_faces[face_id] = {
                        'encoding': encoding,
                        'last_seen': current_time,
                        'position': (x1, y1, x2, y2),
                        'midpoint': midpoint
                    }
                    active_ids.add(face_id)

        # Remove faces not seen recently
        self.active_faces = {
            face_id: data for face_id, data in self.active_faces.items()
            if data['last_seen'] > current_time - 0.5
        }

        y_offset = 60
        for face_id, data in self.active_faces.items():
            if current_time - data['last_seen'] < 0.5:
                x1, y1, x2, y2 = data['position']
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f'ID: {face_id}', (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                midpoint = data['midpoint']
                cv2.circle(frame, (int(midpoint[0]), int(midpoint[1])),
                           2, (0, 255, 0), -1)

                displayed_info.append(
                    (face_id, int(midpoint[0]), int(midpoint[1])))

        displayed_info.sort(key=lambda x: x[0])
        for face_id, x, y in displayed_info:
            cv2.putText(frame, f'XY{face_id}: ({x},{y})', (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            y_offset += 20

        # Servo control logic:
        # Motor1 is horizontal, Motor0 is partial vertical, Motor2&3 (via set_arm_position) is extended vertical.
        if self.face_to_track in self.active_faces:
            data = self.active_faces.get(self.face_to_track)
            midpoint = data['midpoint']
            frame_center_x = frame.shape[1] // 2
            frame_center_y = frame.shape[0] // 2
            error_x = frame_center_x - midpoint[0]
            error_y = frame_center_y - midpoint[1]

            # Initialize servo deltas
            delta_servo1 = 0
            delta_servo0 = 0

            # Check horizontal (Motor1)
            if abs(error_x) > self.deadzone_x:
                # Calculate the desired angle change
                delta_servo1 = self.k_p * error_x
                # Limit the angle change per update
                delta_servo1 = max(-self.servo_step,
                                   min(self.servo_step, delta_servo1))

            # Check vertical (Motor0 first)
            if abs(error_y) > self.deadzone_y:
                delta_servo0 = self.k_p * error_y
                delta_servo0 = max(-self.servo_step,
                                   min(self.servo_step, delta_servo0))

            # Update servo angles
            new_servo1_angle = self.servo1_angle + delta_servo1
            new_servo0_angle = self.servo0_angle - delta_servo0  # Adjust sign if needed

            # Clamp angles
            new_servo1_angle = max(0, min(180, new_servo1_angle))
            new_servo0_angle = max(0, min(180, new_servo0_angle))

            # If servo0 angle hits limit and we still need more adjustment
            # we then adjust arm_angle (for servo2 & servo3).
            # For example, if we need to go "up" (error_y < 0), and servo0=0 means top already.
            # So if we still need to move up but servo0=0, we decrease arm_angle if possible.
            # Similarly, if we need to go down (error_y > 0) and servo0=180 means bottom already,
            # we increase arm_angle.
            #
            # Logic:
            # Try moving servo0 first:
            servo0_moved = True
            if delta_servo0 < 0 and new_servo0_angle <= 0:
                # Reached top limit of servo0
                servo0_moved = False
            elif delta_servo0 > 0 and new_servo0_angle >= 180:
                # Reached bottom limit of servo0
                servo0_moved = False

            # If servo0 cannot move further, move arm
            new_arm_angle = self.arm_angle
            if not servo0_moved:
                # Need extra vertical range
                if delta_servo0 < 0 and new_servo0_angle <= 0:
                    # Need to go further up: decrease arm_angle if possible
                    arm_delta = -self.servo_step  # Move arm backward
                    new_arm_angle = max(0, self.arm_angle + arm_delta)
                elif delta_servo0 > 0 and new_servo0_angle >= 180:
                    # Need to go further down: increase arm_angle if possible
                    arm_delta = self.servo_step  # Move arm forward
                    new_arm_angle = min(180, self.arm_angle + arm_delta)
            else:
                # If servo0 can move, we move servo0 and keep arm_angle stable
                self.servo0_angle = new_servo0_angle

            # Set servo angles considering deadzone
            self.set_servo_angle_with_deadzone(
                1, new_servo1_angle, 'servo1')  # Horizontal servo
            # If servo0_moved, we set servo0 angle:
            if servo0_moved:
                self.set_servo_angle_with_deadzone(
                    0, self.servo0_angle, 'servo0')
            else:
                # If servo0 not moved, we keep servo0 angle as is, and move arm
                self.set_arm_angle_with_deadzone(new_arm_angle)
                self.arm_angle = new_arm_angle

            # Update angles in memory
            self.servo1_angle = new_servo1_angle
            # servo0_angle updated only if servo0_moved
            # arm_angle updated only if not servo0_moved

            # Display servo angles for debugging
            cv2.putText(frame, f'Servo0 Angle: {int(self.servo0_angle)}', (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
            y_offset += 20
            cv2.putText(frame, f'Servo1 Angle: {int(self.servo1_angle)}', (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
            y_offset += 20
            cv2.putText(frame, f'Arm Angle: {int(self.arm_angle)}', (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
            y_offset += 20
        else:
            # Face ID 1 not detected, do not move servos
            pass

        # Convert BGR to RGB for Qt
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.frame_count += 1
        return rgb_frame

    def run(self, frame_signal):
        self.is_running = True
        prev_frame_time = time.time()
        fps = 0

        try:
            while self.is_running:
                current_time = time.time()
                elapsed = current_time - prev_frame_time

                if elapsed < self.frame_time:
                    time.sleep(self.frame_time - elapsed)
                    current_time = time.time()

                frame = self.process_frame()

                if elapsed > 0:
                    new_fps = self.calculate_fps(current_time)
                    fps = fps * 0.9 + new_fps * 0.1 if fps > 0 else new_fps

                # Add FPS text to frame
                cv2.putText(frame, f'FPS: {int(fps)}', (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                # Convert frame to QImage and emit
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                q_image = QImage(frame.data, width, height,
                                 bytes_per_line, QImage.Format.Format_RGB888)
                frame_signal.emit(q_image)

                prev_frame_time = current_time

            self.cleanup()

        except KeyboardInterrupt:
            print("Program interrupted by user (Ctrl+C).")
            

    def stop(self):
        self.is_running = False

    def cleanup(self):
        # Move servos back to neutral positions smoothly
        steps = 10
        delay = 0.05

        for i in range(steps):
            self.servo0_angle += (90 - self.servo0_angle) / (steps - i)
            self.servo1_angle += (90 - self.servo1_angle) / (steps - i)
            self.arm_angle += (90 - self.arm_angle) / (steps - i)
            self.set_servo_angle_with_deadzone(0, self.servo0_angle, 'servo0')
            self.set_servo_angle_with_deadzone(1, self.servo1_angle, 'servo1')
            self.set_arm_angle_with_deadzone(self.arm_angle)
            time.sleep(delay)

        if hasattr(self, 'picam2'):
            if self.picam2:
                self.picam2.close()
                self.picam2 = None
        cv2.destroyAllWindows()

    # Add this method to get active faces for the UI
    def get_active_faces(self):
        return self.known_face_ids
