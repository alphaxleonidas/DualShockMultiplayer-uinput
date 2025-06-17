# Disclaimer

The script is as-is. I personally have no experience in python and the script was made by 99% with ChatGPT (with a few hours of troubleshooting and feeding it with outputs). So expect a spaghetti code... sorry.

# Description

This script wraps a PS4 or PS5 controller and creates a uinput controller (xinput controller) that should make it work with any game that also supports gamepad in general or xbox controllers. Works systemwide without the need for steam input, lutris or bottles. Works wired and via Bluetooth.

**It only works for one active controller!**

# Installing
Download the files manually or clone
```
git clone https://github.com/sera-ina/DualShock-uinput.git
```

## Requirements
- python3
- python3-dev
- python_uinput
- evdev
- bluetoothctl
  - if desired to be able to disconnect the controller via (PS + Start) combination

## Preparation

Once you installed python on your system, create a virtual enviroment (for example ".venv" in your home folder)
```
python3 -m venv ~/.venv
```
Update pip
```
~/.venv/bin/pip install --upgrade pip setuptools wheel
```
When it is done, install the dependencies manually or with the requirements.txt file
```
~/.venv/bin/pip install -r requirements.txt
```

# Usage
In the config.py file you can change the deadzone of each stick, the name of the controller and if you want to be able to use the (PS + Start) combo to disconnect the controller.

**Connect you PS4/PS5 controller first via USB or Bluetooth**, then run the script
```
~/.venv/bin/python ds4input.py
```
as the script looks for the controller directly on start.
