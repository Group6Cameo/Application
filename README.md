# Cameo Framework

A comprehensive framework for controlling Raspberry Pi-based camouflage displays with face tracking capabilities.

## Features

- Face detection and tracking using Hailo AI
- Servo motor control for dynamic tracking
- WiFi configuration interface
- QR code-based calibration system
- Camouflage pattern generation and display
- REST API for remote control
- Web interface for pattern uploads

## Prerequisites

- Raspberry Pi 5
- Raspberry Pi OS (64-bit)
- Python 3.11+
- Hailo 8L (for RPi) AI accelerator
- Servo motors (for tracking)
- Display screen
- Camera module
- NVMe base

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Group6Cameo/Application.git
```
```bash
cd Application
```

2. Run the setup script:
```bash
bash setup.sh
```

The setup script will:
- Install system dependencies
- Create Python virtual environment
- Install Python packages
- Configure Hailo TAPPAS
- Set up autostart services

## Project Structure

```
cameo-framework/
├── rpi_control/           # Main application package
│   ├── api/              # REST API implementation
│   ├── utils/            # Utility functions
│   ├── widgets/          # GUI components
│   └── assets/           # Static assets
├── scripts/              # Helper scripts
└── requirements.txt      # Python dependencies
```

## Running the Application

1. Start the main application:
```bash
bash start.sh
```

2. The application will:
- Launch the GUI interface
- Start the REST API server
- Initialize face tracking
- Begin camouflage pattern display

## Configuration

### Face Recognition

The system uses Hailo AI for face detection and recognition. Configuration files are located in: `python:rpi_control/utils/resources/configs/scrfd.json`


### Network Configuration

The system provides a GUI interface for WiFi configuration. Network settings are managed through python: `rpi_control/widgets/network.py`


## API Documentation

The REST API is available at `http://<device-ip>:8000/api` and provides endpoints for:
- Pattern upload
- Face tracking control
- System status
- Calibration management

## Development

When developing, make sure you have the cameo venv activated.


## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT

## Support

For issues and support, please create an issue in the GitHub repository.


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
