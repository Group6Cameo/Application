import socket
import netifaces


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
    print("\n" + "="*50)
    print("Network Information:")
    print(f"API is available at: http://{ip}:8000")
    print(f"API documentation: http://{ip}:8000/docs")
    print("="*50 + "\n")
