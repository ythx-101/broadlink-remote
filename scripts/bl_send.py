#!/usr/bin/env python3
"""
bl_send.py — Broadlink IR sender, zero Python crypto dependency.
Uses openssl CLI for AES-128-CBC. Runs on OpenWrt/aarch64 routers.

Usage:
  python3 bl_send.py power_on
  python3 bl_send.py power_off
  python3 bl_send.py --ip 192.168.8.221 --codes /path/to/ir_codes.json power_on
"""
import socket, struct, json, base64, subprocess, sys, os, time, random

DEVICE_IP = os.environ.get("BL_IP", "192.168.1.100")
DEVICE_PORT = 80
INIT_KEY = bytes.fromhex("097628343fe99e23765c1513accf8b02")
INIT_IV  = bytes.fromhex("562e17996d093d28ddb3ba695a2e6f58")
TIMEOUT  = 5

class BroadlinkDevice:
    def __init__(self, ip, port=80):
        self.host = (ip, port)
        self.mac = bytes(6)  # discovered during auth
        self.devtype = 0
        self.count = random.randint(0x8000, 0xFFFF)
        self.id = 0
        self.key = INIT_KEY
        self.iv = INIT_IV

    def _aes_encrypt(self, data):
        p = subprocess.run(
            ["openssl", "enc", "-aes-128-cbc", "-nopad",
             "-K", self.key.hex(), "-iv", self.iv.hex()],
            input=data, capture_output=True, timeout=5
        )
        if p.returncode != 0:
            raise RuntimeError(f"openssl encrypt failed: {p.stderr.decode()}")
        return p.stdout

    def _aes_decrypt(self, data):
        p = subprocess.run(
            ["openssl", "enc", "-d", "-aes-128-cbc", "-nopad",
             "-K", self.key.hex(), "-iv", self.iv.hex()],
            input=data, capture_output=True, timeout=5
        )
        if p.returncode != 0:
            raise RuntimeError(f"openssl decrypt failed: {p.stderr.decode()}")
        return p.stdout

    def send_packet(self, packet_type, payload):
        self.count = ((self.count + 1) | 0x8000) & 0xFFFF
        packet = bytearray(0x38)
        packet[0x00:0x08] = bytes.fromhex("5aa5aa555aa5aa55")
        packet[0x24:0x26] = self.devtype.to_bytes(2, "little")
        packet[0x26:0x28] = packet_type.to_bytes(2, "little")
        packet[0x28:0x2A] = self.count.to_bytes(2, "little")
        packet[0x2A:0x30] = self.mac[::-1]
        packet[0x30:0x34] = self.id.to_bytes(4, "little")

        p_checksum = (sum(payload) + 0xBEAF) & 0xFFFF
        packet[0x34:0x36] = p_checksum.to_bytes(2, "little")

        padding = (16 - len(payload) % 16) % 16
        encrypted = self._aes_encrypt(bytes(payload) + bytes(padding))
        packet.extend(encrypted)

        checksum = (sum(packet) + 0xBEAF) & 0xFFFF
        packet[0x20:0x22] = checksum.to_bytes(2, "little")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(TIMEOUT)
        try:
            sock.sendto(bytes(packet), self.host)
            resp = sock.recv(2048)
            return resp
        finally:
            sock.close()

    def discover_and_auth(self):
        """Discover device via UDP broadcast, then authenticate."""
        # Step 1: Discover
        cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cs.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        cs.settimeout(TIMEOUT)

        addr = socket.gethostbyname(socket.gethostname())
        parts = addr.split(".")

        packet = bytearray(0x30)
        now = time.localtime()
        packet[0x08] = now.tm_year & 0xFF
        packet[0x09] = (now.tm_year >> 8) & 0xFF
        packet[0x0A] = now.tm_min
        packet[0x0B] = now.tm_hour
        subyear = now.tm_year % 100
        packet[0x0C] = subyear
        packet[0x0D] = now.tm_wday
        packet[0x0E] = now.tm_mday
        packet[0x0F] = now.tm_mon
        for i, p in enumerate(parts):
            packet[0x18 + i] = int(p) & 0xFF
        packet[0x1C:0x1E] = (80).to_bytes(2, "little")  # source port
        packet[0x26] = 6  # command: discover

        checksum = (sum(packet) + 0xBEAF) & 0xFFFF
        packet[0x20:0x22] = checksum.to_bytes(2, "little")

        cs.sendto(bytes(packet), (self.host[0], 80))
        try:
            resp, addr = cs.recvfrom(2048)
            self.mac = resp[0x3A:0x40]
            self.devtype = int.from_bytes(resp[0x34:0x36], "little")
            print(f"Discovered: devtype=0x{self.devtype:04x}, mac={self.mac.hex()}")
        except socket.timeout:
            # If broadcast discover fails, try direct auth with zeroed mac
            print("Broadcast discover timed out, trying direct auth...")
        finally:
            cs.close()

        # Step 2: Auth
        payload = bytearray(0x50)
        payload[0x04:0x14] = [0x31] * 16
        payload[0x1E] = 0x01
        payload[0x2D] = 0x01
        payload[0x30:0x36] = b"Test 1"

        resp = self.send_packet(0x65, payload)

        # Check error
        err = int.from_bytes(resp[0x22:0x24], "little")
        if err != 0:
            raise RuntimeError(f"Auth error: {err}")

        dec = self._aes_decrypt(resp[0x38:])
        self.id = int.from_bytes(dec[0x00:0x04], "little")
        self.key = dec[0x04:0x14]
        print(f"Authenticated: id=0x{self.id:08x}")

    def send_ir(self, ir_data):
        """Send IR data (broadlink format). RM4 Mini uses length-prefixed packet."""
        # RM4 Mini (0x520c) uses: <H length> <I command> <data>
        # RM2/Pro uses: <I command> <data>
        is_rm4 = self.devtype in (0x520c, 0x5213, 0x5218, 0x6026, 0x6184, 0x610e, 0x610f, 0x62bc, 0x62be, 0x649b, 0x653a)
        if is_rm4:
            packet = struct.pack("<HI", len(ir_data) + 4, 0x02) + ir_data
        else:
            packet = struct.pack("<I", 0x02) + ir_data
        resp = self.send_packet(0x6A, packet)
        err = int.from_bytes(resp[0x22:0x24], "little")
        if err != 0:
            raise RuntimeError(f"Send IR error: {err}")
        print("IR sent successfully ✅")

def main():
    import argparse
    p = argparse.ArgumentParser(description="Broadlink IR sender (no crypto dependency)")
    p.add_argument("action", help="IR code key from codes file (e.g. power_on)")
    p.add_argument("--ip", default=DEVICE_IP, help="Device IP")
    p.add_argument("--codes", default=None, help="Path to ir_codes.json")
    args = p.parse_args()

    # Find codes file
    codes_path = args.codes
    if not codes_path:
        for candidate in [
            os.path.join(os.path.dirname(__file__), "..", "data", "ir_codes.json"),
            os.path.expanduser("~/broadlink-ac/data/ir_codes.json"),
        ]:
            if os.path.exists(candidate):
                codes_path = candidate
                break
    if not codes_path or not os.path.exists(codes_path):
        print(f"ERROR: ir_codes.json not found"); sys.exit(1)

    codes = json.load(open(codes_path))
    if args.action not in codes:
        print(f"ERROR: '{args.action}' not in codes. Available: {list(codes.keys())}")
        sys.exit(1)

    ir_data = base64.b64decode(codes[args.action])

    dev = BroadlinkDevice(args.ip)
    dev.discover_and_auth()
    dev.send_ir(ir_data)

if __name__ == "__main__":
    main()
