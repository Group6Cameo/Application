#!/usr/bin/env bash
# Currently in development, not yet tested

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get directory paths
APP_DIR="$(pwd)"
REPO_DIR="$(dirname "$APP_DIR")"
HOME_DIR="$(echo $HOME)"

# Print paths for verification
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_info "Paths detected:"
log_info "APP_DIR: $APP_DIR"
log_info "REPO_DIR: $REPO_DIR"
log_info "HOME_DIR: $HOME_DIR"

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Error handling
check_error() {
    if [ $? -ne 0 ]; then
        log_error "$1 failed"
        exit 1
    fi
}

# Check if script is run with sudo
check_sudo() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Please run with sudo"
        exit 1
    fi
}

# Check system requirements
check_system_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python version
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python3 is required but not installed"
        exit 1
    fi
    
    # Check available disk space (minimum 10GB)
    available_space=$(df -BG . | tail -n 1 | awk '{print $4}' | sed 's/G//')
    if [ "$available_space" -lt 10 ]; then
        log_warn "Less than 10GB disk space available: ${available_space}GB"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check internet connection
    if ! ping -c 1 google.com >/dev/null 2>&1; then
        log_error "No internet connection"
        exit 1
    fi
}

# Backup function
create_backup() {
    local backup_dir="../backup_$(date +%Y%m%d_%H%M%S)"
    log_info "Creating backup in $backup_dir"
    mkdir -p "$backup_dir"
    
    # Backup existing configurations if they exist
    if [ -d "../cameo" ]; then
        cp -r ../cameo "$backup_dir/" 2>/dev/null || true
    fi
}

# Progress tracking
TOTAL_STEPS=9
current_step=0

progress() {
    current_step=$((current_step + 1))
    log_info "Step $current_step/$TOTAL_STEPS: $1"
}

# Main installation process
main() {
    # Initial checks
    check_system_requirements
    create_backup
    
    # Exit on error
    set -e
    
    # 1. System update
    progress "Updating system packages"
    sudo apt update || check_error "System update"
    sudo apt upgrade -y || check_error "System upgrade"
    
    # 2. OpenCV Dependencies
    progress "Installing OpenCV dependencies"
    sudo apt install -y libhdf5-dev libhdf5-103 libqtgui4 libqtwebkit4 libqt4-test \
        libatlas-base-dev libjasper-dev libilmbase23 libopenexr23 libgstreamer1.0-dev \
        || check_error "OpenCV dependencies installation"
    
    sudo apt install -y python3-picamera2 || check_error "picamera2 installation"
    
    # 3. Virtual Environment Setup
    progress "Setting up Python virtual environment"
    sudo apt install -y python3-venv || check_error "venv installation"
    
    if [ ! -d "../cameo" ]; then
        python3 -m venv ../cameo --system-site-packages || check_error "Virtual environment creation"
    else
        log_warn "Virtual environment already exists, skipping creation"
    fi
    
    source ../cameo/bin/activate || check_error "Virtual environment activation"
    
    # 4. Python Dependencies
    progress "Installing Python dependencies"
    pip install --upgrade pip || check_error "pip upgrade"
    pip install cmake || check_error "cmake installation"
    pip install -r requirements.txt || check_error "Python requirements installation"
    
    # 5. Hailo Installation
    progress "Installing Hailo components"
    sudo apt-get install -y hailo-all || check_error "Hailo installation"
    sudo apt install rpicam-apps || check_error "rpicam-apps installation"
    
    # 6. System Libraries
    progress "Installing system libraries"
    sudo apt-get install -y \
        rsync ffmpeg x11-utils python3-dev python3-pip python3-setuptools \
        python3-virtualenv python-gi-dev libgirepository1.0-dev gcc-12 g++-12 \
        cmake git libzmq3-dev libopencv-dev python3-opencv libcairo2-dev \
        libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
        libgstreamer-plugins-bad1.0-dev gstreamer1.0-plugins-base \
        gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
        gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-tools \
        gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl gstreamer1.0-gtk3 \
        gstreamer1.0-qt5 gstreamer1.0-pulseaudio python3-gi python3-gi-cairo \
        gir1.2-gtk-3.0 gstreamer1.0-libcamera || check_error "System libraries installation"
    
    # 7. Repository Setup
    progress "Cloning and setting up repositories"
    cd ../
    if [ ! -d "tappas_gcc12" ]; then
        git clone https://github.com/Aoyamaxx/tappas_gcc12 || check_error "Repository cloning"
    else
        log_warn "tappas_gcc12 directory already exists, skipping clone"
    fi
    
    cd tappas_gcc12
    ./install.sh --skip-hailort --target-platform rpi || check_error "tappas installation"
    
    # 8. Final Setup
    progress "Performing final setup"
    cd ../
    cd Application
    pip install -e . || check_error "Application installation"
    
    # 9. Verification
    progress "Verifying installation"
    python3 -c "import cv2; print('OpenCV Version:', cv2.__version__)" || check_error "OpenCV verification"
    
    log_info "Installation completed successfully!"
}

# Run main function with error handling
if ! main; then
    log_error "Installation failed"
    exit 1
fi

# After successful installation, create startup script
create_startup() {
    log_info "Creating startup script..."
    
    # Create app.sh
    cat > "$HOME_DIR/app.sh" << EOL
#!/bin/bash

REPO_DIR="$REPO_DIR"
APP_DIR="$APP_DIR"

cd \$REPO_DIR

# Activate virtual environment
source cameo/bin/activate

cd \$APP_DIR

# Run the application
python -m rpi_control.launcher
EOL

    # Make app.sh executable
    chmod +x "$HOME_DIR/app.sh"
    
    # Create autostart directory
    mkdir -p "$HOME_DIR/.config/autostart"
    
    # Create desktop entry file
    cat > "$HOME_DIR/.config/autostart/app.desktop" << EOL
[Desktop Entry]
Type=Application
Name=App
Exec=/bin/bash $HOME_DIR/app.sh
X-GNOME-Autostart-enabled=true
EOL

    log_info "Startup configuration completed"
}

# Add this at the end of the script, after successful installation
if [ $? -eq 0 ]; then
    log_info "Setup completed successfully!"
    log_info "Creating startup configuration..."
    create_startup
    log_info "You can now activate the virtual environment with: source ../cameo/bin/activate"
    log_info "The application will start automatically on next boot"
else
    log_error "Installation failed"
    exit 1
fi
