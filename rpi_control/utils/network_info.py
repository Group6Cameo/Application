"""
Network information and ngrok URL management module for the RPI control system.

This module provides utilities for managing and retrieving network connectivity
information, with a focus on making the API accessible from any device.
It implements:
- ngrok URL management for public access
- Local network IP detection
- Fallback mechanisms for network detection

The system uses ngrok for creating secure tunnels to the local API, making it
accessible from any device regardless of network location. URLs are persisted
to a temporary file to maintain consistency across system components.

File Structure:
    - ngrok URLs are stored in /tmp/ngrok_url.txt
    - URLs are cached and refreshed as needed
    - File permissions follow system temporary directory standards

Dependencies:
    - netifaces for network interface detection
    - socket for hostname resolution
    - pathlib for file operations
"""

from pathlib import Path
import socket
import netifaces

# File to store ngrok URL
NGROK_URL_FILE = "/tmp/ngrok_url.txt"


def set_ngrok_url(url: str):
    """
    Persist the current ngrok URL to the temporary file system.

    Args:
        url (str): The complete ngrok URL including protocol and port

    The URL is stored in a temporary file for access by other system
    components. The function handles file operations safely and provides
    feedback on success or failure.

    Raises:
        Exception: If file writing fails, with the specific error captured
                  in the error message
    """
    try:
        with open(NGROK_URL_FILE, "w") as f:
            f.write(url)
            print(f"Saved ngrok URL to {NGROK_URL_FILE}")
    except Exception as e:
        print(f"Failed to save ngrok URL: {e}")


def get_public_url():
    """
    Retrieve the current public URL for API access.

    Returns:
        str: The complete URL for accessing the API, either:
             - ngrok URL if available
             - Local network URL as fallback

    The function implements a cascading fallback mechanism:
    1. Attempts to read the cached ngrok URL
    2. Falls back to local network URL if ngrok URL is unavailable
    3. Uses localhost as a last resort

    Note:
        The returned URL always includes the protocol and port number
    """
    try:
        if Path(NGROK_URL_FILE).exists():
            print("Using ngrok URL")
            with open(NGROK_URL_FILE, "r") as f:
                url = f.read().strip()
                if url:
                    print(f"Using ngrok URL: {url}")
                    return url
    except Exception as e:
        print(f"Failed to read ngrok URL: {e}")

    print("Using local URL")
    return f"http://{get_ip_address()}:8000"


def get_ip_address():
    """
    Determine the device's primary IP address on the local network.

    Returns:
        str: The device's IP address, with fallback options:
             1. Wireless interface (wlan0) IP if available
             2. Ethernet interface (eth0) IP if available
             3. Hostname-resolved IP as fallback
             4. Localhost (127.0.0.1) as last resort

    The function implements a prioritized interface checking system:
    1. Checks wireless interfaces first (modern RPi typically uses wireless)
    2. Falls back to ethernet if wireless is unavailable
    3. Uses hostname resolution as a backup
    4. Guarantees a valid IP address return value

    Note:
        Prioritizes wireless over ethernet to match typical RPi deployments
    """
    interfaces = ['wlan0', 'eth0']  # Common interface names

    for iface in interfaces:
        try:
            if iface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    return addrs[netifaces.AF_INET][0]['addr']
        except:
            continue

    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except:
        return "127.0.0.1"


def print_network_info():
    """
    Display comprehensive network connection information.

    Prints a formatted summary of all network access points including:
    - Local network API URL
    - Public access URL (ngrok)

    The output is formatted with clear visual separation using ASCII
    decorations for improved readability in terminal environments.

    Example output:
        ==================================================
        Network Information:
        Local API: http://192.168.1.100:8000
        Public URL: https://abcd1234.ngrok.io
        ==================================================
    """
    ip = get_ip_address()
    public_url = get_public_url()
    print("\n" + "="*50)
    print("Network Information:")
    print(f"Local API: http://{ip}:8000")
    print(f"Public URL: {public_url}")
    print("="*50 + "\n")
