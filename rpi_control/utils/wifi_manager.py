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

            # Remove duplicates while preserving order
            return list(dict.fromkeys(networks))
        except subprocess.CalledProcessError:
            return []

    def connect_to_network(self, ssid, username=None, password=None):
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
