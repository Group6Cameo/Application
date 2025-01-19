from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name="rpi-control",
    version="0.1.0",
    packages=find_packages(),
    install_requires=required,
    entry_points={
        'console_scripts': [
            'rpi-control=rpi_control.launcher:main',
            'rpi-control-gui=rpi_control.main:main',
            'rpi-control-server=rpi_control.server:main',
        ],
    },
    author="Montijn van den Beukel",
    description="A Raspberry Pi control interface for Cameo",
    keywords="raspberry-pi, qt, wifi",
    python_requires=">=3.7",
    package_data={
        'rpi_control': ['assets/*', 'static/*'],
    },
)
