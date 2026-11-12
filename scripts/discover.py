#!/usr/bin/env python3
"""
BroadLink device discovery and pairing script.

Usage:
    python3 scripts/discover.py

Output format:
    Device: <devtype>, IP: <ip>, MAC: <mac>, Name: <name>
"""

import broadlink
import json
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DEVICE_FILE = os.path.join(DATA_DIR, "device.json")


def discover_devices(timeout=5):
    """Discover BroadLink devices on the network."""
    print(f"[*] Scanning for BroadLink devices (timeout={timeout}s)...")
    
    try:
        devices = broadlink.discover(timeout=timeout)
        
        if not devices:
            print("[!] No devices found")
            return []
        
        discovered = []
        for d in devices:
            # Try to authenticate
            try:
                d.auth()
                print(f"[+] Device authenticated: {d.host[0]}")
            except Exception as e:
                print(f"[!] Auth failed for {d.host[0]}: {e}")
                continue
            
            info = {
                "devtype": d.devtype,
                "ip": d.host[0],
                "mac": d.mac.hex(),
                "name": getattr(d, 'name', 'Unknown')
            }
            discovered.append(info)
            print(f"    Device: devtype=0x{info['devtype']:04x}, IP={info['ip']}, MAC={info['mac']}")
        
        return discovered
        
    except Exception as e:
        print(f"[!] Discovery error: {e}")
        return []


def save_device_info(device):
    """Save device info to JSON file for later use."""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    with open(DEVICE_FILE, 'w') as f:
        json.dump(device, f, indent=2)
    
    print(f"[+] Device info saved to {DEVICE_FILE}")


def load_device_info():
    """Load saved device info."""
    if os.path.exists(DEVICE_FILE):
        with open(DEVICE_FILE, 'r') as f:
            return json.load(f)
    return None


def main():
    print("=" * 50)
    print("BroadLink Device Discovery")
    print("=" * 50)
    
    # Check for saved device
    saved_device = load_device_info()
    if saved_device:
        print(f"[*] Found saved device: {saved_device['ip']}")
    
    # Discover devices
    devices = discover_devices(timeout=5)
    
    if devices:
        # Save first device (usually the RM mini/pro)
        device = devices[0]
        save_device_info(device)
        
        print("\n[+] Discovery complete!")
        print(f"    Use this IP: {device['ip']}")
        print(f"    Use this MAC: {device['mac']}")
        return 0
    else:
        print("\n[!] No devices found. Make sure:")
        print("    1. BroadLink device is powered on")
        print("    2. Device is on same network as router")
        print("    3. Device is in pairing mode (LED blinking)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
