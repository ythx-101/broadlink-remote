#!/usr/bin/env python3
"""
BroadLink WiFi Setup — 无需官方 APP，纯脚本配网。

使用前：
  1. 长按 RM4 背面 Reset 按钮 5-10 秒，指示灯快闪
  2. 电脑 WiFi 连接 RM4 发出的热点（名称类似 BroadLink_xxx）
  3. 运行本脚本

用法：
  python3 wifi_setup.py --ssid "你的WiFi名" --password "你的WiFi密码"
  python3 wifi_setup.py --ssid "MyWiFi" --password "12345678" --security 4

安全模式：
  0 = 无密码
  1 = WEP
  2 = WPA1
  3 = WPA2
  4 = WPA1/WPA2（默认，大多数家用路由器用这个）
"""

import argparse
import sys

try:
    import broadlink
except ImportError:
    print("❌ 需要安装 broadlink 库：pip install broadlink")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="BroadLink WiFi 配网（无需官方 APP）")
    parser.add_argument("--ssid", required=True, help="你家 WiFi 名称")
    parser.add_argument("--password", required=True, help="WiFi 密码")
    parser.add_argument("--security", type=int, default=4,
                        choices=[0, 1, 2, 3, 4],
                        help="安全模式：0=无密码, 1=WEP, 2=WPA1, 3=WPA2, 4=WPA1/2（默认）")
    args = parser.parse_args()

    print(f"[*] 正在配网...")
    print(f"    SSID: {args.ssid}")
    print(f"    安全模式: {args.security}")
    print()

    try:
        broadlink.setup(args.ssid, args.password, args.security)
        print("✅ 配网指令已发送！")
        print()
        print("接下来：")
        print("  1. 等待 10-20 秒，RM4 指示灯变为常亮")
        print("  2. 把电脑 WiFi 切回你家路由器")
        print("  3. 运行 python3 discover.py 发现设备")
    except Exception as e:
        print(f"❌ 配网失败: {e}")
        print()
        print("排查：")
        print("  - 确认电脑已连上 BroadLink_xxx 热点")
        print("  - 确认 RM4 指示灯在快闪（AP 模式）")
        print("  - WiFi 名称和密码是否正确")
        sys.exit(1)


if __name__ == "__main__":
    main()
