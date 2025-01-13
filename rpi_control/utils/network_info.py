import os
from pathlib import Path
import socket
import netifaces

# File to store ngrok URL
NGROK_URL_FILE = "/tmp/ngrok_url.txt"


def set_ngrok_url(url: str):
    """Set the current ngrok URL"""
    try:
        with open(NGROK_URL_FILE, "w") as f:
            f.write(url)
    except Exception as e:
        print(f"Failed to save ngrok URL: {e}")


def get_public_url():
    """Get the ngrok URL if available, otherwise return local URL"""
    try:
        if os.path.exists(NGROK_URL_FILE):
            with open(NGROK_URL_FILE, "r") as f:
                url = f.read().strip()
                if url:
                    return url
    except Exception as e:
        print(f"Failed to read ngrok URL: {e}")

    # Fallback to local URL
    return f"http://{get_ip_address()}:8000"


def get_ip_address():
    """Get the Raspberry Pi's IP address on the local network"""
    # Try to get IP from wireless interface first
    interfaces = ['wlan0', 'eth0']  # Common interface names

    for iface in interfaces:
        try:
            if iface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    return addrs[netifaces.AF_INET][0]['addr']
        except:
            continue

    # Fallback method
    try:
        # Get hostname
        hostname = socket.gethostname()
        # Get IP
        return socket.gethostbyname(hostname)
    except:
        return "127.0.0.1"  # Localhost as last resort


def print_network_info():
    """Print network information for connecting to the API"""
    ip = get_ip_address()
    public_url = get_public_url()
    print("\n" + "="*50)
    print("Network Information:")
    print(f"Local API: http://{ip}:8000")
    print(f"Public URL: {public_url}")
    print(f"API documentation: http://{ip}:8000/docs")
    print("="*50 + "\n")
