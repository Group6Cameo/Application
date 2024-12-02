import cv2
import dlib
import numpy as np
import face_recognition
from picamera2 import Picamera2
# import time
# from adafruit_servokit import ServoKit


class FaceTrackingSystem:
    def __init__(self):
        print("started hahaha")
    #     # Initialize camera
    #     self.picam2 = Picamera2()
    #     camera_config = self.picam2.create_video_configuration(
    #         main={"size": (640, 480), "format": "RGB888"},
    #         controls={"FrameRate": 30}
    #     )
    #     self.picam2.configure(camera_config)
    #     self.picam2.start()

    #     # Initialize face detection and recognition models
    #     self.face_detector = dlib.get_frontal_face_detector()
    #     self.shape_predictor = dlib.shape_predictor(
    #         'shape_predictor_68_face_landmarks.dat')

    #     # Initialize tracking variables
    #     self.known_face_encodings = []
    #     self.known_face_ids = []
    #     self.current_id = 1
    #     self.active_faces = {}  # {face_id: {'encoding': encoding, 'last_seen': timestamp}}

    #     # Parameters
    #     self.recognition_threshold = 0.6
    #     self.process_every_n_frames = 3
    #     self.frame_count = 0
    #     self.max_faces = 10

    #     # FPS calculation
    #     self.fps_frames = []
    #     self.fps_window = 30
    #     self.target_fps = 30
    #     self.frame_time = 1.0 / self.target_fps

    #     # Performance optimization
    #     self.process_every_n_frames = 3
    #     self.frame_count = 0
    #     self.last_process_time = time.time()

    #     # Frame smoothing
    #     self.last_frame = None
    #     self.smoothing_factor = 0.5

    #     # Initialize servos
    #     self.kit = ServoKit(channels=16)
    #     self.kit.servo[0].set_pulse_width_range(400, 2500)
    #     self.kit.servo[2].set_pulse_width_range(400, 2600)
    #     self.servo0_angle = 90  # Up/Down servo angle
    #     self.servo2_angle = 90  # Left/Right servo angle
    #     self.servo_min_angle = 0
    #     self.servo_max_angle = 180
    #     self.kit.servo[0].angle = self.servo0_angle
    #     self.kit.servo[2].angle = self.servo2_angle

    #     # Deadzone parameters (adjust these to change the deadzone size)
    #     self.deadzone_x = 50
    #     self.deadzone_y = 50

    #     # Proportional control constant (adjust to change tracking speed)
    #     self.k_p = 0.05

    #     # Maximum change in angle per update (adjust to change tracking speed)
    #     self.servo_step = 1

    # def detect_faces(self, frame):
    #     """Use dlib to detect faces"""
    #     return self.face_detector(frame, 1)

    # def get_face_encoding(self, frame, face):
    #     """Get face encoding"""
    #     try:
    #         shape = self.shape_predictor(frame, face)
    #         face_locations = [
    #             (face.top(), face.right(), face.bottom(), face.left())]
    #         encoding = face_recognition.face_encodings(
    #             frame, face_locations)[0]
    #         return encoding
    #     except:
    #         return None

    # def find_best_match(self, encoding):
    #     """Find the best matching face ID"""
    #     if not self.known_face_encodings:
    #         return None

    #     distances = face_recognition.face_distance(
    #         self.known_face_encodings, encoding)
    #     min_distance = min(distances)

    #     if min_distance < self.recognition_threshold:
    #         return self.known_face_ids[np.argmin(distances)]
    #     return None

    # def calculate_fps(self, current_time):
    #     """Calculate smooth FPS using moving average"""
    #     if self.fps_frames:
    #         time_diff = current_time - self.fps_frames[-1]
    #         if time_diff > 0:
    #             current_fps = 1.0 / time_diff
    #             self.fps_frames.append(current_time)

    #             while len(self.fps_frames) > self.fps_window:
    #                 self.fps_frames.pop(0)

    #             if len(self.fps_frames) > 1:
    #                 avg_fps = (len(self.fps_frames) - 1) / \
    #                     (self.fps_frames[-1] - self.fps_frames[0])
    #                 return int(avg_fps)

    #     self.fps_frames.append(current_time)
    #     return 0

    # def process_frame(self):
    #     current_time = time.time()
    #     frame = self.picam2.capture_array()
    #     displayed_info = []

    #     if self.last_frame is not None:
    #         frame = cv2.addWeighted(frame, self.smoothing_factor,
    #                                 self.last_frame, 1 - self.smoothing_factor, 0)
    #     self.last_frame = frame.copy()

    #     time_since_last_process = current_time - self.last_process_time
    #     should_process = (self.frame_count % self.process_every_n_frames == 0 and
    #                       time_since_last_process >= self.frame_time)

    #     active_ids = set()

    #     if should_process:
    #         self.last_process_time = current_time

    #         faces = self.detect_faces(frame)

    #         for face in faces:
    #             x1, y1, x2, y2 = face.left(), face.top(), face.right(), face.bottom()

    #             encoding = self.get_face_encoding(frame, face)
    #             if encoding is None:
    #                 continue

    #             face_id = self.find_best_match(encoding)

    #             if face_id is None:
    #                 if len(self.known_face_encodings) < self.max_faces:
    #                     face_id = self.current_id
    #                     self.current_id += 1
    #                     self.known_face_encodings.append(encoding)
    #                     self.known_face_ids.append(face_id)
    #                     print(f"New face detected: ID {face_id}")

    #             if face_id is not None:
    #                 shape = self.shape_predictor(frame, face)
    #                 left_eye = np.mean([(shape.part(36).x, shape.part(36).y),
    #                                     (shape.part(37).x, shape.part(37).y),
    #                                     (shape.part(38).x, shape.part(38).y),
    #                                     (shape.part(39).x, shape.part(39).y),
    #                                     (shape.part(40).x, shape.part(40).y),
    #                                     (shape.part(41).x, shape.part(41).y)], axis=0)
    #                 right_eye = np.mean([(shape.part(42).x, shape.part(42).y),
    #                                      (shape.part(43).x, shape.part(43).y),
    #                                      (shape.part(44).x, shape.part(44).y),
    #                                      (shape.part(45).x, shape.part(45).y),
    #                                      (shape.part(46).x, shape.part(46).y),
    #                                      (shape.part(47).x, shape.part(47).y)], axis=0)

    #                 midpoint = ((left_eye[0] + right_eye[0]) // 2,
    #                             (left_eye[1] + right_eye[1]) // 2)

    #                 self.active_faces[face_id] = {
    #                     'encoding': encoding,
    #                     'last_seen': current_time,
    #                     'position': (x1, y1, x2, y2),
    #                     'midpoint': midpoint
    #                 }
    #                 active_ids.add(face_id)

    #     # Remove faces not seen recently
    #     self.active_faces = {
    #         face_id: data for face_id, data in self.active_faces.items()
    #         if data['last_seen'] > current_time - 0.5
    #     }

    #     y_offset = 60
    #     for face_id, data in self.active_faces.items():
    #         if current_time - data['last_seen'] < 0.5:
    #             x1, y1, x2, y # Initialize camera
    #     self.picam2 = Picamera2()
    #     camera_config = self.picam2.create_video_configuration(
    #         main={"size": (640, 480), "format": "RGB888"},
    #         controls={"FrameRate": 30}
    #     )
    #     self.picam2.configure(camera_config)
    #     self.picam2.start()

    #     # Initialize face detection and recognition models
    #     self.face_detector = dlib.get_frontal_face_detector()
    #     self.shape_predictor = dlib.shape_predictor(
    #         'shape_predictor_68_face_landmarks.dat')

    #     # Initialize tracking variables
    #     self.known_face_encodings = []
    #     self.known_face_ids = []
    #     self.current_id = 1
    #     self.active_faces = {}  # {face_id: {'encoding': encoding, 'last_seen': timestamp}}

    #     # Parameters
    #     self.recognition_threshold = 0.6
    #     self.process_every_n_frames = 3
    #     self.frame_count = 0
    #     self.max_faces = 10

    #     # FPS calculation
    #     self.fps_frames = []
    #     self.fps_window = 30
    #     self.target_fps = 30
    #     self.frame_time = 1.0 / self.target_fps

    #     # Performance optimization
    #     self.process_every_n_frames = 3
    #     self.frame_count = 0
    #     self.last_process_time = time.time()

    #     # Frame smoothing
    #     self.last_frame = None
    #     self.smoothing_factor = 0.5

    #     # Initialize servos
    #     self.kit = ServoKit(channels=16)
    #     self.kit.servo[0].set_pulse_width_range(400, 2500)
    #     self.kit.servo[2].set_pulse_width_range(400, 2600)
    #     self.servo0_angle = 90  # Up/Down servo angle
    #     self.servo2_angle = 90  # Left/Right servo angle
    #     self.servo_min_angle = 0
    #     self.servo_max_angle = 180
    #     self.kit.servo[0].angle = self.servo0_angle
    #     self.kit.servo[2].angle = self.servo2_angle

    #     # Deadzone parameters (adjust these to change the deadzone size)
    #     self.deadzone_x = 50
    #     self.deadzone_y = 50

    #     # Proportional control constant (adjust to change tracking speed)
    #     self.k_p = 0.05

    #     # Maximum change in angle per update (adjust to change tracking speed)
    #     self.servo_step = 1

    # def detect_faces(self, frame):
    #     """Use dlib to detect faces"""
    #     return self.face_detector(frame, 1)

    # def get_face_encoding(self, frame, face):
    #     """Get face encoding"""
    #     try:
    #         shape = self.shape_predictor(frame, face)
    #         face_locations = [
    #             (face.top(), face.right(), face.bottom(), face.left())]
    #         encoding = face_recognition.face_encodings(
    #             frame, face_locations)[0]
    #         return encoding
    #     except:
    #         return None

    # def find_best_match(self, encoding):
    #     """Find the best matching face ID"""
    #     if not self.known_face_encodings:
    #         return None

    #     distances = face_recognition.face_distance(
    #         self.known_face_encodings, encoding)
    #     min_distance = min(distances)

    #     if min_distance < self.recognition_threshold:
    #         return self.known_face_ids[np.argmin(distances)]
    #     return None

    # def calculate_fps(self, current_time):
    #     """Calculate smooth FPS using moving average"""
    #     if self.fps_frames:
    #         time_diff = current_time - self.fps_frames[-1]
    #         if time_diff > 0:
    #             current_fps = 1.0 / time_diff
    #             self.fps_frames.append(current_time)

    #             while len(self.fps_frames) > self.fps_window:
    #                 self.fps_frames.pop(0)

    #             if len(self.fps_frames) > 1:
    #                 avg_fps = (len(self.fps_frames) - 1) / \
    #                     (self.fps_frames[-1] - self.fps_frames[0])
    #                 return int(avg_fps)

    #     self.fps_frames.append(current_time)
    #     return 0

    # def process_frame(self):
    #     current_time = time.time()
    #     frame = self.picam2.capture_array()
    #     displayed_info = []

    #     if self.last_frame is not None:
    #         frame = cv2.addWeighted(frame, self.smoothing_factor,
    #                                 self.last_frame, 1 - self.smoothing_factor, 0)
    #     self.last_frame = frame.copy()

    #     time_since_last_process = current_time - self.last_process_time
    #     should_process = (self.frame_count % self.process_every_n_frames == 0 and
    #                       time_since_last_process >= self.frame_time)

    #     active_ids = set()

    #     if should_process:
    #         self.last_process_time = current_time

    #         faces = self.detect_faces(frame)

    #         for face in faces:
    #             x1, y1, x2, y2 = face.left(), face.top(), face.right(), face.bottom()

    #             encoding = self.get_face_encoding(frame, face)
    #             if encoding is None:
    #                 continue

    #             face_id = self.find_best_match(encoding)

    #             if face_id is None:
    #                 if len(self.known_face_encodings) < self.max_faces:
    #                     face_id = self.current_id
    #                     self.current_id += 1
    #                     self.known_face_encodings.append(encoding)
    #                     self.known_face_ids.append(face_id)
    #                     print(f"New face detected: ID {face_id}")

    #             if face_id is not None:
    #                 shape = self.shape_predictor(frame, face)
    #                 left_eye = np.mean([(shape.part(36).x, shape.part(36).y),
    #                                     (shape.part(37).x, shape.part(37).y),
    #                                     (shape.part(38).x, shape.part(38).y),
    #                                     (shape.part(39).x, shape.part(39).y),
    #                                     (shape.part(40).x, shape.part(40).y),
    #                                     (shape.part(41).x, shape.part(41).y)], axis=0)
    #                 right_eye = np.mean([(shape.part(42).x, shape.part(42).y),
    #                                      (shape.part(43).x, shape.part(43).y),
    #                                      (shape.part(44).x, shape.part(44).y),
    #                                      (shape.part(45).x, shape.part(45).y),
    #                                      (shape.part(46).x, shape.part(46).y),
    #                                      (shape.part(47).x, shape.part(47).y)], axis=0)

    #                 midpoint = ((left_eye[0] + right_eye[0]) // 2,
    #                             (left_eye[1] + right_eye[1]) // 2)

    #                 self.active_faces[face_id] = {
    #                     'encoding': encoding,
    #                     'last_seen': current_time,
    #                     'position': (x1, y1, x2, y2),
    #                     'midpoint': midpoint
    #                 }
    #                 active_ids.add(face_id)

    #     # Remove faces not seen recently
    #     self.active_faces = {
    #         face_id: data for face_id, data in self.active_faces.items()
    #         if data['last_seen'] > current_time - 0.5
    #     }

    #     y_offset = 60
    #     for face_id, data in self.active_faces.items():
    #         if current_time - data['last_seen'] < 0.5:
    #             x1, y1, x2, y2 = data['position']
    #             cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    #             cv2.putText(frame, f'ID: {face_id}', (x1, y1 - 10),
    #                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    #             midpoint = data['midpoint']
    #             cv2.circle(frame, (int(midpoint[0]), int(midpoint[1])),
    #                        2, (0, 255, 0), -1)

    #             displayed_info.append(
    #                 (face_id, int(midpoint[0]), int(midpoint[1])))

    #     displayed_info.sort(key=lambda x: x[0])
    #     for face_id, x, y in displayed_info:
    #         cv2.putText(frame, f'XY{face_id}: ({x},{y})',
    #                     (10, y_offset),
    #                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    #         y_offset += 20

    #     # Servo control to keep face ID 1 centered
    #     if 1 in self.active_faces:
    #         data = self.active_faces[1]
    #         midpoint = data['midpoint']
    #         frame_center_x = frame.shape[1] // 2
    #         frame_center_y = frame.shape[0] // 2
    #         error_x = frame_center_x - midpoint[0]
    #         error_y = frame_center_y - midpoint[1]

    #         # Initialize servo deltas
    #         delta_servo2 = 0
    #         delta_servo0 = 0

    #         # Check if error is outside the deadzone for X-axis
    #         if abs(error_x) > self.deadzone_x:
    #             # Calculate the desired angle change
    #             delta_servo2 = self.k_p * error_x
    #             # Limit the angle change per update
    #             delta_servo2 = max(-self.servo_step,
    #                                min(self.servo_step, delta_servo2))

    #         # Check if error is outside the deadzone for Y-axis
    #         if abs(error_y) > self.deadzone_y:
    #             delta_servo0 = self.k_p * error_y
    #             delta_servo0 = max(-self.servo_step,
    #                                min(self.servo_step, delta_servo0))

    #         # Update servo angles
    #         self.servo2_angle += delta_servo2
    #         self.servo0_angle -= delta_servo0  # Adjust sign if needed

    #         # Clamp servo angles to min and max
    #         self.servo2_angle = max(self.servo_min_angle, min(
    #             self.servo_max_angle, self.servo2_angle))
    #         self.servo0_angle = max(self.servo_min_angle, min(
    #             self.servo_max_angle, self.servo0_angle))

    #         # Set the servo angles
    #         self.kit.servo[2].angle = self.servo2_angle
    #         self.kit.servo[0].angle = self.servo0_angle

    #         # Display servo angles for debugging
    #         cv2.putText(frame, f'Servo0 Angle: {int(self.servo0_angle)}', (10, y_offset),
    #                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
    #         y_offset += 20
    #         cv2.putText(frame, f'Servo2 Angle: {int(self.servo2_angle)}', (10, y_offset),
    #                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
    #         y_offset += 20
    #     else:
    #         # Face ID 1 not detected, do not move servos
    #         pass

    #     self.frame_count += 1
    #     return frame

    # def run(self):
    #     prev_frame_time = time.time()
    #     fps = 0

    #     while True:
    #         current_time = time.time()

    #         elapsed = current_time - prev_frame_time
    #         if elapsed < self.frame_time:
    #             time.sleep(self.frame_time - elapsed)
    #             current_time = time.time()

    #         frame = self.process_frame()

    #         if elapsed > 0:
    #             new_fps = self.calculate_fps(current_time)
    #             fps = fps * 0.9 + new_fps * 0.1 if fps > 0 else new_fps

    #         cv2.putText(frame, f'FPS: {int(fps)}', (10, 30),
    #                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    #         cv2.imshow("Face Tracking", frame)
    #         prev_frame_time = current_time

    #         if cv2.waitKey(1) & 0xFF == ord('q'):
    #             break

    #     self.cleanup()

    # def cleanup(self):
    #     self.picam2.stop()
    #     cv2.destroyAllWindows()
# 2 = data['position']
    #             cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    #             cv2.putText(frame, f'ID: {face_id}', (x1, y1 - 10),
    #                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    #             midpoint = data['midpoint']
    #             cv2.circle(frame, (int(midpoint[0]), int(midpoint[1])),
    #                        2, (0, 255, 0), -1)

    #             displayed_info.append(
    #                 (face_id, int(midpoint[0]), int(midpoint[1])))

    #     displayed_info.sort(key=lambda x: x[0])
    #     for face_id, x, y in displayed_info:
    #         cv2.putText(frame, f'XY{face_id}: ({x},{y})',
    #                     (10, y_offset),
    #                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    #         y_offset += 20

    #     # Servo control to keep face ID 1 centered
    #     if 1 in self.active_faces:
    #         data = self.active_faces[1]
    #         midpoint = data['midpoint']
    #         frame_center_x = frame.shape[1] // 2
    #         frame_center_y = frame.shape[0] // 2
    #         error_x = frame_center_x - midpoint[0]
    #         error_y = frame_center_y - midpoint[1]

    #         # Initialize servo deltas
    #         delta_servo2 = 0
    #         delta_servo0 = 0

    #         # Check if error is outside the deadzone for X-axis
    #         if abs(error_x) > self.deadzone_x:
    #             # Calculate the desired angle change
    #             delta_servo2 = self.k_p * error_x
    #             # Limit the angle change per update
    #             delta_servo2 = max(-self.servo_step,
    #                                min(self.servo_step, delta_servo2))

    #         # Check if error is outside the deadzone for Y-axis
    #         if abs(error_y) > self.deadzone_y:
    #             delta_servo0 = self.k_p * error_y
    #             delta_servo0 = max(-self.servo_step,
    #                                min(self.servo_step, delta_servo0))

    #         # Update servo angles
    #         self.servo2_angle += delta_servo2
    #         self.servo0_angle -= delta_servo0  # Adjust sign if needed

    #         # Clamp servo angles to min and max
    #         self.servo2_angle = max(self.servo_min_angle, min(
    #             self.servo_max_angle, self.servo2_angle))
    #         self.servo0_angle = max(self.servo_min_angle, min(
    #             self.servo_max_angle, self.servo0_angle))

    #         # Set the servo angles
    #         self.kit.servo[2].angle = self.servo2_angle
    #         self.kit.servo[0].angle = self.servo0_angle

    #         # Display servo angles for debugging
    #         cv2.putText(frame, f'Servo0 Angle: {int(self.servo0_angle)}', (10, y_offset),
    #                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
    #         y_offset += 20
    #         cv2.putText(frame, f'Servo2 Angle: {int(self.servo2_angle)}', (10, y_offset),
    #                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
    #         y_offset += 20
    #     else:
    #         # Face ID 1 not detected, do not move servos
    #         pass

    #     self.frame_count += 1
    #     return frame

    # def run(self):
    #     prev_frame_time = time.time()
    #     fps = 0

    #     while True:
    #         current_time = time.time()

    #         elapsed = current_time - prev_frame_time
    #         if elapsed < self.frame_time:
    #             time.sleep(self.frame_time - elapsed)
    #             current_time = time.time()

    #         frame = self.process_frame()

    #         if elapsed > 0:
    #             new_fps = self.calculate_fps(current_time)
    #             fps = fps * 0.9 + new_fps * 0.1 if fps > 0 else new_fps

    #         cv2.putText(frame, f'FPS: {int(fps)}', (10, 30),
    #                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    #         cv2.imshow("Face Tracking", frame)
    #         prev_frame_time = current_time

    #         if cv2.waitKey(1) & 0xFF == ord('q'):
    #             break

    #     self.cleanup()

    # def cleanup(self):
    #     self.picam2.stop()
    #     cv2.destroyAllWindows()
 # Initialize camera
    #     self.picam2 = Picamera2()
    #     camera_config = self.picam2.create_video_configuration(
    #         main={"size": (640, 480), "format": "RGB888"},
    #         controls={"FrameRate": 30}
    #     )
    #     self.picam2.configure(camera_config)
    #     self.picam2.start()

    #     # Initialize face detection and recognition models
    #     self.face_detector = dlib.get_frontal_face_detector()
    #     self.shape_predictor = dlib.shape_predictor(
    #         'shape_predictor_68_face_landmarks.dat')

    #     # Initialize tracking variables
    #     self.known_face_encodings = []
    #     self.known_face_ids = []
    #     self.current_id = 1
    #     self.active_faces = {}  # {face_id: {'encoding': encoding, 'last_seen': timestamp}}

    #     # Parameters
    #     self.recognition_threshold = 0.6
    #     self.process_every_n_frames = 3
    #     self.frame_count = 0
    #     self.max_faces = 10

    #     # FPS calculation
    #     self.fps_frames = []
    #     self.fps_window = 30
    #     self.target_fps = 30
    #     self.frame_time = 1.0 / self.target_fps

    #     # Performance optimization
    #     self.process_every_n_frames = 3
    #     self.frame_count = 0
    #     self.last_process_time = time.time()

    #     # Frame smoothing
    #     self.last_frame = None
    #     self.smoothing_factor = 0.5

    #     # Initialize servos
    #     self.kit = ServoKit(channels=16)
    #     self.kit.servo[0].set_pulse_width_range(400, 2500)
    #     self.kit.servo[2].set_pulse_width_range(400, 2600)
    #     self.servo0_angle = 90  # Up/Down servo angle
    #     self.servo2_angle = 90  # Left/Right servo angle
    #     self.servo_min_angle = 0
    #     self.servo_max_angle = 180
    #     self.kit.servo[0].angle = self.servo0_angle
    #     self.kit.servo[2].angle = self.servo2_angle

    #     # Deadzone parameters (adjust these to change the deadzone size)
    #     self.deadzone_x = 50
    #     self.deadzone_y = 50

    #     # Proportional control constant (adjust to change tracking speed)
    #     self.k_p = 0.05

    #     # Maximum change in angle per update (adjust to change tracking speed)
    #     self.servo_step = 1

    # def detect_faces(self, frame):
    #     """Use dlib to detect faces"""
    #     return self.face_detector(frame, 1)

    # def get_face_encoding(self, frame, face):
    #     """Get face encoding"""
    #     try:
    #         shape = self.shape_predictor(frame, face)
    #         face_locations = [
    #             (face.top(), face.right(), face.bottom(), face.left())]
    #         encoding = face_recognition.face_encodings(
    #             frame, face_locations)[0]
    #         return encoding
    #     except:
    #         return None

    # def find_best_match(self, encoding):
    #     """Find the best matching face ID"""
    #     if not self.known_face_encodings:
    #         return None

    #     distances = face_recognition.face_distance(
    #         self.known_face_encodings, encoding)
    #     min_distance = min(distances)

    #     if min_distance < self.recognition_threshold:
    #         return self.known_face_ids[np.argmin(distances)]
    #     return None

    # def calculate_fps(self, current_time):
    #     """Calculate smooth FPS using moving average"""
    #     if self.fps_frames:
    #         time_diff = current_time - self.fps_frames[-1]
    #         if time_diff > 0:
    #             current_fps = 1.0 / time_diff
    #             self.fps_frames.append(current_time)

    #             while len(self.fps_frames) > self.fps_window:
    #                 self.fps_frames.pop(0)

    #             if len(self.fps_frames) > 1:
    #                 avg_fps = (len(self.fps_frames) - 1) / \
    #                     (self.fps_frames[-1] - self.fps_frames[0])
    #                 return int(avg_fps)

    #     self.fps_frames.append(current_time)
    #     return 0

    # def process_frame(self):
    #     current_time = time.time()
    #     frame = self.picam2.capture_array()
    #     displayed_info = []

    #     if self.last_frame is not None:
    #         frame = cv2.addWeighted(frame, self.smoothing_factor,
    #                                 self.last_frame, 1 - self.smoothing_factor, 0)
    #     self.last_frame = frame.copy()

    #     time_since_last_process = current_time - self.last_process_time
    #     should_process = (self.frame_count % self.process_every_n_frames == 0 and
    #                       time_since_last_process >= self.frame_time)

    #     active_ids = set()

    #     if should_process:
    #         self.last_process_time = current_time

    #         faces = self.detect_faces(frame)

    #         for face in faces:
    #             x1, y1, x2, y2 = face.left(), face.top(), face.right(), face.bottom()

    #             encoding = self.get_face_encoding(frame, face)
    #             if encoding is None:
    #                 continue

    #             face_id = self.find_best_match(encoding)

    #             if face_id is None:
    #                 if len(self.known_face_encodings) < self.max_faces:
    #                     face_id = self.current_id
    #                     self.current_id += 1
    #                     self.known_face_encodings.append(encoding)
    #                     self.known_face_ids.append(face_id)
    #                     print(f"New face detected: ID {face_id}")

    #             if face_id is not None:
    #                 shape = self.shape_predictor(frame, face)
    #                 left_eye = np.mean([(shape.part(36).x, shape.part(36).y),
    #                                     (shape.part(37).x, shape.part(37).y),
    #                                     (shape.part(38).x, shape.part(38).y),
    #                                     (shape.part(39).x, shape.part(39).y),
    #                                     (shape.part(40).x, shape.part(40).y),
    #                                     (shape.part(41).x, shape.part(41).y)], axis=0)
    #                 right_eye = np.mean([(shape.part(42).x, shape.part(42).y),
    #                                      (shape.part(43).x, shape.part(43).y),
    #                                      (shape.part(44).x, shape.part(44).y),
    #                                      (shape.part(45).x, shape.part(45).y),
    #                                      (shape.part(46).x, shape.part(46).y),
    #                                      (shape.part(47).x, shape.part(47).y)], axis=0)

    #                 midpoint = ((left_eye[0] + right_eye[0]) // 2,
    #                             (left_eye[1] + right_eye[1]) // 2)

    #                 self.active_faces[face_id] = {
    #                     'encoding': encoding,
    #                     'last_seen': current_time,
    #                     'position': (x1, y1, x2, y2),
    #                     'midpoint': midpoint
    #                 }
    #                 active_ids.add(face_id)

    #     # Remove faces not seen recently
    #     self.active_faces = {
    #         face_id: data for face_id, data in self.active_faces.items()
    #         if data['last_seen'] > current_time - 0.5
    #     }

    #     y_offset = 60
    #     for face_id, data in self.active_faces.items():
    #         if current_time - data['last_seen'] < 0.5:
    #             x1, y1, x2, y2 = data['position']
    #             cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    #             cv2.putText(frame, f'ID: {face_id}', (x1, y1 - 10),
    #                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    #             midpoint = data['midpoint']
    #             cv2.circle(frame, (int(midpoint[0]), int(midpoint[1])),
    #                        2, (0, 255, 0), -1)

    #             displayed_info.append(
    #                 (face_id, int(midpoint[0]), int(midpoint[1])))

    #     displayed_info.sort(key=lambda x: x[0])
    #     for face_id, x, y in displayed_info:
    #         cv2.putText(frame, f'XY{face_id}: ({x},{y})',
    #                     (10, y_offset),
    #                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    #         y_offset += 20

    #     # Servo control to keep face ID 1 centered
    #     if 1 in self.active_faces:
    #         data = self.active_faces[1]
    #         midpoint = data['midpoint']
    #         frame_center_x = frame.shape[1] // 2
    #         frame_center_y = frame.shape[0] // 2
    #         error_x = frame_center_x - midpoint[0]
    #         error_y = frame_center_y - midpoint[1]

    #         # Initialize servo deltas
    #         delta_servo2 = 0
    #         delta_servo0 = 0

    #         # Check if error is outside the deadzone for X-axis
    #         if abs(error_x) > self.deadzone_x:
    #             # Calculate the desired angle change
    #             delta_servo2 = self.k_p * error_x
    #             # Limit the angle change per update
    #             delta_servo2 = max(-self.servo_step,
    #                                min(self.servo_step, delta_servo2))

    #         # Check if error is outside the deadzone for Y-axis
    #         if abs(error_y) > self.deadzone_y:
    #             delta_servo0 = self.k_p * error_y
    #             delta_servo0 = max(-self.servo_step,
    #                                min(self.servo_step, delta_servo0))

    #         # Update servo angles
    #         self.servo2_angle += delta_servo2
    #         self.servo0_angle -= delta_servo0  # Adjust sign if needed

    #         # Clamp servo angles to min and max
    #         self.servo2_angle = max(self.servo_min_angle, min(
    #             self.servo_max_angle, self.servo2_angle))
    #         self.servo0_angle = max(self.servo_min_angle, min(
    #             self.servo_max_angle, self.servo0_angle))

    #         # Set the servo angles
    #         self.kit.servo[2].angle = self.servo2_angle
    #         self.kit.servo[0].angle = self.servo0_angle

    #         # Display servo angles for debugging
    #         cv2.putText(frame, f'Servo0 Angle: {int(self.servo0_angle)}', (10, y_offset),
    #                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
    #         y_offset += 20
    #         cv2.putText(frame, f'Servo2 Angle: {int(self.servo2_angle)}', (10, y_offset),
    #                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
    #         y_offset += 20
    #     else:
    #         # Face ID 1 not detected, do not move servos
    #         pass

    #     self.frame_count += 1
    #     return frame

    # def run(self):
    #     prev_frame_time = time.time()
    #     fps = 0

    #     while True:
    #         current_time = time.time()

    #         elapsed = current_time - prev_frame_time
    #         if elapsed < self.frame_time:
    #             time.sleep(self.frame_time - elapsed)
    #             current_time = time.time()

    #         frame = self.process_frame()

    #         if elapsed > 0:
    #             new_fps = self.calculate_fps(current_time)
    #             fps = fps * 0.9 + new_fps * 0.1 if fps > 0 else new_fps

    #         cv2.putText(frame, f'FPS: {int(fps)}', (10, 30),
    #                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    #         cv2.imshow("Face Tracking", frame)
    #         prev_frame_time = current_time

    #         if cv2.waitKey(1) & 0xFF == ord('q'):
    #             break

    #     self.cleanup()

    # def cleanup(self):
    #     self.picam2.stop()
    #     cv2.destroyAllWindows()
