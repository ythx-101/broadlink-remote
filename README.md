# broadlink-remote 🦞

用 BroadLink RM4 Mini 通过红外控制空调、电视、风扇等任何红外设备。

**不需要官方 APP**，全程脚本搞定。

## 特性

- 🔌 **免 APP 配网** — 一行 Python 命令把 RM4 连上你家 WiFi
- 📡 **红外学习** — 对着设备按遥控器，录制信号
- 🧮 **协议计算** — 学不到的码，查协议直接算出来（附 TCL 空调完整示例）
- 🪶 **零依赖发送器** — `bl_send.py` 只需 `openssl`，跑在路由器上也行
- 🦞 **OpenClaw 集成** — 说句话控制空调

## 快速开始

```bash
pip install broadlink
```

### 1. 配网

长按 RM4 Reset 按钮 → 电脑连上 `BroadLink_xxx` 热点 → 运行：

```bash
python3 scripts/wifi_setup.py --ssid "你家WiFi" --password "密码"
```

### 2. 发现设备

```bash
python3 scripts/discover.py
```

### 3. 学习红外码

```bash
python3 scripts/ac_control.py learn power_on   # 对着 RM4 按遥控器
python3 scripts/ac_control.py learn power_off
```

### 4. 控制设备

```bash
python3 scripts/ac_control.py ac on
python3 scripts/ac_control.py ac off
python3 scripts/ac_control.py ac temp 26
```

## 学不到的码怎么办？

有些复杂红外信号 RM4 学不到（比如我们的 TCL 空调开机码试了 50 多次都截不全）。

解决方案：**查协议，算出来。**

1. 去 [IRremoteESP8266](https://github.com/crankyoldgit/IRremoteESP8266) 查你的空调品牌协议
2. 参考 `scripts/tcl_ir_analysis.py`（TCL 完整协议分析）
3. 用 `scripts/tcl_send.py` 里的 `encode_broadlink()` 转成 Broadlink 格式

详见 [SKILL.md](SKILL.md)。

## 文件结构

```
├── SKILL.md                    # 完整文档（从零到能用的教程）
├── scripts/
│   ├── wifi_setup.py           # WiFi 配网（替代官方 APP）
│   ├── discover.py             # 发现设备
│   ├── ac_control.py           # 学习 + 发送（需 broadlink 库）
│   ├── bl_send.py              # 零依赖发送器（只需 openssl）
│   ├── ac.sh                   # SSH 远程调用入口
│   ├── tcl_send.py             # TCL 红外码生成器
│   └── tcl_ir_analysis.py      # TCL112AC 协议分析（529 行）
└── data/
    └── ir_codes.json           # 红外码存储
```

## 硬件

- **BroadLink RM4 Mini** — ~60 块，淘宝/京东
- 任何能跑 Python 且与 RM4 同局域网的设备

## License

MIT
