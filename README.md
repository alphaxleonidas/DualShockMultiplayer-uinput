# Disclaimer

Forked from [DualShock-uinput](https://github.com/sera-ina/DualShock-uinput)

The original repo was made by ChatGPT but this fork has been modified using Copilot. Sorry if it's messy. 

This fork has been modified for multicontroller support and hotplugging. 

# Description

I wanted a tool that works systemwide for any game so I don't always have to rely on SteamInput/Bottles/Lutris. Works wired and via Bluetooth. Works for PS4 and PS5 controller.

It in general reads the raw input from the PS controllers and sends it as a virtual controller in uinput (xinput), which I needed especially in older games which don't support DirectInput at all.

~~**It only works for one active controller!**~~

**It works with multiple active controllers. Tested on two.**



## Requirements
### packages
- python3
- python3-dev
- python3-venv
- python3-pyudev (for hotplug support)
### pip
- python_uinput
- evdev
### system
- bluetoothctl
  - if desired to be able to disconnect the controller via (PS + Start) combination
### dependency installation
- for an ubuntu based distro, use:
```
sudo apt update
sudo apt install python3-dev python3-venv python3-pyudev
```
note: rest of the dependencies are not needed in my testing. might have to use ```bluez``` instead of ```bluetoothctl``` for ubuntu based distros.

# Installation
Download the files manually or clone repo
```
cd ~
git clone https://github.com/alphaxleonidas/DualShockMultiplayer-uinput.git
```

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
~/.venv/bin/pip install -r ~/DualShockMultiplayer-uinput/requirements.txt
```
Create udev rules file
```
sudo nano /etc/udev/rules.d/99-psinput.rules
```
and add
```
KERNEL=="uinput", MODE="0660", GROUP="input"
```
Add user to input group
```
sudo usermod -aG input $USER
```
Load uinput module
```
sudo modprobe uinput
```
Reload udev rules
```
sudo udevadm control --reload-rules
sudo udevadm trigger
```

# Usage

**Steps:**
- **Connect you PS4/PS5 controller first via USB or Bluetooth**, then run the script
```
~/.venv/bin/python ~/DualShockMultiplayer-uinput/ds4input_multiplayerv2.py
```
as the script looks for the controller directly on start else the script will just stop with an error.

# Creating an App Entry

Instead of running the command, you can create a launch script which will appear in the App Menu.
```
nano ~/.local/share/applications/ds4input_multiplayerv2.desktop
```
Add this to the file: 
```
[Desktop Entry]
Version=1.0
Name=DualShock Multiplayer uinput
Comment=Run DualShock DS4 input script Hot plugging
Exec=/home/<username>/.venv/bin/python /home/<username>/DualShockMultiplayer-uinput/ds4input_multiplayerv2.py
Type=Application
Icon=input-gaming
Terminal=false
Categories=Utility;Game;
Keywords=ds4;dualshock4;controller;dualsense;sense;
```
Replace ```<username>``` with your username, so the paths becomes correct. E.g. 

```Exec=/home/randomusername/.venv/bin/python /home/randomusername/DualShockMultiplayer-uinput/ds4input_multiplayerv2.py```

Now make this desktop entry an executeable:
```
chmod +x ~/.local/share/applications/ds4input_multiplayerv2.desktop
```
Now logout and relogin into a new session. You will see ```DualShock Multiplayer uinput``` in the appmenu.
Now connect your DualShock or DualSense and run the ```DualShock Multiplayer uinput``` from the appmenu.

# Disconnect
To disconnect from bluetooth, use (PS + Start) 

# Additional Infos
- No vibration / force feedback
- The PS button is a separate button that you can map, for example in AntiMicroX
- In the config.py file you can change the deadzone of each stick, the name of the controller and if you want to be able to use the (PS + Start) combo to disconnect the controller.
- ```ds4input_multiplayerv2.py``` is for hotplugging support.

# Issues 
- ~~If the controller is disconnected while the script is running, reconnecting will not make it work. You will have to restart the script. So expect some degree of memory leak.~~  Fixed with ds4input_multiplayerv2.py .
- After first connecting, the system automatically registers up+forward input from the controller. Which resolves after moving the Left Analogue Stick.
