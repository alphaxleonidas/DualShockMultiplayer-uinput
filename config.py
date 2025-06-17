# set to True if you need some debug output in the console, generally not needed
DEBUG = False

# Deadzone settings, CENTER should be left untouched
CENTER = 128
DEADZONE_L = 10  # Left stick
DEADZONE_R = 10  # Right stick

#enables or disables the shortcut (PS Button + Start) to disconnect the controller on use. set to "False" if not desired
BT_SWITCH = True

# Bluetooth MAC addresses to disconnect. If you have multiple ps4/ps5 controllers then set their addresses here. you can find the addresses via terminal "bluetoothctl devices"
BT_MACS = [
    "84:17:66:82:57:F3",   # DS4 MAC - replace with yours
    "D0:BC:C1:7F:32:BD",   # DualSense MAC - replace with yours
]

#change the name of the created virtual controller
controllerName="Virtual Uinput Controller"
