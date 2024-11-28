from setuptools import setup, find_packages

setup(
    name="rpi-control",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt5>=5.15.0",
        "wifi>=0.3.8",
        "opencv-python",
        "cmake",
        "face_recognition",
        "cvzone",
        "mediapipe",
        "numpy",
        "scipy",
        "pillow",
        "ultralytics",
        "tensorflow",
        "scikit-learn",
        "face_recognition",
        "dlib"
    ],
    entry_points={
        'console_scripts': [
            'rpi-control=rpi_control.main:main',
        ],
    },
    author="Your Name",
    description="A Raspberry Pi control interface with network management and screensaver",
    keywords="raspberry-pi, qt, wifi",
    python_requires=">=3.7",
    package_data={
        'rpi_control': ['assets/*'],
    },
)
