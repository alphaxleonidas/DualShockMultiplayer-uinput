import evdev
import uinput
import subprocess
import re
import config
import threading
import time
from evdev import InputDevice, categorize, ecodes

class ControllerHandler:
    """Handles individual controller input and maps to unique player slot"""
    
    def __init__(self, device, player_id):
        self.device = device
        self.player_id = player_id
        self.hat_state = {
            ecodes.ABS_HAT0X: 0,
            ecodes.ABS_HAT0Y: 0,
        }
        self.button_state = {'ps': False, 'start': False}
        self.last_values = {}
        self.mac_address = self.get_mac_by_name()
        
        # Create unique virtual controller name with player number
        controller_name = f"{config.controllerName} - Player {player_id}"
        
        # Create virtual device with unique name for player identification
        self.ui = uinput.Device(self._get_events(), name=controller_name)
        
        print(f"[Player {player_id}] Controller registered: {device.name}")
        print(f"[Player {player_id}] Virtual device: {controller_name}")
        if self.mac_address:
            print(f"[Player {player_id}] MAC Address: {self.mac_address}")

    def _get_events(self):
        """Define virtual controller events - standard Xbox-style layout"""
        return (
            # Analog sticks
            uinput.ABS_X + (0, 255, 0, 0),      # Left stick X
            uinput.ABS_Y + (0, 255, 0, 0),      # Left stick Y
            uinput.ABS_RX + (0, 255, 0, 0),     # Right stick X
            uinput.ABS_RY + (0, 255, 0, 0),     # Right stick Y
            
            # Triggers
            uinput.ABS_Z + (0, 255, 0, 0),      # LT (L2)
            uinput.ABS_RZ + (0, 255, 0, 0),     # RT (R2)
            
            # Face buttons
            uinput.BTN_A,                        # Cross/A
            uinput.BTN_B,                        # Circle/B
            uinput.BTN_X,                        # Square/X
            uinput.BTN_Y,                        # Triangle/Y
            
            # Shoulder buttons
            uinput.BTN_TL,                       # LB (L1)
            uinput.BTN_TR,                       # RB (R1)
            
            # Menu buttons
            uinput.BTN_SELECT,                   # Share/Select
            uinput.BTN_START,                    # Options/Start
            
            # Stick clicks
            uinput.BTN_THUMBL,                   # Left stick click
            uinput.BTN_THUMBR,                   # Right stick click
            
            # D-pad
            uinput.ABS_HAT0X + (-1, 1, 0, 0),   # D-pad X
            uinput.ABS_HAT0Y + (-1, 1, 0, 0),   # D-pad Y
            
            # PS/Guide button
            uinput.BTN_MODE,
        )

    def get_mac_by_name(self, target_name=None):
        """Get MAC address of the connected controller"""
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
            print(f"[Player {self.player_id}] Error getting MAC: {e}")
        return None

    def disconnect_bluetooth(self):
        """Disconnect controller via Bluetooth"""
        if self.mac_address:
            print(f"[Player {self.player_id}] Disconnecting...")
            try:
                subprocess.run(["bluetoothctl", "disconnect", self.mac_address], check=True)
                print(f"[Player {self.player_id}] Disconnected successfully.")
            except subprocess.CalledProcessError:
                print(f"[Player {self.player_id}] Failed to disconnect.")

    def check_disconnect_combo(self, code, val):
        """Check if PS + Start combo is pressed"""
        if code == 'BTN_MODE':
            self.button_state['ps'] = (val == 1)
        elif code == 'BTN_START':
            self.button_state['start'] = (val == 1)
        return self.button_state['ps'] and self.button_state['start']

    def handle_events(self):
        """Main event loop for this controller/player"""
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

        print(f"[Player {self.player_id}] Event handler started")
        
        try:
            for event in self.device.read_loop():
                if event.type == ecodes.EV_ABS:
                    code = event.code
                    val = event.value

                    if code in abs_map:
                        # Apply deadzone filtering
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

                        # Only emit if value changed
                        if self.last_values.get(code) != filtered_val:
                            self.ui.emit(abs_map[code], filtered_val, syn=False)
                            self.last_values[code] = filtered_val

                        # Update hat state for D-pad
                        if code == ecodes.ABS_HAT0X:
                            self.hat_state[ecodes.ABS_HAT0X] = val
                        elif code == ecodes.ABS_HAT0Y:
                            self.hat_state[ecodes.ABS_HAT0Y] = val
                    else:
                        if config.DEBUG:
                            print(f"[Player {self.player_id}] [ABS] Unhandled: {code} = {val}")

                    self.ui.syn()

                elif event.type == ecodes.EV_KEY:
                    keyevent = categorize(event)
                    code = keyevent.keycode
                    val = 1 if keyevent.keystate == keyevent.key_down else 0

                    if isinstance(code, (list, tuple)):
                        code = code[0]

                    # Check for disconnect combo
                    if self.check_disconnect_combo(code, val):
                        if config.BT_SWITCH:
                            print(f"[Player {self.player_id}] PS + Start combo detected! Disconnecting...")
                            self.disconnect_bluetooth()
                            return  # Exit this player's thread

                    if config.DEBUG:
                        print(f"[Player {self.player_id}] [KEY]: {code} = {val}")

                    if code in keymap:
                        if self.last_values.get(code) != val:
                            self.ui.emit(keymap[code], val)
                            self.last_values[code] = val
                    else:
                        if config.DEBUG:
                            print(f"[Player {self.player_id}] [KEY] Unmapped: {code} = {val}")

        except OSError as e:
            print(f"[Player {self.player_id}] Device disconnected: {e}")
        except Exception as e:
            print(f"[Player {self.player_id}] Error: {e}")
        finally:
            print(f"[Player {self.player_id}] Handler stopped")


def find_all_controllers():
    """Find all connected PS4/PS5 controllers"""
    devices = []
    device_list = [InputDevice(path) for path in evdev.list_devices()]
    
    for device in device_list:
        if config.DEBUG:
            print(f"Detected device: {device.name} ({device.path})")
        
        if ("Wireless Controller" in device.name or
            "DualSense Wireless Controller" in device.name or
            "PS4 Controller" in device.name or
            "PlayStation 4" in device.name):
            
            caps = device.capabilities()
            if ecodes.EV_ABS in caps and ecodes.EV_KEY in caps:
                keys = caps.get(ecodes.EV_KEY, [])
                if ecodes.BTN_SOUTH in keys:
                    devices.append(device)
                    if config.DEBUG:
                        print(f"[DEBUG] Added controller: {device.name}")
    
    return devices


def main():
    print("=" * 60)
    print("DualShock Multi-Player Controller Handler")
    print("=" * 60)
    print("Searching for DualShock/DualSense controllers...")
    
    controller_devices = find_all_controllers()
    
    if not controller_devices:
        print("❌ No controllers found.")
        print("Please connect your PS4/PS5 controller(s) first via USB or Bluetooth.")
        return
    
    print(f"✓ Found {len(controller_devices)} controller(s)")
    print()
    
    threads = []
    
    # Create a thread for each controller, assigning player IDs starting from 1
    for idx, device in enumerate(controller_devices, start=1):
        print(f"Initializing Player {idx}: {device.name}")
        handler = ControllerHandler(device, player_id=idx)
        thread = threading.Thread(target=handler.handle_events, daemon=False)
        thread.start()
        threads.append((idx, thread))
        time.sleep(0.1)  # Small delay between controller initialization
    
    print()
    print("=" * 60)
    print(f"✓ All {len(threads)} controller(s) initialized as separate players")
    print("Press PS + Start to disconnect a controller")
    print("Press Ctrl+C to stop all controllers")
    print("=" * 60)
    print()
    
    # Keep main thread alive
    try:
        for player_id, thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("Shutting down all players...")
        print("=" * 60)


if __name__ == "__main__":
    main()
