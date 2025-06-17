# Disclaimer

The script is as-is. I personally have no experience in python and the script was made by 99% with ChatGPT (with a few hours of troubleshooting and feeding it with outputs).

# Description

This script wraps a PS4 or PS5 controller and creates a uinput controller (or an xinput controller) that should make it work with any game that also supports gamepad in general or xbox controllers. Works systemwide without the need for steam input, lutris or bottles. Works wired and via Bluetooth.

**It only works for one active controller!**

# Installing
## Requirements
- python3
  - tested with Python 3.13.3
- pip
- python_uinput 1.0.1
- evdev 1.9.2

## Preparation

Once you installed python on your system, create a virtual enviroment (for example ".venv" in your home folder)
```
python3 -m venv ~/.venv
```
