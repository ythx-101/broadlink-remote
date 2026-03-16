#!/usr/bin/env python3
"""
TCL112AC IR Protocol Analysis & Power-ON Code Generator
Based on IRremoteESP8266 library's TCL112AC protocol definition.
"""

# === Protocol Definition (from ir_Tcl.h) ===
# Byte 0-2: Header [0x23, 0xCB, 0x26]
# Byte 3:  bits[1:0] = MsgType (0b01=Normal, 0b10=Special)
# Byte 4:  (unused/reserved)
# Byte 5:  bit2=Power, bit3=OffTimerEnabled, bit4=OnTimerEnabled,
#          bit5=Quiet, bit6=Light, bit7=Econo
# Byte 6:  bits[3:0]=Mode, bit4=Health, bit5=Turbo
# Byte 7:  bits[3:0]=Temp (31-temp), bits[7:4]=reserved
# Byte 8:  bits[2:0]=Fan, bits[5:3]=SwingV, bit6=TimerIndicator
# Byte 9:  bits[6:1]=OffTimer
# Byte 10: bits[6:1]=OnTimer
# Byte 11: 0x00
# Byte 12: bit3=SwingH, bit5=HalfDegree, bit7=isTcl
# Byte 13: Checksum

# Mode constants
MODE_HEAT = 1
MODE_DRY  = 2
MODE_COOL = 3
MODE_FAN  = 7
MODE_AUTO = 8

# Fan constants
FAN_AUTO = 0b000
FAN_MIN  = 0b001
FAN_LOW  = 0b010
FAN_MED  = 0b011
FAN_HIGH = 0b101

# SwingV constants
SWINGV_OFF     = 0b000
SWINGV_HIGHEST = 0b001
SWINGV_HIGH    = 0b010
SWINGV_MIDDLE  = 0b011
SWINGV_LOW     = 0b100
SWINGV_LOWEST  = 0b101
SWINGV_ON      = 0b111

# MsgType constants
MSG_NORMAL  = 0b01  # 0x01
MSG_SPECIAL = 0b10  # 0x02

def calc_checksum(state):
    """Calculate checksum per TCL112AC rules"""
    if len(state) < 14:
        return 0
    if state[3] == 0x02:  # Special message
        return sum(state[:13]) + 0xF & 0xFF  # sumBytes with offset 0xF
    else:
        return sum(state[:13]) & 0xFF

def calc_checksum_alt(state):
    """Alternative: the offset 0xF is added once, not per-byte"""
    if state[3] == 0x02:
        return (sum(state[:13]) + 0xF) & 0xFF
    else:
        return sum(state[:13]) & 0xFF

def verify_known_codes():
    """Verify our understanding against known codes"""
    print("=" * 60)
    print("VERIFYING KNOWN CODES")
    print("=" * 60)
    
    # Example codes from a specific TCL112AC unit (your codes will differ).
    # Replace these with your own learned/calculated values.
    # Known OFF code
    frame1 = [0x23, 0xCB, 0x26, 0x02, 0x00, 0x40, 0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x25]
    frame2 = [0x23, 0xCB, 0x26, 0x01, 0x00, 0x20, 0x41, 0x02, 0x05, 0x00, 0x00, 0x00, 0x80, 0xFD]
    
    print("\n--- Frame1 (OFF - Special message) ---")
    s1 = sum(frame1[:13])
    print(f"  Raw bytes: {' '.join(f'{b:02X}' for b in frame1)}")
    print(f"  Sum of bytes 0-12: 0x{s1:04X} ({s1})")
    print(f"  (sum + 0xF) & 0xFF = 0x{(s1 + 0xF) & 0xFF:02X}")
    print(f"  Actual checksum: 0x{frame1[13]:02X}")
    print(f"  User formula (0x3B - sum) & 0xFF = 0x{(0x3B - s1) & 0xFF:02X}")
    # Note: 0x3B - sum = -(sum - 0x3B) = -(sum) + 0x3B
    # Equivalent to (0x3B - sum) & 0xFF vs (sum + 0xF) & 0xFF
    # If sum = 0x216: (0x3B - 0x216) & 0xFF = (0x3B - 0x16) & 0xFF = 0x25
    # (0x216 + 0xF) & 0xFF = (0x225) & 0xFF = 0x25
    # 0x3B - x == x + 0xF (mod 256) => 0x3B = 2x + 0xF => 2x = 0x2C => x = 0x16 
    # This works specifically for this sum! Let's verify more carefully.
    # Actually: -(sum) + 0x3B ≡ sum + 0xF (mod 256)?
    # -sum + 0x3B ≡ sum + 0xF => -2*sum ≡ 0xF - 0x3B = -0x2C => 2*sum ≡ 0x2C => sum ≡ 0x16
    # This only works when sum ≡ 0x16 mod 128. So the user's formula is a coincidence!
    # The real formula is (sum + 0xF) & 0xFF for Special messages.
    
    print(f"\n  Byte 3 = 0x{frame1[3]:02X} -> MsgType = {frame1[3] & 0x03} (Special={MSG_SPECIAL})")
    print(f"  Byte 5 = 0x{frame1[5]:02X} = {frame1[5]:08b}")
    print(f"    Power = {(frame1[5] >> 2) & 1}")
    print(f"    Quiet = {(frame1[5] >> 5) & 1}")
    print(f"    Light = {(frame1[5] >> 6) & 1} (inverted: Light ON when bit=0)")
    print(f"    Econo = {(frame1[5] >> 7) & 1}")
    print(f"  Byte 6 = 0x{frame1[6]:02X} = {frame1[6]:08b}")
    print(f"    Mode  = {frame1[6] & 0x0F}")
    print(f"    Health = {(frame1[6] >> 4) & 1}")
    print(f"    Turbo  = {(frame1[6] >> 5) & 1}")
    
    print("\n--- Frame2 (OFF - Normal message) ---")
    s2 = sum(frame2[:13])
    print(f"  Raw bytes: {' '.join(f'{b:02X}' for b in frame2)}")
    print(f"  Sum of bytes 0-12: 0x{s2:04X} ({s2})")
    print(f"  sum & 0xFF = 0x{s2 & 0xFF:02X}")
    print(f"  Actual checksum: 0x{frame2[13]:02X}")
    print(f"  Match: {(s2 & 0xFF) == frame2[13]}")
    
    print(f"\n  Byte 3 = 0x{frame2[3]:02X} -> MsgType = {frame2[3] & 0x03} (Normal={MSG_NORMAL})")
    print(f"  Byte 5 = 0x{frame2[5]:02X} = {frame2[5]:08b}")
    print(f"    Power = {(frame2[5] >> 2) & 1}")
    print(f"    OffTimerEn = {(frame2[5] >> 3) & 1}")
    print(f"    OnTimerEn = {(frame2[5] >> 4) & 1}")
    print(f"    Quiet = {(frame2[5] >> 5) & 1}")
    print(f"    Light = {(frame2[5] >> 6) & 1} (inverted: ON=0)")
    print(f"    Econo = {(frame2[5] >> 7) & 1}")
    print(f"  Byte 6 = 0x{frame2[6]:02X} = {frame2[6]:08b}")
    print(f"    Mode  = {frame2[6] & 0x0F} (1=Heat)")
    print(f"    Health = {(frame2[6] >> 4) & 1}")
    print(f"    Turbo  = {(frame2[6] >> 5) & 1}")
    print(f"  Byte 7 = 0x{frame2[7]:02X} = {frame2[7]:08b}")
    temp_raw = frame2[7] & 0x0F
    temp = 31 - temp_raw
    print(f"    Temp raw = {temp_raw} -> Temp = 31 - {temp_raw} = {temp} C")
    print(f"  Byte 8 = 0x{frame2[8]:02X} = {frame2[8]:08b}")
    fan = frame2[8] & 0x07
    swingv = (frame2[8] >> 3) & 0x07
    timer_ind = (frame2[8] >> 6) & 1
    print(f"    Fan = {fan} (5=High)")
    print(f"    SwingV = {swingv}")
    print(f"    TimerIndicator = {timer_ind}")
    print(f"  Byte 12 = 0x{frame2[12]:02X} = {frame2[12]:08b}")
    print(f"    SwingH = {(frame2[12] >> 3) & 1}")
    print(f"    HalfDegree = {(frame2[12] >> 5) & 1}")
    print(f"    isTcl = {(frame2[12] >> 7) & 1}")

    # Known good state from IRremoteESP8266: On, Cool, 24C
    reset_state = [0x23, 0xCB, 0x26, 0x01, 0x00, 0x24, 0x03, 0x07, 0x40, 0x00, 0x00, 0x00, 0x00, 0x03]
    print("\n--- IRremoteESP8266 Reset State (ON, Cool, 24C) ---")
    sr = sum(reset_state[:13])
    print(f"  Raw bytes: {' '.join(f'{b:02X}' for b in reset_state)}")
    print(f"  sum & 0xFF = 0x{sr & 0xFF:02X}, Actual: 0x{reset_state[13]:02X}, Match: {(sr & 0xFF) == reset_state[13]}")
    print(f"  Byte 3 = 0x{reset_state[3]:02X} (MsgType = Normal)")
    print(f"  Byte 5 = 0x{reset_state[5]:02X} = {reset_state[5]:08b}")
    print(f"    Power = {(reset_state[5] >> 2) & 1} (ON!)")
    print(f"  Byte 6 = 0x{reset_state[6]:02X} -> Mode = {reset_state[6] & 0x0F} (3=Cool)")
    print(f"  Byte 7 = 0x{reset_state[7]:02X} -> Temp = 31 - {reset_state[7] & 0x0F} = {31 - (reset_state[7] & 0x0F)} C")
    print(f"  Byte 8 = 0x{reset_state[8]:02X} -> Fan = {reset_state[8] & 0x07}, SwingV = {(reset_state[8]>>3) & 0x07}")
    print(f"  Byte 12 = 0x00 -> isTcl = 0 (GZ055BE1 model)")


def build_frame(power=True, mode=MODE_COOL, temp_c=26, fan=FAN_AUTO,
                swingv=SWINGV_OFF, swingh=False, light=True, econo=False,
                health=False, turbo=False, quiet=False, is_tcl=True,
                msg_type=MSG_NORMAL, half_degree=False,
                on_timer=0, off_timer=0):
    """Build a 14-byte TCL112AC frame"""
    state = [0] * 14
    
    # Header
    state[0] = 0x23
    state[1] = 0xCB
    state[2] = 0x26
    
    # Byte 3: MsgType
    state[3] = msg_type & 0x03
    
    # Byte 4: reserved
    state[4] = 0x00
    
    # Byte 5: Power, timers, quiet, light, econo
    b5 = 0
    if power:
        b5 |= (1 << 2)
    if off_timer > 0:
        b5 |= (1 << 3)
    if on_timer > 0:
        b5 |= (1 << 4)
    if quiet:
        b5 |= (1 << 5)
    if not light:  # Light bit is inverted (cleared when light is ON)
        b5 |= (1 << 6)
    if econo:
        b5 |= (1 << 7)
    state[5] = b5
    
    # Byte 6: Mode, Health, Turbo
    b6 = mode & 0x0F
    if health:
        b6 |= (1 << 4)
    if turbo:
        b6 |= (1 << 5)
    state[6] = b6
    
    # Byte 7: Temperature (31 - temp)
    temp_val = int(31 - temp_c) & 0x0F
    state[7] = temp_val
    
    # Byte 8: Fan, SwingV, TimerIndicator
    b8 = fan & 0x07
    b8 |= (swingv & 0x07) << 3
    if on_timer > 0 or off_timer > 0:
        b8 |= (1 << 6)
    state[8] = b8
    
    # Byte 9: OffTimer
    off_timer_val = min(off_timer, 720) // 20
    state[9] = (off_timer_val & 0x3F) << 1
    
    # Byte 10: OnTimer
    on_timer_val = min(on_timer, 720) // 20
    state[10] = (on_timer_val & 0x3F) << 1
    
    # Byte 11: 0x00
    state[11] = 0x00
    
    # Byte 12: SwingH, HalfDegree, isTcl
    b12 = 0
    if swingh:
        b12 |= (1 << 3)
    if half_degree:
        b12 |= (1 << 5)
    if is_tcl:
        b12 |= (1 << 7)
    state[12] = b12
    
    # Byte 13: Checksum
    if state[3] == 0x02:  # Special message
        state[13] = (sum(state[:13]) + 0xF) & 0xFF
    else:
        state[13] = sum(state[:13]) & 0xFF
    
    return state


def format_frame(frame):
    return ' '.join(f'{b:02X}' for b in frame)


def analyze_experiments():
    """Analyze the user's experimental results"""
    print("\n" + "=" * 60)
    print("ANALYZING EXPERIMENTAL RESULTS")
    print("=" * 60)
    
    # User's OFF code Frame1 is a "Special" message (MsgType=0x02)
    # This is used for quiet mode toggling in the IRremoteESP8266 library!
    # Frame2 is the "Normal" message that contains the actual AC state.
    
    print("""
KEY PROTOCOL INSIGHT:
  Frame1 (MsgType=0x02, Special) is sent BEFORE the main command
  to handle quiet/mute state changes. It's a "pre-signal".
  
  Frame2 (MsgType=0x01, Normal) is the ACTUAL command containing
  power state, mode, temperature, fan speed, etc.

YOUR OFF CODE DECODED:
  Frame1: Special message with Quiet off, Light ON (bit6=1 means light OFF!)
    - Actually byte5=0x40 means Light bit=1, so Light is OFF in this frame
    - byte6=0xC0 = mode=0 (undefined), turbo=1, health=1 ... weird for a pre-frame
    - This frame format for Special messages may differ from Normal messages
    
  Frame2: Normal message - THE MAIN COMMAND
    - Power = OFF (bit2 of byte5 = 0, since 0x20 = 0b00100000)
    - Wait... 0x20 = 0b00100000, bit2 = 0, so Power IS off
    - bit5 = 1 -> Quiet = ON
    - Mode = 1 (Heat?!) or mode stored differently
    - Temp = 31 - 2 = 29C
    - Fan = 5 (High)
    - SwingV = 0 (Off)
    - isTcl = 1 (byte12 bit7 = 1, 0x80)
""")
    
    print("EXPERIMENT ANALYSIS:")
    print("-" * 40)
    
    # byte5 0x40->0x60 beeped
    # 0x40 = 01000000, 0x60 = 01100000
    # Difference: bit5 flipped (Quiet bit in the Special frame)
    print("1. byte5 0x40->0x60 (in Frame1, Special): flipped bit5 (Quiet)")
    print("   -> AC recognized it as valid quiet toggle command")
    
    # byte3=0x01 + byte5=0x20 beeped
    # Changed Frame1 from Special(0x02) to Normal(0x01), byte5=0x20
    # 0x20 = 00100000, bit5=Quiet=1
    # As Normal message: Power=0, Quiet=1
    print("2. byte3=0x01 + byte5=0x20 (Frame1 becomes Normal): ")
    print("   -> Sent as Normal message with Power=0, Quiet=1")
    print("   -> AC recognized valid Normal message format!")
    
    # byte5=0x20 + byte6=0x00 beeped  
    print("3. byte5=0x20 + byte6=0x00 (in Frame1?): Quiet change")
    print("   -> Another valid configuration detected by AC")
    
    print("""
WHY BEEP BUT NO POWER ON:
  The experiments that beeped were recognized as valid commands,
  but they didn't include Power=ON (bit2 of byte5).
  
  To POWER ON, we need Frame2 with:
  - byte3 = 0x01 (Normal message type)
  - byte5 bit2 = 1 (Power ON)
  - Plus valid mode/temp/fan parameters
""")


def generate_power_on_codes():
    """Generate power-on codes, sorted by priority"""
    print("\n" + "=" * 60)
    print("GENERATING POWER-ON CODES (26C, Cool, Auto Fan)")
    print("=" * 60)
    
    # The library sends:
    # 1. First a Special frame (for quiet toggle), then
    # 2. A Normal frame (actual command)
    # 
    # For our case, we need to figure out what Frame1 (Special) should look like
    # for a power-on command. Looking at the library code:
    #   quiet_off = {0x23, 0xCB, 0x26, 0x02, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x65}
    # This is the "quiet off" special frame. Checksum: sum(0..12) + 0xF
    # sum = 0x23+0xCB+0x26+0x02+0x00+0x40+0+0+0+0+0+0+0 = 0x156
    # (0x156 + 0xF) & 0xFF = 0x165 & 0xFF = 0x65 ✓
    
    candidates = []
    
    # --- Candidate 1: Direct from IRremoteESP8266 reset state (ON, Cool, 24C) adapted to 26C ---
    # Reset: 0x23, 0xCB, 0x26, 0x01, 0x00, 0x24, 0x03, 0x07, 0x40, 0x00, 0x00, 0x00, 0x00, 0x03
    # For 26C: Temp = 31-26 = 5, so byte7 = 0x05
    frame2 = build_frame(power=True, mode=MODE_COOL, temp_c=26, fan=FAN_AUTO,
                         swingv=SWINGV_ON, is_tcl=False, light=True)
    # Use the known quiet_off as Frame1
    frame1 = [0x23, 0xCB, 0x26, 0x02, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x65]
    candidates.append(("Library quiet_off + ON/Cool/26C/AutoFan/SwingOn (GZ055BE1 model)", frame1, frame2))
    
    # --- Candidate 2: Same but with isTcl=True (TAC09CHSD model) ---
    frame2 = build_frame(power=True, mode=MODE_COOL, temp_c=26, fan=FAN_AUTO,
                         swingv=SWINGV_ON, is_tcl=True, light=True)
    candidates.append(("Library quiet_off + ON/Cool/26C/AutoFan/SwingOn (TCL model, isTcl=1)", frame1, frame2))
    
    # --- Candidate 3: No swing, isTcl=True ---
    frame2 = build_frame(power=True, mode=MODE_COOL, temp_c=26, fan=FAN_AUTO,
                         swingv=SWINGV_OFF, is_tcl=True, light=True)
    candidates.append(("Library quiet_off + ON/Cool/26C/AutoFan/NoSwing (TCL model)", frame1, frame2))
    
    # --- Candidate 4: Use user's original Frame1 as-is, only change Frame2 ---
    frame1_orig = [0x23, 0xCB, 0x26, 0x02, 0x00, 0x40, 0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x25]
    frame2 = build_frame(power=True, mode=MODE_COOL, temp_c=26, fan=FAN_AUTO,
                         swingv=SWINGV_OFF, is_tcl=True, light=True)
    candidates.append(("Original Frame1 + ON/Cool/26C/AutoFan (TCL model)", frame1_orig, frame2))
    
    # --- Candidate 5: Same as 4 but GZ055BE1 model ---
    frame2 = build_frame(power=True, mode=MODE_COOL, temp_c=26, fan=FAN_AUTO,
                         swingv=SWINGV_OFF, is_tcl=False, light=True)
    candidates.append(("Original Frame1 + ON/Cool/26C/AutoFan (GZ055BE1 model)", frame1_orig, frame2))
    
    # --- Candidate 6: SwingV=ON, FanHigh, isTcl ---
    frame2 = build_frame(power=True, mode=MODE_COOL, temp_c=26, fan=FAN_HIGH,
                         swingv=SWINGV_ON, is_tcl=True, light=True)
    candidates.append(("Library quiet_off + ON/Cool/26C/HighFan/SwingOn (TCL)", frame1, frame2))
    
    # --- Candidate 7: Auto mode instead of Cool ---
    frame2 = build_frame(power=True, mode=MODE_AUTO, temp_c=26, fan=FAN_AUTO,
                         swingv=SWINGV_OFF, is_tcl=True, light=True)
    candidates.append(("Library quiet_off + ON/Auto/26C/AutoFan (TCL)", frame1, frame2))
    
    # --- Candidate 8: Mimic the OFF frame2 structure but with Power ON ---
    # OFF Frame2: 23 CB 26 01 00 20 41 02 05 00 00 00 80 FD
    # byte5: 0x20 -> 0x24 (set power bit2)
    # Keep everything else the same as OFF
    frame2_mimic = [0x23, 0xCB, 0x26, 0x01, 0x00, 0x24, 0x41, 0x02, 0x05, 0x00, 0x00, 0x00, 0x80, 0x00]
    frame2_mimic[13] = sum(frame2_mimic[:13]) & 0xFF
    candidates.append(("Original Frame1 + OFF-frame with Power bit ON (minimal change)", frame1_orig, frame2_mimic))
    
    # --- Candidate 9: Exact same as OFF but set power bit in Frame2 + cool mode ---
    frame2_cool = [0x23, 0xCB, 0x26, 0x01, 0x00, 0x24, 0x03, 0x05, 0x00, 0x00, 0x00, 0x00, 0x80, 0x00]
    frame2_cool[13] = sum(frame2_cool[:13]) & 0xFF
    candidates.append(("Original Frame1 + Power ON/Cool/26C/AutoFan/isTcl (simple)", frame1_orig, frame2_cool))
    
    # --- Candidate 10: No Frame1 at all, just Frame2 (single frame) ---
    frame2 = build_frame(power=True, mode=MODE_COOL, temp_c=26, fan=FAN_AUTO,
                         swingv=SWINGV_OFF, is_tcl=True, light=True)
    candidates.append(("Single frame only: ON/Cool/26C/AutoFan (TCL)", None, frame2))
    
    for i, (desc, f1, f2) in enumerate(candidates, 1):
        print(f"\n{'='*50}")
        print(f"  Candidate #{i}: {desc}")
        print(f"{'='*50}")
        if f1:
            s1 = sum(f1[:13])
            chk1_expected = (s1 + 0xF) & 0xFF if f1[3] == 0x02 else s1 & 0xFF
            print(f"  Frame1: {format_frame(f1)}")
            print(f"    Checksum valid: {f1[13] == chk1_expected}")
        else:
            print(f"  Frame1: (none - single frame mode)")
        s2 = sum(f2[:13])
        chk2_expected = (s2 + 0xF) & 0xFF if f2[3] == 0x02 else s2 & 0xFF
        print(f"  Frame2: {format_frame(f2)}")
        print(f"    Checksum valid: {f2[13] == chk2_expected}")
        print(f"    Decoded: Power={'ON' if (f2[5]>>2)&1 else 'OFF'}, ", end="")
        mode_val = f2[6] & 0x0F
        mode_names = {1:'Heat', 2:'Dry', 3:'Cool', 7:'Fan', 8:'Auto'}
        print(f"Mode={mode_names.get(mode_val, f'?{mode_val}')}, ", end="")
        print(f"Temp={31 - (f2[7] & 0x0F)}C, ", end="")
        fan_val = f2[8] & 0x07
        fan_names = {0:'Auto', 1:'Min', 2:'Low', 3:'Med', 5:'High'}
        print(f"Fan={fan_names.get(fan_val, f'?{fan_val}')}, ", end="")
        sv = (f2[8]>>3)&0x07
        print(f"SwingV={sv}, ", end="")
        print(f"isTcl={(f2[12]>>7)&1}")


def explain_your_off_code():
    """Deep decode of the user's OFF code"""
    print("\n" + "=" * 60)
    print("DEEP DECODE: YOUR OFF CODE")
    print("=" * 60)
    
    frame2 = [0x23, 0xCB, 0x26, 0x01, 0x00, 0x20, 0x41, 0x02, 0x05, 0x00, 0x00, 0x00, 0x80, 0xFD]
    
    b5 = frame2[5]  # 0x20 = 0b00100000
    b6 = frame2[6]  # 0x41 = 0b01000001
    b7 = frame2[7]  # 0x02
    b8 = frame2[8]  # 0x05
    b12 = frame2[12] # 0x80
    
    print(f"""
Frame2 (Normal / Main Command) Decode:
  byte3  = 0x01 -> MsgType = Normal (0b01)
  byte5  = 0x{b5:02X} = {b5:08b}
    bit2 (Power)         = {(b5>>2)&1} -> OFF
    bit3 (OffTimerEn)    = {(b5>>3)&1} -> Disabled
    bit4 (OnTimerEn)     = {(b5>>4)&1} -> Disabled
    bit5 (Quiet)         = {(b5>>5)&1} -> ON (quiet mode was active!)
    bit6 (Light)         = {(b5>>6)&1} -> Light OFF (inverted logic)
    bit7 (Econo)         = {(b5>>7)&1} -> OFF
  byte6  = 0x{b6:02X} = {b6:08b}
    bits[3:0] (Mode)     = {b6&0x0F} -> Heat (1)
    bit4 (Health)        = {(b6>>4)&1} -> OFF
    bit5 (Turbo)         = {(b6>>5)&1} -> OFF
    bit6 (?)             = {(b6>>6)&1} -> SET (1) -- NOTE: upper bits of byte6                                         
  byte7  = 0x{b7:02X} = {b7:08b}
    bits[3:0] (Temp)     = {b7&0x0F} -> 31 - {b7&0x0F} = {31-(b7&0x0F)} C
  byte8  = 0x{b8:02X} = {b8:08b}
    bits[2:0] (Fan)      = {b8&0x07} -> High (5)
    bits[5:3] (SwingV)   = {(b8>>3)&0x07} -> Off (0)
    bit6 (TimerInd)      = {(b8>>6)&1} -> No timer
  byte12 = 0x{b12:02X} = {b12:08b}
    bit3 (SwingH)        = {(b12>>3)&1} -> OFF
    bit5 (HalfDegree)    = {(b12>>5)&1} -> No
    bit7 (isTcl)         = {(b12>>7)&1} -> YES (TCL brand)

SUMMARY: OFF command, last state was Heat/29C/HighFan/Quiet/LightOff/TCL
Note: byte6 bit6 = 1 (0x41 vs 0x01), this bit is "reserved" in the 
library but may be meaningful for your specific model.
""")

    # Now look at Frame1
    frame1 = [0x23, 0xCB, 0x26, 0x02, 0x00, 0x40, 0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x25]
    b5 = frame1[5]  # 0x40
    b6 = frame1[6]  # 0xC0
    
    print(f"""Frame1 (Special / Pre-signal) Decode:
  byte3  = 0x02 -> MsgType = Special (0b10)
  byte5  = 0x{b5:02X} = {b5:08b}
    In Special messages, byte5 layout may differ.
    bit6 = 1 -> Light=OFF or Quiet-related flag
  byte6  = 0x{b6:02X} = {b6:08b}
    bits[3:0] = 0 (no mode in special frames?)
    bit6 = 1, bit7 = 1 -> Upper flags set
  
  Compare with library's quiet_off frame:
    Library:  23 CB 26 02 00 40 00 00 00 00 00 00 00 65
    Yours:    23 CB 26 02 00 40 C0 00 00 00 00 00 00 25
    Diff: byte6 (0x00 vs 0xC0), causing different checksum
    
  Your Frame1 byte6=0xC0 may encode the last known state's
  mode/health/turbo in the Special frame, or it may be a 
  variant not covered by the library.
""")


def main():
    verify_known_codes()
    explain_your_off_code()
    analyze_experiments()
    generate_power_on_codes()
    
    print("\n" + "=" * 60)
    print("RECOMMENDED TESTING ORDER")
    print("=" * 60)
    print("""
Priority order for testing:

HIGH PRIORITY (most likely to work):
  #8  - Minimal change from your OFF code (just flip power bit)
  #9  - Power ON with Cool mode, keeping your Frame1
  #4  - Your Frame1 + standard ON/Cool/26C (TCL model)
  #3  - Library quiet_off + standard ON/Cool/26C (TCL model, no swing)

MEDIUM PRIORITY:
  #2  - Same as #3 but with SwingV=ON
  #1  - Same as #2 but GZ055BE1 model (isTcl=0)
  #5  - Your Frame1 + standard ON/Cool/26C (GZ055BE1 model)
  #10 - Single frame (no pre-signal)

LOWER PRIORITY:
  #6  - High fan variant
  #7  - Auto mode variant

CRITICAL NOTES:
  1. Your Frame1 has byte6=0xC0 which differs from the library's
     quiet_off (byte6=0x00). If none work, try with byte6=0x00
     in Frame1 (library's exact quiet_off frame).
  
  2. byte6 bit6 in Frame2 (0x41 vs 0x01 in your OFF code) - 
     this unknown bit may need to be set for your model.
     If candidates don't work, try setting bit6 of byte6 in Frame2.
  
  3. The temperature in your OFF code is 29C with Heat mode.
     If the AC remembers its last mode, try Heat/29C first.
""")


if __name__ == "__main__":
    main()
