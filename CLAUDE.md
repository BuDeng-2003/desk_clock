# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

基于 ESP32-C3 supermini + MicroPython 的桌面时钟，通过 GC9A01 240x240 TFT LCD 显示时间、日期和天气信息。

## 硬件引脚映射

| 功能 | GPIO |
|------|------|
| SPI SCK | 4 |
| SPI MOSI | 0 |
| TFT DC | 2 |
| TFT CS | 3 |
| TFT RESET | 1 |
| TFT BL | 11 |
| BOOT 按钮 | 9 |

SPI 总线: `SPI(1)`, 波特率 40MHz.

## 文件结构与职责

```
src/main.py              # 主程序入口：硬件初始化、主循环（1Hz时钟 + 30min天气轮询）、WDT
src/common/net_weather.py # 网络模块：WiFi连接、校园网Portal认证、心知天气API拉取
vga1_8x16.py             # 8x16 点阵字体（ASCII 0x20-0x7f）
vga2_16x32.py            # 16x32 点阵字体（0-255 全字符集）
xbm2bin.py               # 本地工具：将 wether_UI/ 中的 XBM 图标转为 RGB565 .bin 文件
wether_UI/               # 天气图标 XBM 源文件（32x32 单色）
*.bin                    # 预转换的天气图标 RGB565 二进制（需推流至 ESP32 根目录）
test/                    # 开发调试脚本（非生产代码）
firmware_4MiB.bin        # ESP32-C3 4MB Flash MicroPython 固件
```

## 关键架构设计

### 主循环策略
`main.py` 采用**单调非阻塞轮询**而非 asyncio：通过 `time.ticks_diff()` 实现两个逻辑协程 —— 1Hz 时钟刷新和 30 分钟天气刷新。WDT 超时 8 秒，每次循环喂狗。

### 网络握手流程
`setup_network()` 的状态机顺序：
1. WiFi 物理层连接（20s 超时）
2. 尝试 NTP 对时——成功说明 MAC 无感知放行，直接跳过认证
3. NTP 失败则执行校园网 Portal 动态注入（探针获取加密参数 → POST 认证）
4. 再次 NTP 对时确认网络可用

### 天气数据流
心知天气 API 返回 JSON → 流式解析提取 `code` 和 `temperature` 字段（避免完整 JSON 解析以节省内存）→ `code` 映射到预生成的 `.bin` 图标文件 → `blit_buffer()` 直接写入显存。

### 内存管理
- `gc.threshold(16384)` 在启动时设置 GC 阈值
- 天气图标预分配 32×32×2 字节 `bytearray` 池，防止碎片化
- 每次网络操作后调用 `gc.collect()`
- API 响应缓冲区 128 字节上限，超出后滑动窗口截断

### 天气图标构建
`xbm2bin.py` 将 `wether_UI/*.xbm` 转为 `{code}.bin`，心知天气 `code` 映射见脚本内 `icon_map`。颜色配置：前景 0xFD20（橙黄），背景 0x0000（纯黑）。图标必须严格 32×32 像素（128 字节 XBM 数据）。

## ESP32 串口通信（重要）

**ESP32-C3 设备**: COM8, vid:303a pid:1001（内置 USB-Serial-JTAG）

**关键限制**: Git Bash (MSYS2) 环境下 Python 的 `pyserial` 对 Windows COM 口存在底层阻塞 bug —— `open()` 能成功，但 `read()`/`write()` 在 OS 层永久挂起。**所有 mpremote 命令必须通过 `.bat` 批处理文件执行**，bash 会自动将 `.bat` 委托给 Windows 原生命令行，绕过串口阻塞。

### mpremote 操作模板

不要直接在 bash 中执行 mpremote。先写入 `.bat` 文件再运行：

```bash
# 执行 MicroPython 代码
echo "@echo off && python -m mpremote connect COM8 exec \"...\"" > tmp.bat && ./tmp.bat

# 推送文件（单文件）
echo "@echo off && python -m mpremote connect COM8 cp src/main.py :main.py" > tmp.bat && ./tmp.bat

# 推送文件（多文件批量）
echo "@echo off && for %f in (*.bin) do python -m mpremote connect COM8 cp %f :%f" > tmp.bat && ./tmp.bat

# 软复位
echo "@echo off && python -m mpremote connect COM8 soft-reset" > tmp.bat && ./tmp.bat
```

mpremote 会自动发送 Ctrl+C 中断运行中的 `main.py` 进入 raw REPL，**不需要**手动按键进下载模式。只有在主循环死锁且 Ctrl+C 无效的极端情况下，才需要按住 BOOT 键 (GPIO9) 上电进入安全模式。

## 部署方式

MicroPython 项目无编译步骤。通过上述 `.bat` 包装的 mpremote 推流至 ESP32。

ESP32-C3 需先烧录 `firmware_4MiB.bin` 固件（MicroPython 4MB Flash 版本），且 `gc9a01` 驱动已内置在固件中。

## 注意事项

- 华三校园网 Portal 认证的 `userId`/`password` 硬编码在 `net_weather.py` 中，更换网络环境时需更新
- BOOT 键 (GPIO9) 在启动时检测：按下则进入安全模式直接退出到 REPL，防止死锁循环
- `test/desk_clock.py` 中 SPI MOSI 引脚为 GPIO5，与 `main.py` 的 GPIO0 不同——前者是测试用的错误接线记录
