from threading import Thread
import time
import board
import adafruit_apds9960.apds9960
from PyQt6.QtCore import QObject, pyqtSignal


class BrightnessManager(QObject):
    brightness_changed = pyqtSignal(int)

    def __init__(self, brightness_overlay=None):
        super().__init__()
        self.brightness_overlay = brightness_overlay

        # Initialize I2C and APDS9960 sensor
        i2c = board.I2C()
        self.sensor = adafruit_apds9960.apds9960.APDS9960(i2c)

        # Enable proximity and color sensing
        self.sensor.enable_proximity = True
        self.sensor.enable_color = True

        # Thread control
        self.is_running = False
        self.thread = None

    def _monitor_loop(self):
        while self.is_running:
            try:
                # Read sensor values
                r, g, b, c = self.sensor.color_data

                # Add base brightness (30%) and adjust scaling
                BASE_BRIGHTNESS = 20

                # Map clear value to additional brightness (0-60%)
                additional_brightness = min(
                    max((c / 6000) * 100, 0), 60)

                # Combine base and additional brightness
                total_brightness = BASE_BRIGHTNESS + additional_brightness

                # Clamp final value between 0-100
                brightness_percent = min(max(total_brightness, 0), 100)

                # Emit the brightness change signal
                self.brightness_changed.emit(int(brightness_percent))

                # Debug print
                print(
                    f"Light value: {c}, Additional: {additional_brightness:.1f}%, Total: {brightness_percent:.1f}%")

                time.sleep(0.1)

            except Exception as e:
                print(f"Error reading sensor: {e}")
                time.sleep(5)

    def start(self):
        """Start the monitoring thread"""
        if not self.is_running:
            self.is_running = True
            self.thread = Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            print("Brightness monitoring started")

    def stop(self):
        """Stop the monitoring thread"""
        self.is_running = False
        if self.thread:
            self.thread.join()
            self.thread = None
            print("Brightness monitoring stopped")
