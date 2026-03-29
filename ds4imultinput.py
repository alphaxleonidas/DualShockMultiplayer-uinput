import evdev
import uinput
import subprocess
import re
import config
import threading
from evdev import InputDevice, categorize, ecodes

class ControllerHandler:
    def __init__(self, device, controller_id):
        self.device = device
        self.controller_id = controller_id
        self.hat_state = {
            ecodes.ABS_HAT0X: 0,
            ecodes.ABS_HAT0Y: 0,
        }
        self.button_state = {'ps': False, 'start': False}
        self.last_values = {}
        self.mac_address = self.get_mac_by_name()
        
        # Create unique virtual controller name for each device
        controller_name = f"{config.controllerName} #{controller_id}"
        self.ui = uinput.Device(self._get_events(), name=controller_name)
        
        print(f"[Controller {controller_id}] Using device: {device.name}")
        if self.mac_address:
            print(f"[Controller {controller_id}] MAC Address: {self.mac_address}")

    def _get_events(self):
        """Define virtual controller events"""
        return (
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

    def get_mac_by_name(self, target_name=None):
        if target_name is None:
            target_name = self.device.name
        try:
            result = subprocess.run(
                ['bluetoothctl', 'devices'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            for line in result.stdout.strip().split('\n'):
                match = re.match(r'Device\s+([0-9A-F:]{17})\s+(.+)', line)
                if match:
                    mac, name = match.groups()
                    if name == target_name:
                        return mac
        except Exception as e:
            print(f"[Controller {self.controller_id}] Error getting MAC: {e}")
        return None

    def disconnect_bluetooth(self):
        if self.mac_address:
            print(f"[Controller {self.controller_id}] Disconnecting Bluetooth device...")
            try:
                subprocess.run(["bluetoothctl", "disconnect", self.mac_address], check=True)
                print(f"[Controller {self.controller_id}] Disconnected successfully.")
            except subprocess.CalledProcessError:
                print(f"[Controller {self.controller_id}] Failed to disconnect.")

    def check_disconnect_combo(self, code, val):
        if code == 'BTN_MODE':
            self.button_state['ps'] = (val == 1)
        elif code == 'BTN_START':
            self.button_state['start'] = (val == 1)
        return self.button_state['ps'] and self.button_state['start']

    def handle_events(self):
        """Main event loop for this controller"""
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

        try:
            for event in self.device.read_loop():
                if event.type == ecodes.EV_ABS:
                    code = event.code
                    val = event.value

                    if code in abs_map:
                        # Deadzone filtering
                        if code in (ecodes.ABS_X, ecodes.ABS_Y):  # Left stick
                            centered_val = val - config.CENTER
                            if abs(centered_val) < config.DEADZONE_L:
                                filtered_val = config.CENTER
                            else:
                                filtered_val = val
                        elif code in (ecodes.ABS_RX, ecodes.ABS_RY):  # Right stick
                            centered_val = val - config.CENTER
                            if abs(centered_val) < config.DEADZONE_R:
                                filtered_val = config.CENTER
                            else:
                                filtered_val = val
                        else:
                            filtered_val = val

                        if self.last_values.get(code) != filtered_val:
                            self.ui.emit(abs_map[code], filtered_val, syn=False)
                            self.last_values[code] = filtered_val

                        if code == ecodes.ABS_HAT0X:
                            self.hat_state[ecodes.ABS_HAT0X] = val
                        elif code == ecodes.ABS_HAT0Y:
                            self.hat_state[ecodes.ABS_HAT0Y] = val
                    else:
                        if config.DEBUG:
                            print(f"[Controller {self.controller_id}] [ABS] Unhandled: {code} = {val}")

                    self.ui.syn()

                elif event.type == ecodes.EV_KEY:
                    keyevent = categorize(event)
                    code = keyevent.keycode
                    val = 1 if keyevent.keystate == keyevent.key_down else 0

                    if isinstance(code, (list, tuple)):
                        code = code[0]

                    if self.check_disconnect_combo(code, val):
                        if config.BT_SWITCH:
                            print(f"[Controller {self.controller_id}] PS + Start combo detected!")
                            self.disconnect_bluetooth()
                            return  # Exit this controller's thread

                    if config.DEBUG:
                        print(f"[Controller {self.controller_id}] [KEY]: {code} = {val}")

                    if code in keymap:
                        if self.last_values.get(code) != val:
                            self.ui.emit(keymap[code], val)
                            self.last_values[code] = val
                    else:
                        if config.DEBUG:
                            print(f"[Controller {self.controller_id}] [KEY] Unmapped: {code} = {val}")

        except OSError as e:
            print(f"[Controller {self.controller_id}] Device disconnected or error: {e}")


def find_all_controllers():
    """Find all connected PS4/PS5 controllers"""
    devices = []
    controller_ids = {}
    device_list = [InputDevice(path) for path in evdev.list_devices()]
    
    for device in device_list:
        if config.DEBUG:
            print(f"Detected: {device.name}")
        if ("Wireless Controller" in device.name or
            "DualSense Wireless Controller" in device.name):
            caps = device.capabilities()
            if ecodes.EV_ABS in caps and ecodes.EV_KEY in caps:
                keys = caps.get(ecodes.EV_KEY, [])
                if ecodes.BTN_SOUTH in keys:
                    # Assign unique ID to each controller
                    device_path = device.path
                    if device_path not in controller_ids:
                        controller_ids[device_path] = len(devices) + 1
                    devices.append((device, controller_ids[device_path]))
    
    return devices


def main():
    print("Searching for DualShock/DualSense controllers...")
    controller_devices = find_all_controllers()
    
    if not controller_devices:
        print("No controllers found. Please connect your PS4/PS5 controller(s) first.")
        return
    
    print(f"Found {len(controller_devices)} controller(s)")
    
    threads = []
    
    # Create a thread for each controller
    for device, controller_id in controller_devices:
        handler = ControllerHandler(device, controller_id)
        thread = threading.Thread(target=handler.handle_events, daemon=True)
        thread.start()
        threads.append(thread)
        print(f"Started handler for controller {controller_id}")
    
    # Keep main thread alive
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\nShutting down all controllers...")


if __name__ == "__main__":
    main()
