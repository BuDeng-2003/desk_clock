# desk_clock

ESP32-C3 supermini + MicroPython 桌面时钟，GC9A01 240x240 TFT LCD 显示时间、日期和天气。

> 通用嵌入式规范（串口通信、内存管理、Git 提交等）见父目录 `C:\Desktop\embedded\CLAUDE.md`

## 常用命令

```bash
# 构建天气图标（assets/weather_icons/*.xbm → src/icons/*.bin）
python tools/xbm2bin.py

# 推送全部文件到 ESP32
echo "@echo off && for %f in (esp32_image\*) do python -m mpremote connect COM8 cp %f :%~nxf" > tmp.bat && ./tmp.bat

# 推送单个文件
echo "@echo off && python -m mpremote connect COM8 cp esp32_image\main.py :main.py" > tmp.bat && ./tmp.bat

# 软复位
echo "@echo off && python -m mpremote connect COM8 soft-reset" > tmp.bat && ./tmp.bat
```

## 硬件引脚

| 功能 | GPIO |
|------|------|
| SPI SCK | 4 |
| SPI MOSI | 0 |
| TFT DC | 2 |
| TFT CS | 3 |
| TFT RESET | 1 |
| TFT BL | 11 |
| BOOT 按钮 | 9 |

SPI: `SPI(1)`, 40MHz. 设备: COM8, vid:303a pid:1001.

## 文件结构

```
src/             # 设备文件系统镜像（推流 = 此目录 → ESP32 根目录）
  main.py                #   主程序：硬件初始化、主循环、WDT
  common/
    net_weather.py       #   网络：WiFi + Portal认证 + 心知天气API
  fonts/
    vga1_8x16.py         #   8x16 字体 (ASCII 0x20-0x7f)
    vga2_16x32.py        #   16x32 字体 (0-255)
  icons/                 #   天气图标 RGB565 (39个, 0.bin~38.bin)
    *.bin
assets/
  weather_icons/         # 图标 XBM 源文件 (22个)
    *.xbm
tools/
  xbm2bin.py             # 构建: assets/weather_icons/*.xbm → src/icons/*.bin
firmware/
  firmware_4MiB.bin      # MicroPython 固件 (含 gc9a01 驱动)
test/                    # 调试脚本
```

## 架构要点

### 主循环
单调非阻塞轮询: `time.ticks_diff()` 实现 1Hz 时钟 + 30min 天气两路协程。WDT 8s，每次循环喂狗。

### 网络握手
`setup_network()` → WiFi连接 → NTP对时（成功=MAC放行跳过认证）→ 失败则 Portal 动态注入 → NTP确认

### 天气数据流
API JSON → 流式 `split()` 提取 code/temp/text → code 映射 `.bin` 图标 → `blit_buffer()` 直推显存

### 图标构建
`tools/xbm2bin.py` 心知天气全量 39 code (0-38) 映射见 `icon_map`。前景 0xFD20 橙黄, 背景 0x0000 纯黑。严格 32x32px.

## UI 配色方案

`main.py` 定义的全局色板，改动 UI 时参考：

| 变量 | 色值 | 用途 |
|------|------|------|
| `C_BG` | `BLACK` (0x0000) | 全屏背景 |
| `C_ACCENT` | `color565(0, 200, 200)` | 顶部/底部装饰线、卡片边框 |
| `C_TIME` | `color565(0, 255, 128)` | 时间数字（卡片内） |
| `C_DATE` | `color565(180, 180, 180)` | 日期文字 |
| `C_TEMP` | `color565(255, 255, 255)` | 温度数字 |
| `C_DESC` | `color565(150, 150, 150)` | 天气描述 |
| `C_CARD` | `color565(12, 12, 28)` | 时间卡片底色 |
| `C_LINE` | `color565(40, 40, 40)` | 卡片内发光效果线 |

## 注意事项

- **时区**: `main.py:110` 硬编码 `+ 8 * 3600` (UTC+8)，换时区需改
- **天气 API**: `api.seniverse.com:80`，HTTP/**1.0**（非 1.1），参数 `language=en&unit=c`
- 华三 Portal 认证 `userId`/`password` 硬编码在 `net_weather.py`，换网需更新
- `test/desk_clock.py` SPI MOSI=GPIO5 与 main.py 的 GPIO0 不同——历史错误接线
