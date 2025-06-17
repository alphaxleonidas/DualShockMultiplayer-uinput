import evdev
import uinput
import subprocess
from evdev import InputDevice, categorize, ecodes

DEBUG = False

# Deadzone constants and center value
CENTER = 128
DEADZONE_L = 10  # Left stick deadzone
DEADZONE_R = 10  # Right stick deadzone

# Bluetooth MAC addresses to disconnect
BT_MACS = [
    "84:17:66:82:57:F3",   # DS4 MAC - replace with yours
    "D0:BC:C1:7F:32:BD",   # DualSense MAC - replace with yours
]

# Find DS4 or DualSense controller device
def find_controller():
    devices = [InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        if DEBUG:
            print(f"Detected: {device.name}")
        if ("Wireless Controller" in device.name or
            "DualSense Wireless Controller" in device.name or
            "Xbox One S Controller" in device.name):
            return device
    raise RuntimeError("Controller not found")

# Define virtual Xbox 360 controller events
events = (
    uinput.ABS_X + (0, 255, 0, 0),
    uinput.ABS_Y + (0, 255, 0, 0),
    uinput.ABS_RX + (0, 255, 0, 0),
    uinput.ABS_RY + (0, 255, 0, 0),
    uinput.ABS_Z + (0, 255, 0, 0),     # LT
    uinput.ABS_RZ + (0, 255, 0, 0),    # RT

    uinput.BTN_A,
    uinput.BTN_B,
    uinput.BTN_X,
    uinput.BTN_Y,
    uinput.BTN_TL,        # LB
    uinput.BTN_TR,        # RB
    uinput.BTN_SELECT,
    uinput.BTN_START,
    uinput.BTN_THUMBL,
    uinput.BTN_THUMBR,

    uinput.ABS_HAT0X + (-1, 1, 0, 0),  # D-pad X
    uinput.ABS_HAT0Y + (-1, 1, 0, 0),  # D-pad Y

    uinput.BTN_MODE,
)

# Maps for buttons and axes
keymap = {
    'BTN_SOUTH': uinput.BTN_A,
    'BTN_A': uinput.BTN_A,
    'BTN_GAMEPAD': uinput.BTN_A,

    'BTN_EAST': uinput.BTN_B,
    'BTN_B': uinput.BTN_B,

    'BTN_WEST': uinput.BTN_X,
    'BTN_Y': uinput.BTN_X,

    'BTN_NORTH': uinput.BTN_Y,
    'BTN_X': uinput.BTN_Y,

    'BTN_TL': uinput.BTN_TL,
    'BTN_TR': uinput.BTN_TR,
    'BTN_SELECT': uinput.BTN_SELECT,
    'BTN_START': uinput.BTN_START,
    'BTN_THUMBL': uinput.BTN_THUMBL,
    'BTN_THUMBR': uinput.BTN_THUMBR,

    'KEY_UP': uinput.ABS_HAT0Y,
    'KEY_DOWN': uinput.ABS_HAT0Y,
    'KEY_LEFT': uinput.ABS_HAT0X,
    'KEY_RIGHT': uinput.ABS_HAT0X,

    'BTN_MODE': uinput.BTN_MODE,
}

abs_map = {
    ecodes.ABS_X: uinput.ABS_X,
    ecodes.ABS_Y: uinput.ABS_Y,
    ecodes.ABS_RX: uinput.ABS_RX,
    ecodes.ABS_RY: uinput.ABS_RY,
    ecodes.ABS_Z: uinput.ABS_Z,
    ecodes.ABS_RZ: uinput.ABS_RZ,
    ecodes.ABS_HAT0X: uinput.ABS_HAT0X,
    ecodes.ABS_HAT0Y: uinput.ABS_HAT0Y,
}

hat_state = {
    ecodes.ABS_HAT0X: 0,
    ecodes.ABS_HAT0Y: 0,
}

button_state = {'ps': False, 'start': False}
last_values = {}

def check_disconnect_combo(code, val, state):
    if code == 'BTN_MODE':  # PS button
        state['ps'] = (val == 1)
    elif code == 'BTN_START':
        state['start'] = (val == 1)
    return state['ps'] and state['start']

def disconnect_bluetooth(mac_addresses):
    for mac in mac_addresses:
        print(f"Disconnecting Bluetooth device {mac} ...")
        try:
            subprocess.run(["bluetoothctl", "disconnect", mac], check=True)
            print(f"Disconnected {mac} successfully.")
        except subprocess.CalledProcessError:
            print(f"Failed to disconnect device {mac}.")

device = find_controller()
print(f"Using controller device: {device.name}")

ui = uinput.Device(events, name="Virtual Xinput Controller")

# Main event loop
for event in device.read_loop():
    if event.type == ecodes.EV_ABS:
        code = event.code
        val = event.value

        if code in abs_map:
            # Deadzone filtering
            if code in (ecodes.ABS_X, ecodes.ABS_Y):  # Left stick
                centered_val = val - CENTER
                if abs(centered_val) < DEADZONE_L:
                    filtered_val = CENTER
                else:
                    filtered_val = val
            elif code in (ecodes.ABS_RX, ecodes.ABS_RY):  # Right stick
                centered_val = val - CENTER
                if abs(centered_val) < DEADZONE_R:
                    filtered_val = CENTER
                else:
                    filtered_val = val
            else:
                filtered_val = val

            if last_values.get(code) != filtered_val:
                ui.emit(abs_map[code], filtered_val, syn=False)
                last_values[code] = filtered_val

            # Update hat state for D-pad for completeness
            if code == ecodes.ABS_HAT0X:
                hat_state[ecodes.ABS_HAT0X] = val
            elif code == ecodes.ABS_HAT0Y:
                hat_state[ecodes.ABS_HAT0Y] = val
        else:
            if DEBUG:
                print(f"[ABS] Unhandled: {code} = {val}")

        ui.syn()

    elif event.type == ecodes.EV_KEY:
        keyevent = categorize(event)
        code = keyevent.keycode
        val = 1 if keyevent.keystate == keyevent.key_down else 0

        if isinstance(code, (list, tuple)):
            code = code[0]

        if check_disconnect_combo(code, val, button_state):
            print("PS + Start combo detected! Disconnecting Bluetooth devices...")
            disconnect_bluetooth(BT_MACS)
            break

        if DEBUG:
            print(f"[DEBUG] KEY: {code} = {val}")

        if code in keymap:
            if last_values.get(code) != val:
                ui.emit(keymap[code], val)
                last_values[code] = val
        else:
            if DEBUG:
                print(f"[KEY] Unmapped: {code} = {val}")
