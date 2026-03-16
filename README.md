<div align="center">

# 🦞 broadlink-remote

**Control any IR device with BroadLink RM4 — no app needed.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-blue.svg)](https://github.com/openclaw/openclaw)
[![Python 3.7+](https://img.shields.io/badge/Python-3.7+-green.svg)](https://www.python.org)
[![GitHub stars](https://img.shields.io/github/stars/ythx-101/broadlink-remote?style=social)](https://github.com/ythx-101/broadlink-remote)

*No official app · Learn or calculate IR codes · Zero-dep sender for routers · OpenClaw ready*

[Quick Start](#-quick-start) · [Two Ways to Get IR Codes](#-two-ways-to-get-ir-codes) · [How It Works](#-how-it-works) · [Story](#-story)

</div>

---

## 😤 Problem

```
You: turn on the AC
AI:  I can't control physical devices.

You: ...seriously?
```

BroadLink sells a $8 IR blaster. But the official app is required for setup, and there's no clean CLI/API for agents.

**broadlink-remote** solves this: script-only WiFi setup, IR learning, and protocol-based code calculation — all from the command line. No app, no cloud, no account.

## 📊 What You Get

| Feature | Description |
|---------|-------------|
| 🔌 WiFi setup | Configure RM4 without official app |
| 📡 IR learning | Record signals from physical remote |
| 🧮 Protocol calc | Generate IR codes from protocol specs |
| 🪶 Zero-dep sender | `bl_send.py` runs on OpenWrt (only needs `openssl`) |
| 🦞 OpenClaw integration | Say "turn on the AC" → done |

> **For AI Agents**: All scripts are CLI-friendly with clear exit codes. Import `encode_broadlink()` for direct integration.

## 🚀 Quick Start

### 30 seconds (experienced users)

```bash
pip install broadlink
git clone https://github.com/ythx-101/broadlink-remote.git
cd broadlink-remote

# 1. Setup WiFi (hold Reset on RM4, connect to its hotspot, then:)
python3 scripts/wifi_setup.py --ssid "YourWiFi" --password "YourPass"

# 2. Discover device
python3 scripts/discover.py

# 3. Learn IR codes (point remote at RM4, press buttons)
python3 scripts/ac_control.py learn power_on
python3 scripts/ac_control.py learn power_off

# 4. Control
python3 scripts/ac_control.py ac on
```

### Step by Step

#### Step 1: WiFi Setup (one-time, no app)

```bash
# Hold RM4 Reset button 5-10s → LED blinks fast
# Connect your computer to "BroadLink_xxx" hotspot
python3 scripts/wifi_setup.py --ssid "YourWiFi" --password "YourPass" --security 4
# Wait 10-20s → LED goes solid → switch back to your WiFi
```

Security modes: `0`=open, `1`=WEP, `2`=WPA1, `3`=WPA2, `4`=WPA1/2 (default)

#### Step 2: Discover Device

```bash
python3 scripts/discover.py
# [+] Found: 192.168.1.xxx (MAC: xxxxxxxxxxxx, Type: 0x520c)
```

#### Step 3: Get IR Codes

```bash
# Learn from remote (point at RM4 and press buttons)
python3 scripts/ac_control.py learn power_on
python3 scripts/ac_control.py learn power_off
python3 scripts/ac_control.py learn temp_26

# Or calculate from protocol (when learning fails)
python3 scripts/tcl_send.py 0  # Generate TCL AC code candidate #0
```

#### Step 4: Control

```bash
# Full control (needs broadlink library)
python3 scripts/ac_control.py ac on
python3 scripts/ac_control.py ac off
python3 scripts/ac_control.py ac temp 26
python3 scripts/ac_control.py ac mode cool

# Zero-dep sender (only needs openssl, for routers)
python3 scripts/bl_send.py power_on
python3 scripts/bl_send.py power_off

# Remote via SSH (OpenClaw integration)
bash scripts/ac.sh on
bash scripts/ac.sh off
```

## 🧮 Two Ways to Get IR Codes

### Way 1: Learn (try this first)

Point your physical remote at RM4, press buttons. Works for any brand.

```bash
python3 scripts/ac_control.py learn power_on   # Press ON button
python3 scripts/ac_control.py learn power_off  # Press OFF button
```

**Limitation**: Some complex signals can't be captured (our TCL AC on-code failed 50+ times).

### Way 2: Calculate (when learning fails)

Look up your AC brand protocol in [IRremoteESP8266](https://github.com/crankyoldgit/IRremoteESP8266), then compute the IR bytes directly.

```
Protocol bytes → IR pulse timing → Broadlink format → Send
```

Example: TCL112AC protocol, turning ON = flip one bit:

```
OFF: 23 CB 26 01 00 20 41 02 05 00 00 00 80 FD
                      ^^-- Power=0 (bit2=0)

ON:  23 CB 26 01 00 24 41 02 05 00 00 00 80 01
                      ^^-- Power=1 (bit2=1), recalc checksum
```

`encode_broadlink()` in `tcl_send.py` converts any protocol bytes to Broadlink format — **this part is universal**, only the protocol bytes differ per brand.

See [SKILL.md](SKILL.md) for full protocol documentation.

## 🔧 How It Works

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   You / AI   │────▶│  bl_send.py  │────▶│  BroadLink   │──── IR ───▶ 🌡️ AC
│  "AC on"     │     │  (UDP+AES)   │     │  RM4 Mini    │──── IR ───▶ 📺 TV
└──────────────┘     └──────────────┘     └──────────────┘──── IR ───▶ 🌀 Fan
```

**Two senders, same result:**

| | `ac_control.py` | `bl_send.py` |
|--|:-:|:-:|
| **Dependencies** | `pip install broadlink` | Only `openssl` CLI |
| **Features** | Discover + Learn + Send | Send only |
| **Best for** | PC / Raspberry Pi | OpenWrt router / embedded |
| **Crypto** | Python cryptodome | openssl CLI (AES-128-CBC) |

## 📦 Requirements

| | Required | Optional |
|--|----------|----------|
| **Runtime** | Python 3.7+ | — |
| **WiFi setup** | `pip install broadlink` | — |
| **IR learning** | `pip install broadlink` | Physical remote |
| **IR sending** | Nothing (bl_send.py) | `broadlink` lib for ac_control.py |
| **Protocol calc** | Nothing | [IRremoteESP8266](https://github.com/crankyoldgit/IRremoteESP8266) reference |

## 🗂️ File Structure

```
├── README.md                     # This file
├── SKILL.md                      # Full tutorial (zero to working)
├── scripts/
│   ├── wifi_setup.py             # WiFi setup (replaces official app)
│   ├── discover.py               # Device discovery
│   ├── ac_control.py             # Learn + Send (needs broadlink lib)
│   ├── bl_send.py                # Zero-dep sender (openssl only)
│   ├── ac.sh                     # SSH remote entry point
│   ├── tcl_send.py               # TCL IR code generator
│   └── tcl_ir_analysis.py        # TCL112AC protocol analysis (529 lines)
└── data/
    └── ir_codes.json             # IR code storage
```

## 📖 Story

We built this to control a TCL AC remotely. The RM4 learned the OFF code in one try, but the ON code failed 50+ times — the signal was too complex for the RM4 to capture.

So we reverse-engineered the TCL112AC protocol from [IRremoteESP8266](https://github.com/crankyoldgit/IRremoteESP8266) source code, found that Power lives at **Frame2 byte5 bit2**, flipped one bit, recalculated the checksum — and it worked.

Then we needed to run it on an OpenWrt router that couldn't install Python crypto libraries. So we wrote `bl_send.py` — a zero-dependency sender that uses `openssl` CLI for AES encryption.

**Learn what you can. Calculate what you can't.**

## 📄 License

[MIT](LICENSE)

---

<div align="center">

*Built for AI agents. Used by [OpenClaw](https://github.com/openclaw/openclaw) 🦞*

**[GitHub](https://github.com/ythx-101/broadlink-remote)** · **[Issues](https://github.com/ythx-101/broadlink-remote/issues)** · **[OpenClaw Q&A](https://github.com/ythx-101/openclaw-qa)**

</div>
