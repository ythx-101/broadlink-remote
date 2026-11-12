#!/usr/bin/env python3
"""
BroadLink AC Control Script
Core control script for learning and sending IR signals.

Usage (PC / Raspberry Pi with broadlink installed):
    python3 scripts/ac_control.py <command> [args]

Commands:
    discover              - Discover BroadLink device
    learn <name>         - Learn IR signal (press remote button)
    send <name>          - Send learned IR signal
    ac on/off            - Turn AC on/off
    ac temp <degrees>    - Set temperature
    ac mode <mode>       - Set mode (cool/heat/auto/dry/fan)
    list                 - List all learned signals
"""

import broadlink
import json
import os
import sys
import time
import threading
from pathlib import Path

# Configuration
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
DEVICE_FILE = os.path.join(DATA_DIR, "device.json")
IR_CODES_FILE = os.path.join(DATA_DIR, "ir_codes.json")

# Device defaults (can be overridden by device.json)
DEFAULT_IP = os.environ.get("BL_IP", "192.168.1.100")
DEFAULT_MAC = os.environ.get("BL_MAC", "000000000000")


def load_device():
    """Load device info from file or use defaults."""
    if os.path.exists(DEVICE_FILE):
        with open(DEVICE_FILE, 'r') as f:
            return json.load(f)
    return {"ip": DEFAULT_IP, "mac": DEFAULT_MAC}


def save_device(device):
    """Save device info to file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DEVICE_FILE, 'w') as f:
        json.dump(device, f, indent=2)


def load_ir_codes():
    """Load learned IR codes from file."""
    if os.path.exists(IR_CODES_FILE):
        with open(IR_CODES_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_ir_codes(codes):
    """Save IR codes to file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(IR_CODES_FILE, 'w') as f:
        json.dump(codes, f, indent=2)


def create_device():
    """Create and authenticate a BroadLink device from saved info or defaults."""
    device_info = load_device()
    ip = device_info["ip"]
    if isinstance(ip, (list, tuple)):
        ip = ip[0]
    mac = bytes.fromhex(device_info["mac"])
    devtype = device_info.get("devtype", 0x520c)  # default: RM4 Mini
    device = broadlink.gendevice(devtype, (ip, 80), mac)
    device.auth()
    return device


def cmd_discover():
    """Discover BroadLink devices on the network."""
    print("[*] Discovering BroadLink devices...")
    
    devices = broadlink.discover(timeout=5)
    
    if not devices:
        print("[!] No devices found")
        return False
    
    for d in devices:
        try:
            d.auth()
        except Exception:
            pass
        
        device_info = {
            "ip": d.host[0],
            "mac": d.mac.hex(),
            "devtype": d.devtype,
            "name": getattr(d, 'name', 'BroadLink RM')
        }
        save_device(device_info)
        
        print(f"[+] Found: {d.host[0]} (MAC: {device_info['mac']}, Type: 0x{d.devtype:04x})")
    
    return True


def cmd_learn(name):
    """Learn an IR signal."""
    if not name:
        print("[!] Please specify signal name")
        return False
    
    print(f"[*] Learning signal: {name}")
    print("[*] Press the remote button now...")
    
    device = create_device()
    
    try:
        device.enter_learning()
    except Exception as e:
        print(f"[!] Failed to enter learning mode: {e}")
        return False
    
    # Wait for signal (max 30 seconds)
    start_time = time.time()
    while time.time() - start_time < 30:
        time.sleep(1)
        
        try:
            data = device.check_data()
            if data:
                # broadlink >= 0.19 already returns the bare IR data
                ir_data = data
                
                # Save the IR code
                codes = load_ir_codes()
                codes[name] = ir_data.hex()
                save_ir_codes(codes)
                
                print(f"[+] Learned: {name} ({len(ir_data)} bytes)")
                return True
        except Exception as e:
            # No data yet, continue waiting
            pass
    
    print("[!] No signal received (timeout)")
    return False


def cmd_send(name):
    """Send a learned IR signal."""
    codes = load_ir_codes()
    
    if name not in codes:
        print(f"[!] Signal '{name}' not found")
        print(f"    Available: {', '.join(codes.keys()) if codes else 'none'}")
        return False
    
    print(f"[*] Sending: {name}")
    
    device = create_device()
    
    try:
        ir_data = bytes.fromhex(codes[name])
        device.send_data(ir_data)
        print(f"[+] Sent: {name}")
        return True
    except Exception as e:
        print(f"[!] Failed to send: {e}")
        return False


def cmd_list():
    """List all learned signals."""
    codes = load_ir_codes()
    
    if not codes:
        print("[*] No learned signals")
        return True
    
    print("[*] Learned signals:")
    for name, data in codes.items():
        print(f"    {name}: {len(data)//2} bytes")
    
    return True


# AC control commands
AC_COMMANDS = {
    "on": "power_on",
    "off": "power_off",
    "cool": "mode_cool",
    "heat": "mode_heat",
    "auto": "mode_auto",
    "dry": "mode_dry",
    "fan": "mode_fan",
}


def cmd_ac(action, value=None):
    """Control AC (on/off/temp/mode)."""
    device_info = load_device()
    
    if action == "on":
        # Turn on with default settings
        signal = "power_on"
        return cmd_send(signal)
    
    elif action == "off":
        signal = "power_off"
        return cmd_send(signal)
    
    elif action == "temp":
        if not value:
            print("[!] Please specify temperature")
            return False
        
        temp = int(value)
        if temp < 16 or temp > 30:
            print("[!] Temperature must be 16-30")
            return False
        
        signal = f"temp_{temp}"
        
        # If we have this specific temp, send it
        codes = load_ir_codes()
        if signal in codes:
            return cmd_send(signal)
        
        print(f"[*] Setting temperature to {temp}°C")
        return cmd_send(signal)
    
    elif action == "mode":
        if not value:
            print("[!] Please specify mode (cool/heat/auto/dry/fan)")
            return False
        
        signal = f"mode_{value}"
        codes = load_ir_codes()
        
        if signal not in codes:
            print(f"[!] Signal '{signal}' not learned yet")
            print(f"    Run: ac_control.py learn {signal}")
            return False
        
        return cmd_send(signal)
    
    else:
        print(f"[!] Unknown AC action: {action}")
        print(f"    Valid: on, off, temp <16-30>, mode <cool/heat/auto/dry/fan>")
        return False


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    
    cmd = sys.argv[1]
    
    if cmd == "discover":
        return 0 if cmd_discover() else 1
    
    elif cmd == "learn":
        name = sys.argv[2] if len(sys.argv) > 2 else None
        return 0 if cmd_learn(name) else 1
    
    elif cmd == "send":
        name = sys.argv[2] if len(sys.argv) > 2 else None
        if not name:
            print("[!] Please specify signal name")
            return 1
        return 0 if cmd_send(name) else 1
    
    elif cmd == "list":
        return 0 if cmd_list() else 1
    
    elif cmd == "ac":
        if len(sys.argv) < 3:
            print("[!] Usage: ac_control.py ac <on/off/temp/mode> [value]")
            return 1
        
        action = sys.argv[2]
        value = sys.argv[3] if len(sys.argv) > 3 else None
        return 0 if cmd_ac(action, value) else 1
    
    else:
        print(f"[!] Unknown command: {cmd}")
        print(__doc__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
