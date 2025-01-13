from threading import Thread
import time
import board
import adafruit_apds9960.apds9960
import os

class BrightnessManager:
    def __init__(self):
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
                r, g, b, c = self.sensor.color_data  # Only need the clear value

                # Map clear value to brightness percentage (0-100)
                brightness_percent = min(max((c / 65535) * 100, 0), 100)

                # Set screen brightness
                self.set_screen_brightness(brightness_percent)

                # Print values
                print(f"Clear: {r, g, b, c}, Brightness: {brightness_percent:.1f}%")
                print("-" * 50)

                time.sleep(0.1)

            except Exception as e:
                print(f"Error reading sensor: {e}")
                time.sleep(5)  # Wait before retrying

    def set_screen_brightness(self, brightness_percent):
        # Convert percentage to integer (0-100)
        brightness_value = int(brightness_percent)

        # Set the brightness using brightnessctl
        try:
            print(f"Setting screen brightness to {brightness_value}%")
            os.system(f"brightnessctl set {brightness_value}%")
        except Exception as e:
            print(f"Error setting screen brightness: {e}")

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
