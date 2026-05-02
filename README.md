# Desk Clock

ESP32-C3 SuperMini + MicroPython 桌面时钟，GC9A01 240x240 TFT LCD 显示时间、日期和天气。

## 功能

- NTP 网络对时（UTC+8）
- 心知天气实时显示（温度 + 天气图标 + 描述）
- 华三校园网 Portal 自动认证
- 防死锁安全启动（按住 BOOT 键上电进入 REPL）

## 硬件

| 功能 | GPIO |
|------|------|
| SPI SCK | 4 |
| SPI MOSI | 0 |
| TFT DC | 2 |
| TFT CS | 3 |
| TFT RESET | 1 |
| TFT BL | 11 |
| BOOT 按钮 | 9 |

SPI: `SPI(1)`, 40MHz. 设备: COM8.

## 项目结构

```
desk_clock/
  esp32_image/             ← 设备文件系统镜像
    main.py                ← 主程序
    common/net_weather.py  ← 网络模块
    fonts/                 ← 字体
    icons/                 ← 天气图标 (.bin)
  assets/weather_icons/    ← 图标 XBM 源文件
  tools/xbm2bin.py         ← 图标构建工具
  firmware/                ← MicroPython 固件
  test/                    ← 调试脚本
```

## 快速开始

1. **刷入固件**（仅首次）
   ```
   esptool.py --chip esp32c3 --port COM8 write_flash 0x0 firmware/firmware_4MiB.bin
   ```

2. **构建天气图标**
   ```
   python tools/xbm2bin.py
   ```

3. **配置 WiFi 和 API**
   编辑 `esp32_image/main.py` 修改 `WIFI_SSID`、`API_KEY`、`CITY`

4. **推送全部文件到 ESP32**
   ```
   mpremote connect COM8 cp -r esp32_image/* :
   ```

5. **软复位**
   ```
   mpremote connect COM8 soft-reset
   ```

## 版本

| 标签 | 说明 |
|------|------|
| v5.0 | 天气布局重构，修复时间频闪 |
| v4.0 | 精简 CLAUDE.md，公共规范抽到父目录 |
| v3.0 | 卡片式时间显示 + 天气描述 |
| v2.0 | ESP32 运行文件归入 esp32_image/ |
| v1.0 | 项目初始化 |
