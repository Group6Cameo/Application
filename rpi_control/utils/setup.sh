#!/bin/bash

# echo "Updating system packages..."
# sudo apt update
# sudo apt upgrade -y

# echo "Installing system dependencies for OpenCV..."
# sudo apt install -y libhdf5-dev libhdf5-103 libqtgui4 libqtwebkit4 libqt4-test libatlas-base-dev libjasper-dev libilmbase23 libopenexr23 libgstreamer1.0-dev

# sudo apt install -y python3-picamera2

# echo "Installing Python dependencies..."
# pip install --upgrade pip
# pip install cmake
# pip install -r requirements.txt

wget https://github.com/davisking/dlib-models/raw/41b158a24d569c8f12151a407fd1cee99fcf3d8b/dlib_face_recognition_resnet_model_v1.dat.bz2
bunzip2 dlib_face_recognition_resnet_model_v1.dat.bz2

wget https://github.com/davisking/dlib-models/raw/41b158a24d569c8f12151a407fd1cee99fcf3d8b/shape_predictor_68_face_landmarks.dat.bz2
bunzip2 shape_predictor_68_face_landmarks.dat.bz2

wget -O res10_300x300_ssd_iter_140000.caffemodel https://github.com/keyurr2/face-detection/raw/20884cfc72638a16b8982076073c742fb2fb84f5/res10_300x300_ssd_iter_140000.caffemodel

echo "Setup complete. Run 'source cameo/bin/activate' to activate the virtual environment."