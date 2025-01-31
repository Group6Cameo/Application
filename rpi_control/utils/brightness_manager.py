"""
Ambient light-based brightness control module for the RPI control system (currently inactive).

This module provides automatic brightness adjustment based on ambient light levels
detected through an APDS9960 light sensor.

Note:
    This module is currently not in active use but remains as a potential solution
    for systems where hardware brightness control is unavailable through the
    Raspberry Pi OS. It works in conjunction with BrightnessOverlay to provide
    ambient-light-responsive display adjustment.

Technical approach:
- Uses APDS9960 sensor for ambient light detection
- Runs continuous light monitoring in a separate thread
- Maps sensor values to brightness levels (0-100%)
- Provides base brightness (20%) plus dynamic adjustment (0-60%)
- Emits signals for brightness changes that can be consumed by overlay system

Dependencies:
    - board: For I2C communication
    - adafruit_apds9960: For light sensor interaction
    - PyQt6: For signal emission
    - threading: For background monitoring
"""

from threading import Thread
import time
import board
import adafruit_apds9960.apds9960
from PyQt6.QtCore import QObject, pyqtSignal


class BrightnessManager(QObject):
    """
    Manager for ambient light-based brightness control.

    Monitors ambient light levels using an APDS9960 sensor and adjusts screen
    brightness accordingly. Uses a separate thread for continuous monitoring
    to prevent blocking the main application thread.

    Signals:
        brightness_changed (int): Emitted when brightness level changes (0-100)
    """

    brightness_changed = pyqtSignal(int)

    def __init__(self, brightness_overlay=None):
        """
        Initialize the brightness manager.

        Args:
            brightness_overlay (BrightnessOverlay, optional): Overlay widget for
                brightness control. Defaults to None.

        Sets up I2C communication, initializes the APDS9960 sensor, and configures
        initial monitoring state.
        """
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
        """
        Main monitoring loop for ambient light detection.

        Continuously reads sensor values and calculates appropriate brightness
        levels. The calculation combines:
        - Base brightness (20%)
        - Dynamic component based on ambient light (0-60%)
        - Protection against extreme changes
        - Error handling with retry mechanism

        The loop runs in a separate thread and emits brightness_changed signals
        when adjustments are needed.
        """
        while self.is_running:
            try:
                # Read sensor values
                r, g, b, c = self.sensor.color_data

                # Add base brightness (30%) and adjust scaling
                BASE_BRIGHTNESS = 20

                # Map clear value to additional brightness (0-60%)
                additional_brightness = min(
                    max((c / 10000) * 100, 0), 80)

                # Combine base and additional brightness
                total_brightness = BASE_BRIGHTNESS + additional_brightness

                # Clamp final value between 0-100
                brightness_percent = min(max(total_brightness, 0), 100)

                # Emit the brightness change signal
                self.brightness_changed.emit(int(brightness_percent))

                # Debug print
                print(
                    f"Light value: {c}, colors: {r, g, b}, Additional: {additional_brightness:.1f}%, Total: {brightness_percent:.1f}%")

                time.sleep(0.1)

            except Exception as e:
                print(f"Error reading sensor: {e}")
                time.sleep(5)

    def start(self):
        """
        Start the ambient light monitoring thread.

        Initializes and starts a daemon thread for continuous light level
        monitoring. The thread will automatically terminate when the main
        program exits.

        Note:
            Only one monitoring thread can be active at a time.
        """
        if not self.is_running:
            self.is_running = True
            self.thread = Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            print("Brightness monitoring started")

    def stop(self):
        """
        Stop the ambient light monitoring thread.

        Gracefully stops the monitoring thread and ensures proper cleanup
        of resources. Waits for the current monitoring cycle to complete
        before terminating.
        """
        self.is_running = False
        if self.thread:
            self.thread.join()
            self.thread = None
            print("Brightness monitoring stopped")

    def cleanup(self):
        """
        Perform cleanup operations.

        Should be called before program termination to ensure proper
        resource cleanup and thread termination. Stops the monitoring
        thread if it's still running.
        """
        self.stop()
