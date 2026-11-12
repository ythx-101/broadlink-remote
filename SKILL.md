# BroadLink Remote — 红外万能遥控 skill

English: see README.md

用 BroadLink RM4 Mini 通过红外控制空调、电视、风扇等任何红外设备。

**不需要官方 APP**，全程脚本搞定。

## 你需要什么

- **BroadLink RM4 Mini**（淘宝/京东可购）
- 一台能跑 Python 的电脑（配网用，只需一次）
- 你家的 WiFi 名称和密码

## 从零开始：完整流程

### Step 1：配网（让 RM4 连上你家 WiFi）

```bash
pip install broadlink
```

1. **长按 RM4 背面 Reset 按钮 5-10 秒**，指示灯开始快闪
2. **电脑 WiFi 连接 RM4 发出的热点**（名称类似 `BroadLink_xxx`）
3. 运行配网脚本：

```bash
python3 scripts/wifi_setup.py --ssid "你家WiFi名" --password "你家WiFi密码"
```

4. 等 10-20 秒，RM4 指示灯变常亮 = 成功
5. 电脑 WiFi 切回你家路由器

### Step 2：发现设备

```bash
python3 scripts/discover.py
```

输出设备 IP 和 MAC，记下来。

### Step 3：获取红外码

两种方式，**能学就学，学不到就算**。

#### 方式 A：遥控器学习（推荐先试）

对着 RM4 按遥控器按钮，设备录制红外信号：

```bash
python3 scripts/ac_control.py learn power_on   # 按遥控器开机键
python3 scripts/ac_control.py learn power_off  # 按关机键
python3 scripts/ac_control.py learn temp_26    # 按 26 度
```

学到的码自动存进 `data/ir_codes.json`。

> **注意**：有些复杂信号 RM4 学不到（我们的 TCL 空调开机码试了 50 多次都截不全）。这时候用方式 B。

#### 方式 B：协议计算（学不到时用）

根据空调品牌的红外协议，直接**算出**红外码，不需要遥控器。

1. 去 [IRremoteESP8266](https://github.com/crankyoldgit/IRremoteESP8266) 查你的空调品牌协议（`src/ir_Xxx.h`）
2. 参考 `scripts/tcl_ir_analysis.py`（TCL 空调的完整协议分析），写你品牌的构造逻辑
3. 用 `scripts/tcl_send.py` 里的 `encode_broadlink()` 转成 Broadlink 格式

编码链路：
```
协议字节 → IR 脉冲时序 → Broadlink 格式 → 写入 ir_codes.json
```

> `encode_broadlink()` 是通用的，任何品牌都能用。只有协议字节部分因品牌而异。

### Step 4：发送红外码

```bash
# 需要 broadlink 库（功能全）
python3 scripts/ac_control.py ac on
python3 scripts/ac_control.py ac off
python3 scripts/ac_control.py ac temp 26

# 或用零依赖版本（只需 openssl，适合路由器/嵌入式）
python3 scripts/bl_send.py power_on
python3 scripts/bl_send.py power_off
```

### Step 5：接入 OpenClaw（可选）

配置 SSH 地址后，通过 `ac.sh` 远程控制：

```bash
export BL_ROUTER_IP="你的路由器IP"
export BL_ROUTER_USER="root"
bash scripts/ac.sh on
bash scripts/ac.sh off
```

接入 OpenClaw 后，说句话就能控制空调。

## 文件说明

| 文件 | 说明 |
|------|------|
| `scripts/wifi_setup.py` | WiFi 配网（替代官方 APP） |
| `scripts/discover.py` | 发现局域网内的 BroadLink 设备 |
| `scripts/ac_control.py` | 完整控制脚本（学习 + 发送，需 `broadlink` 库） |
| `scripts/bl_send.py` | 零依赖发送器（用 `openssl` CLI 做加密，适合路由器） |
| `scripts/tcl_send.py` | TCL 协议红外码生成器（字节 → 脉冲 → Broadlink 格式） |
| `scripts/tcl_ir_analysis.py` | TCL112AC 完整协议分析 |
| `scripts/ac.sh` | SSH 远程调用入口 |
| `data/ir_codes.json` | 红外码存储 |

## 两种发送器对比

| | `ac_control.py` | `bl_send.py` |
|---|---|---|
| 依赖 | `pip install broadlink` | 只需 `openssl` 命令 |
| 功能 | 发现 + 学习 + 发送 | 仅发送 |
| 适合 | 电脑/树莓派 | OpenWrt 路由器/嵌入式 |
| 加密 | Python crypto | openssl CLI |

## 协议计算原理（以 TCL 为例）

TCL112AC 协议，每条指令 = 14 字节 × 2 帧：

```
帧结构：
  Frame1 (Special): 预信号，Quiet 切换用
  Frame2 (Normal):  真正的控制帧

Frame2 字节定义：
  byte 0-2:  Header [0x23, 0xCB, 0x26]
  byte 3:    MsgType (0x01=Normal)
  byte 5:    bit2=Power, bit5=Quiet, bit6=Light
  byte 6:    bits[3:0]=Mode (1=Heat, 3=Cool, 8=Auto)
  byte 7:    bits[3:0]=Temp (31 - 温度)
  byte 8:    bits[2:0]=Fan (0=Auto, 5=High)
  byte 13:   Checksum = sum(bytes[0:13]) & 0xFF
```

关机码 → 开机码，只需翻一个 bit：
```
byte5: 0x20 → 0x24  (bit2: 0→1, Power OFF→ON)
byte13: 重算校验和
```

## 故障排除

| 问题 | 解决 |
|------|------|
| 配网失败 | 确认电脑已连 BroadLink 热点，指示灯在快闪 |
| discover 找不到设备 | 确认 RM4 和电脑在同一局域网 |
| 学习超时 | 遥控器对准 RM4，距离 < 30cm |
| 学不到某些码 | 用协议计算方式（方式 B） |
| 发送无反应 | 检查 RM4 是否被 APP 锁定 → 长按 Reset 重置 |
| 路由器上缺 crypto | 用 `bl_send.py`，只需 openssl |

## 踩坑记录

> 这些是我们实际开发中的经验，可能帮你少走弯路。

1. RM4 学习开机码 → 50+ 次失败（TCL 空调信号太长，RM4 截不全）
2. 盲改 Frame1 的各种 bit → 全部无效（**Frame1 是预信号，不是控制帧**）
3. 用 Claude Opus 翻 IRremoteESP8266 源码 → 找到 TCL112AC 协议，定位 Power 在 **Frame2 byte5 bit2**
4. 翻一个 bit（`0x20 → 0x24`），重算校验和 → 一次成功
5. 路由器上装不了 broadlink 库的 crypto 依赖 → 写了 `bl_send.py` 用 openssl CLI 替代

**能学就学，学不到就查协议算。**
