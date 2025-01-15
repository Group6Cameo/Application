import time
import csv
import subprocess
import threading
import os
from adafruit_servokit import ServoKit
from datetime import datetime

# =============================
# ========== SETTINGS ==========
# =============================
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(WORKING_DIR, 'tmp', 'face_info_log.csv')
IMAGE_WIDTH = 640
IMAGE_HEIGHT = 360

INITIAL_SERVO0_ANGLE = 120
INITIAL_SERVO1_ANGLE = 95
INITIAL_ARM_ANGLE = 90

DEADZONE_X = 60
DEADZONE_Y = 40

K_P = 0.5
SERVO_STEP = 1.5

CENTRE_X = IMAGE_WIDTH // 2
CENTRE_Y = IMAGE_HEIGHT // 2

DETECTION_WINDOW = 1.0  # 1 second window for conflict detection
CONFLICT_THRESHOLD = 3  # Number of conflicts needed to trigger resolution

# Detection conflict global
detection_conflicts = {}  # {gallery_id: [(timestamp, detection_id, x, y), ...]}
current_override = None   # Store current override detection_id if any

# =============================
# ========== SETUP =============
# =============================
kit = ServoKit(channels=16)

kit.servo[0].set_pulse_width_range(400, 2600)
kit.servo[1].set_pulse_width_range(400, 2600)
kit.servo[2].set_pulse_width_range(400, 2600)
kit.servo[3].set_pulse_width_range(400, 2600)

# =============================
# ========== FUNCTIONS =========
# =============================
def set_arm_position(kit_instance, angle):
    """Linked control for servo2 & servo3, so that when servo3 moves forward,
    servo2 moves backward. The 'angle' must be between 0 and 180."""
    if angle < 0 or angle > 180:
        raise ValueError("Angle must be between 0 and 180 degrees.")
    kit_instance.servo[3].angle = angle
    kit_instance.servo[2].angle = 180 - angle

deadzones = {
    'servo0': (999, -1),
    'servo1': (999, -1),
    'arm':   (999, -1)
}

def in_deadzone(angle, deadzone):
    dz_min, dz_max = deadzone
    if dz_min <= dz_max:
        return dz_min <= angle <= dz_max
    return False

def set_servo_angle_with_deadzone(servo_index, angle, deadzone_key):
    angle = max(0, min(180, angle))
    if not in_deadzone(angle, deadzones[deadzone_key]):
        kit.servo[servo_index].angle = angle

def set_arm_angle_with_deadzone(angle):
    angle = max(0, min(180, angle))
    if not in_deadzone(angle, deadzones['arm']):
        set_arm_position(kit, angle)

# Servo default angles
servo0_angle = INITIAL_SERVO0_ANGLE
servo1_angle = INITIAL_SERVO1_ANGLE
arm_angle = INITIAL_ARM_ANGLE

kit.servo[0].angle = servo0_angle
kit.servo[1].angle = servo1_angle
set_arm_position(kit, arm_angle)

def adjust_servo_angles_using_old_logic(target_x, target_y):
    """
    Original servo movement logic with a vertical servo (servo0),
    horizontal servo (servo1), and an arm that moves if servo0 is at a limit.
    """
    global servo0_angle, servo1_angle, arm_angle

    error_x = CENTRE_X - target_x
    error_y = CENTRE_Y - target_y

    # Horizontal servo1
    if abs(error_x) > DEADZONE_X:
        delta_servo1 = K_P * error_x
        delta_servo1 = max(-SERVO_STEP, min(SERVO_STEP, delta_servo1))
    else:
        delta_servo1 = 0

    # Vertical servo0
    if abs(error_y) > DEADZONE_Y:
        delta_servo0 = K_P * error_y
        delta_servo0 = max(-SERVO_STEP, min(SERVO_STEP, delta_servo0))
    else:
        delta_servo0 = 0

    new_servo1_angle = servo1_angle + delta_servo1
    new_servo0_angle = servo0_angle - delta_servo0

    # Clamp angles
    new_servo1_angle = max(0, min(180, new_servo1_angle))
    new_servo0_angle = max(0, min(180, new_servo0_angle))

    # Check if servo0 can move
    servo0_moved = True
    if (delta_servo0 < 0 and new_servo0_angle <= 0):
        servo0_moved = False
    elif (delta_servo0 > 0 and new_servo0_angle >= 180):
        servo0_moved = False

    new_arm_angle = arm_angle
    if not servo0_moved:
        # servo0 is at a limit, move the arm
        if delta_servo0 < 0 and new_servo0_angle <= 0:
            arm_delta = -SERVO_STEP
            new_arm_angle = max(0, arm_angle + arm_delta)
        elif delta_servo0 > 0 and new_servo0_angle >= 180:
            arm_delta = SERVO_STEP
            new_arm_angle = min(180, arm_angle + arm_delta)
    else:
        servo0_angle = new_servo0_angle

    # Set servo1
    set_servo_angle_with_deadzone(1, new_servo1_angle, 'servo1')
    servo1_angle = new_servo1_angle

    # If servo0 moved, update it. Otherwise move arm.
    if servo0_moved:
        set_servo_angle_with_deadzone(0, servo0_angle, 'servo0')
    else:
        set_arm_angle_with_deadzone(new_arm_angle)
        arm_angle = new_arm_angle

# =============================
# === CSV-BASED DETECTION ====
# =============================
def start_monitor_detection():
    """
    Launches the face-detection script in the background.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    monitor_script = os.path.join(current_dir, 'monitor_detections.py')
    subprocess.Popen(['python3', monitor_script])
    print(f"Started monitor_detection.py from: {monitor_script}")

def get_latest_csv_row(csv_path):
    """
    Reads the CSV, returns the row with the largest Rec_BufferSet
    (the second column). If no data, returns None.
    """
    try:
        with open(csv_path, 'r') as f:
            rows = list(csv.reader(f))
        if len(rows) <= 1:
            return None  # only header or empty file

        header = rows[0]
        data_lines = rows[1:]
        
        # The second column is 'Rec_BufferSet' => index=1
        # We'll parse it as an integer and find the maximum
        valid_lines = []
        for row in data_lines:
            # row format:
            # [Timestamp, Rec_BufferSet, Detection_ID, Gallery_ID, Label, Center_X, Center_Y]
            try:
                offset_int = int(row[1])  # convert Rec_BufferSet to int
                valid_lines.append((offset_int, row))
            except:
                # skip invalid rows
                pass

        if not valid_lines:
            return None
        
        # Sort by offset ascending, last item has the largest offset
        valid_lines.sort(key=lambda x: x[0])
        max_offset, max_row = valid_lines[-1]
        return max_row
    except FileNotFoundError:
        return None
    except:
        return None

def check_detection_conflicts(gallery_id, detection_id, center_x, center_y):
    """
    Check if there are conflicts in detection IDs for the same gallery ID
    Returns the detection_id to track
    """
    global detection_conflicts, current_override
    current_time = time.time()
    
    # Initialize or clean old entries
    if gallery_id not in detection_conflicts:
        detection_conflicts[gallery_id] = []
    
    # Remove old entries (older than DETECTION_WINDOW)
    detection_conflicts[gallery_id] = [
        entry for entry in detection_conflicts[gallery_id]
        if current_time - entry[0] < DETECTION_WINDOW
    ]
    
    # Add new detection
    detection_conflicts[gallery_id].append((current_time, detection_id, center_x, center_y))
    
    # Check for conflicts in the current window
    recent_detections = detection_conflicts[gallery_id]
    unique_detection_ids = set(entry[1] for entry in recent_detections)
    
    # If we have conflicts and enough samples
    if len(unique_detection_ids) > 1 and len(recent_detections) >= CONFLICT_THRESHOLD:
        # Group detections by detection_id
        detection_groups = {}
        for entry in recent_detections:
            _, det_id, x, y = entry
            if det_id not in detection_groups:
                detection_groups[det_id] = []
            detection_groups[det_id].append((x, y))
        
        # Find the detection_id closest to center
        closest_id = None
        min_distance = float('inf')
        
        for det_id, positions in detection_groups.items():
            # Calculate average position for this detection_id
            avg_x = sum(x for x, _ in positions) / len(positions)
            avg_y = sum(y for y, _ in positions) / len(positions)
            
            # Calculate distance to center
            distance = ((avg_x - CENTRE_X) ** 2 + (avg_y - CENTRE_Y) ** 2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                closest_id = det_id
        
        current_override = closest_id
        print(f"Conflict detected for Gallery ID {gallery_id}. Using closest Detection ID: {closest_id}")
        return closest_id
    
    # If no conflicts in window, clear override
    if len(unique_detection_ids) == 1 and current_override:
        print(f"Conflict resolved for Gallery ID {gallery_id}. Returning to normal tracking.")
        current_override = None
    
    return detection_id

def cleanup_servos():
    """
    Smoothly move servos back to 90 degrees.
    """
    global servo0_angle, servo1_angle, arm_angle
    target0, target1, targetA = 90, 90, 90
    steps = 10
    delay = 0.01

    for i in range(steps):
        servo0_angle += (target0 - servo0_angle) / (steps - i)
        servo1_angle += (target1 - servo1_angle) / (steps - i)
        arm_angle += (targetA - arm_angle) / (steps - i)
        
        set_servo_angle_with_deadzone(0, servo0_angle, 'servo0')
        set_servo_angle_with_deadzone(1, servo1_angle, 'servo1')
        set_arm_angle_with_deadzone(arm_angle)
        time.sleep(delay)

def get_target_face_id():
    """
    Reads the manually set target face ID from file.
    """
    try:
        target_file = os.path.join(WORKING_DIR, 'tmp', 'target_face.txt')
        with open(target_file, 'r') as f:
            target_id = f.read().strip()
            return target_id
    except Exception as e:
        print(f"Error reading target face ID: {e}")  # Debug output
        return '1'  # Default face ID

# =============================
# == AUTO-REGRESSION LOGIC ====
# =============================

# Global variables for target logic
TARGET_GALLERY_ID = get_target_face_id()  # Current active target
LAST_MANUAL_TARGET_ID = TARGET_GALLERY_ID # Store the last manually set ID
manual_update_detected = False            # Flag to indicate a new manual update

# Timers for auto logic
lost_target_start_time = None
lost_1_start_time = None

# Dictionary for tracking last seen time of each gallery ID
last_seen_gallery_time = {}

def update_last_seen(g_id):
    """Update the last seen timestamp for a given gallery ID."""
    global last_seen_gallery_time
    last_seen_gallery_time[g_id] = time.time()

def get_active_ids(window=1.0):
    """
    Return a list of gallery IDs that have been seen within 'window' seconds.
    """
    now = time.time()
    return [
        gid for gid, t in last_seen_gallery_time.items()
        if (now - t) < window
    ]

def check_and_update_manual_target():
    """
    Check if there's a new manual target in the target_face.txt file.
    If found, update global variables and reset timers.
    """
    global TARGET_GALLERY_ID, LAST_MANUAL_TARGET_ID
    global manual_update_detected, lost_target_start_time, lost_1_start_time

    new_target_id = get_target_face_id()
    if new_target_id != TARGET_GALLERY_ID:
        # We consider this a manual update from the file
        TARGET_GALLERY_ID = new_target_id
        LAST_MANUAL_TARGET_ID = new_target_id
        manual_update_detected = True
        # Reset timers
        lost_target_start_time = None
        lost_1_start_time = None
        print(f"Manual update detected: {new_target_id}")
    else:
        # If no change, we set manual_update_detected to False
        # so auto logic can proceed
        manual_update_detected = False

def auto_regression_logic():
    """
    Auto regression logic to revert target ID if needed.
    Runs only when no manual update is detected.
    """
    global TARGET_GALLERY_ID, LAST_MANUAL_TARGET_ID
    global lost_target_start_time, lost_1_start_time

    active_list = get_active_ids(window=1.0)

    # If the current target is missing from active_list for >=1s, revert to '1'
    if TARGET_GALLERY_ID not in active_list:
        if lost_target_start_time is None:
            lost_target_start_time = time.time()
        else:
            if time.time() - lost_target_start_time >= 1.0:
                # Switch to 1
                TARGET_GALLERY_ID = '1'
                lost_target_start_time = None
                print("Auto regression: target lost for >=1s, switching to '1'")
    else:
        lost_target_start_time = None

    # If the current target is '1' but '1' not in active_list for >=1s,
    # choose the smallest ID from the active list (if any).
    if TARGET_GALLERY_ID == '1' and '1' not in active_list:
        if lost_1_start_time is None:
            lost_1_start_time = time.time()
        else:
            if time.time() - lost_1_start_time >= 1.0:
                if len(active_list) > 0:
                    new_target = min(int(x) for x in active_list)
                    TARGET_GALLERY_ID = str(new_target)
                    print(f"Auto regression: '1' missing for >=1s, switching to smallest ID: {TARGET_GALLERY_ID}")
                lost_1_start_time = None
    else:
        lost_1_start_time = None

    # ========== IMPORTANT CHANGE HERE ==========
    # Only if the *last manual target* was '1', do we auto-switch back to '1'
    # when '1' reappears. If user last manually chose something else (e.g. 2),
    # we don't forcibly revert to '1'.
    # ===========================================
    if (
        TARGET_GALLERY_ID != '1' 
        and '1' in active_list 
        and LAST_MANUAL_TARGET_ID == '1'
    ):
        TARGET_GALLERY_ID = '1'
        print("Auto regression: '1' reappeared in list, switching back to '1'")

    if (
        LAST_MANUAL_TARGET_ID != '1'
        and LAST_MANUAL_TARGET_ID in active_list
        and TARGET_GALLERY_ID != LAST_MANUAL_TARGET_ID
    ):
        TARGET_GALLERY_ID = LAST_MANUAL_TARGET_ID
        print(f"Auto regression: last manual target {LAST_MANUAL_TARGET_ID} reappeared, switching back.")

def track_face():
    """
    Modified track_face function with conflict detection
    and auto regression logic.
    """
    global TARGET_GALLERY_ID
    last_offset = -1
    x_last = None
    y_last = None
    last_check_time = 0
    ID_CHECK_INTERVAL = 0.1  # Check target ID every 0.1 seconds

    while True:
        try:
            current_time = time.time()
            
            # Periodically check if there's a new manual target update
            if current_time - last_check_time >= ID_CHECK_INTERVAL:
                check_and_update_manual_target()

                # If there's no manual update, run auto regression logic
                if not manual_update_detected:
                    auto_regression_logic()

                last_check_time = current_time

            latest_row = get_latest_csv_row(CSV_PATH)
            if latest_row is not None:
                timestamp_str = latest_row[0]
                offset_str = latest_row[1]
                detection_id = latest_row[2]
                gallery_id = latest_row[3]
                label = latest_row[4]
                center_x_str = latest_row[5]
                center_y_str = latest_row[6]

                # Update last seen time for this gallery_id
                if gallery_id not in [None, '', 'null']:
                    update_last_seen(gallery_id)

                # If row matches the currently targeted gallery
                if (gallery_id == TARGET_GALLERY_ID and 
                    detection_id not in [None, '', 'null'] and
                    center_x_str not in [None, '', 'null'] and
                    center_y_str not in [None, '', 'null']):

                    try:
                        offset_int = int(offset_str)
                        center_x = float(center_x_str)
                        center_y = float(center_y_str)

                        # Check conflicts
                        tracked_detection_id = check_detection_conflicts(
                            gallery_id, detection_id, center_x, center_y
                        )

                        # Only process if this is the detection ID we want to track
                        if tracked_detection_id == detection_id:
                            if offset_int > last_offset:
                                last_offset = offset_int
                                x_last = center_x
                                y_last = center_y
                                adjust_servo_angles_using_old_logic(x_last, y_last)
                    except:
                        pass
            
            time.sleep(0.01)

        except KeyboardInterrupt:
            print("\nTracking stopped by user.")
            break
        except Exception as e:
            print(f"Error reading CSV: {e}")
            time.sleep(0.1)

def main():
    try:
        # Only create target face file if it doesn't exist
        target_file = os.path.join(WORKING_DIR, 'tmp', 'target_face.txt')
        if not os.path.exists(target_file):
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            with open(target_file, 'w') as f:
                f.write('1')
            print("Created target face file with default ID: 1")
        
        # Update the global TARGET_GALLERY_ID from existing file
        global TARGET_GALLERY_ID
        TARGET_GALLERY_ID = get_target_face_id()
        print(f"Starting tracking with initial target ID: {TARGET_GALLERY_ID}")
        
        start_monitor_detection()
        # Give it time to spin up
        time.sleep(2)
        track_face()
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        print("Cleaning up servo positions...")
        cleanup_servos()

if __name__ == "__main__":
    main()
