# desk_clock

ESP32-C3 supermini + MicroPython 桌面时钟，GC9A01 240x240 TFT LCD 显示时间、日期和天气。

> 通用嵌入式规范（串口通信、内存管理、Git 提交等）见父目录 `C:\Desktop\embedded\CLAUDE.md`

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
esp32_image/             # 设备文件系统镜像（推流 = 此目录 → ESP32 根目录）
  main.py                #   主程序：硬件初始化、主循环、WDT
  common/net_weather.py  #   网络：WiFi + Portal认证 + 心知天气API
  vga1_8x16.py           #   8x16 字体 (ASCII 0x20-0x7f)
  vga2_16x32.py          #   16x32 字体 (0-255)
  *.bin                  #   天气图标 RGB565 (39个, 0.bin~38.bin)
wether_UI/               # 图标 XBM 源文件 (22个)
xbm2bin.py               # 构建: wether_UI/*.xbm → esp32_image/*.bin
test/                    # 调试脚本
firmware_4MiB.bin        # MicroPython 固件 (含 gc9a01 驱动)
```

## 架构要点

### 主循环
单调非阻塞轮询: `time.ticks_diff()` 实现 1Hz 时钟 + 30min 天气两路协程。WDT 8s，每次循环喂狗。

### 网络握手
`setup_network()` → WiFi连接 → NTP对时（成功=MAC放行跳过认证）→ 失败则 Portal 动态注入 → NTP确认

### 天气数据流
API JSON → 流式 `split()` 提取 code/temp/text → code 映射 `.bin` 图标 → `blit_buffer()` 直推显存

### 图标构建
`xbm2bin.py` 心知天气全量 39 code (0-38) 映射见 `icon_map`。前景 0xFD20 橙黄, 背景 0x0000 纯黑。严格 32x32px.

## 注意事项

- 华三 Portal 认证 `userId`/`password` 硬编码在 `net_weather.py`，换网需更新
- `test/desk_clock.py` SPI MOSI=GPIO5 与 main.py 的 GPIO0 不同——历史错误接线
