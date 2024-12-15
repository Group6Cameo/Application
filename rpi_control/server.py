import uvicorn
from rpi_control.api.main import app


def main():
    # Get the Raspberry Pi's IP address
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    print(f"Starting server on {local_ip}:8000")

    uvicorn.run(
        "rpi_control.api.main:app",
        host="0.0.0.0",  # Binds to all network interfaces
        port=8000,
        reload=False     # Disable reload in production
    )


if __name__ == "__main__":
    main()
