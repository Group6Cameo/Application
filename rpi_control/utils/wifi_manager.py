"""
WiFi network management utility for the RPI control system.

This module provides a platform-independent interface for WiFi operations,
supporting both macOS (development) and Linux/Raspberry Pi systems. It handles:
- Network scanning and discovery
- Connection management
- Current connection status monitoring
- Enterprise and WPA/WEP authentication

The module uses system-specific commands (nmcli on Linux, airport on macOS)
to interact with wireless interfaces, providing a consistent API across platforms.

Dependencies:
    - subprocess for system command execution
    - platform for OS detection
    - re for parsing command output
"""

import subprocess
import re
import platform


class WifiManager:
    """
    A platform-independent WiFi network management interface.

    Provides methods for scanning, connecting to, and monitoring WiFi networks
    across different operating systems. Handles different authentication methods
    and network security types automatically.
    """

    def scan_networks(self):
        """
        Scan for available WiFi networks in range.

        Returns:
            list: A deduplicated list of available network SSIDs

        The method adapts its behavior based on the operating system:
        - On macOS: Uses airport utility
        - On Linux: Uses iwlist scanning

        Note:
            Returns an empty list if scanning fails or requires elevated privileges
        """
        try:
            if platform.system() == 'Darwin':  # macOS
                cmd = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s | awk '{print $1}'"
            else:  # Linux/Raspberry Pi
                cmd = "sudo iwlist wlan0 scan | grep ESSID"

            output = subprocess.check_output(cmd, shell=True).decode()

            if platform.system() == 'Darwin':
                # Skip the header line and remove empty lines
                networks = [line for line in output.split(
                    '\n') if line.strip()]
                if networks:  # Remove the "SSID" header
                    networks = networks[1:]
            else:
                networks = re.findall(r'ESSID:"([^"]*)"', output)

            # Remove duplicates while preserving order
            return list(dict.fromkeys(networks))
        except subprocess.CalledProcessError:
            return []

    def connect_to_network(self, ssid, username=None, password=None):
        """
        Attempt to connect to a specified WiFi network.

        Args:
            ssid (str): The SSID of the network to connect to
            username (str, optional): Username for enterprise networks
            password (str, optional): Network password for secured networks

        Returns:
            bool: True if connection successful, False otherwise

        Features:
            - Checks if already connected to requested network
            - Auto-detects network security type (WPA, WEP, Enterprise)
            - Prompts for credentials if needed and not provided
            - Verifies successful connection
        """
        try:
            # First check if we're already connected to this network
            current_connection = subprocess.check_output(
                "nmcli -t -f ACTIVE,SSID dev wifi | grep '^yes'",
                shell=True, stderr=subprocess.DEVNULL
            ).decode().strip()

            if ssid in current_connection:
                return True

            # Get security info for the network
            try:
                security_info = subprocess.check_output(
                    f'nmcli -f SECURITY device wifi list | grep "{ssid}"',
                    shell=True
                ).decode().strip()

                # Check if network requires credentials
                is_enterprise = 'WPA2-Enterprise' in security_info or 'WPA-Enterprise' in security_info
                needs_password = 'WPA' in security_info or 'WEP' in security_info

                if is_enterprise and not username:
                    print(f"\nNetwork '{ssid}' requires authentication.")
                    username = input("Please enter username: ")
                    if not password:
                        password = input("Please enter password: ")

                elif needs_password and not password:
                    print(f"\nNetwork '{ssid}' requires a password.")
                    password = input("Please enter password: ")

            except subprocess.CalledProcessError:
                pass  # Network might be open or not found

            # Attempt to connect
            if username and password:
                cmd = f'nmcli device wifi connect "{ssid}" password "{password}" username "{username}"'
            elif password:
                cmd = f'nmcli device wifi connect "{ssid}" password "{password}"'
            else:
                cmd = f'nmcli device wifi connect "{ssid}"'

            subprocess.check_call(cmd, shell=True, stderr=subprocess.PIPE)

            # Verify connection was successful
            verification = subprocess.check_output(
                "nmcli -t -f ACTIVE,SSID dev wifi | grep '^yes'",
                shell=True
            ).decode().strip()

            return ssid in verification

        except subprocess.CalledProcessError as e:
            print(f"Failed to connect to {ssid}. Error: {e}")
            return False

    def get_current_network(self):
        """
        Get the SSID of the currently connected network.

        Returns:
            str: The SSID of the connected network
            None: If not connected or unable to determine connection status

        Uses nmcli to query active connections and extracts the current
        network SSID. Handles errors silently and returns None on failure.

        An SSID is a unique identifier for a WiFi network, typically a string of characters
        that represents the name of the network.
        """
        try:
            output = subprocess.check_output(
                "nmcli -t -f ACTIVE,SSID dev wifi | grep '^yes'",
                shell=True,
                stderr=subprocess.DEVNULL
            ).decode().strip()

            if output:
                # Extract SSID from the output (format is "yes:SSID")
                return output.split(':')[1]
            return None

        except subprocess.CalledProcessError:
            return None
