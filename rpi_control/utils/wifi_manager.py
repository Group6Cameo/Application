import subprocess
import re
import platform


class WifiManager:
    def scan_networks(self):
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

            return networks
        except subprocess.CalledProcessError:
            return []

    def connect_to_network(self, ssid, password=None):
        # This is a basic implementation - you might want to use wpa_supplicant
        # or NetworkManager for more robust connectivity
        try:
            if password:
                cmd = f'nmcli device wifi connect "{ssid}" password "{password}"'
            else:
                cmd = f'nmcli device wifi connect "{ssid}"'
            subprocess.check_call(cmd, shell=True)
            return True
        except subprocess.CalledProcessError:
            return False
