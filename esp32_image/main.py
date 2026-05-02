import machine
import time
import gc
gc.threshold(16384)
import gc9a01
from fonts import vga2_16x32 as font_big
from fonts import vga1_8x16 as font_small
from common import net_weather

# ================= 1. 环境配置 =================
WIFI_SSID = "WHU-STU"
WIFI_PASS = ""
API_KEY = "your-seniverse-api-key"
CITY = "wuhan"

# ================= 2. 配色方案 =================
C_BG = gc9a01.BLACK
C_ACCENT = gc9a01.color565(0, 200, 200)
C_TIME = gc9a01.color565(0, 255, 128)
C_DATE = gc9a01.color565(180, 180, 180)
C_TEMP = gc9a01.color565(255, 255, 255)
C_DESC = gc9a01.color565(150, 150, 150)
C_CARD = gc9a01.color565(12, 12, 28)
C_LINE = gc9a01.color565(40, 40, 40)

# ================= 3. 防死锁后门 =================
boot_btn = machine.Pin(9, machine.Pin.IN, machine.Pin.PULL_UP)
print("[BOOT] 3秒后启动主引擎...")
time.sleep(3)
if boot_btn.value() == 0:
    print("[SAFE BOOT] 进入 REPL")
    import sys
    sys.exit()

# ================= 4. 硬件与显存初始化 =================
gc.collect()
ICON_SIZE = 32
icon_buf = bytearray(ICON_SIZE * ICON_SIZE * 2)

spi = machine.SPI(1, baudrate=40000000, sck=machine.Pin(4), mosi=machine.Pin(0))
tft = gc9a01.GC9A01(
    spi, width=240, height=240,
    dc=machine.Pin(2, machine.Pin.OUT),
    cs=machine.Pin(3, machine.Pin.OUT),
    reset=machine.Pin(1, machine.Pin.OUT),
    backlight=machine.Pin(11, machine.Pin.OUT),
    rotation=0
)
tft.init()
tft.fill(C_BG)

# ================= 5. 静态元素（绘制一次） =================
# 顶部 accent 线
tft.fill_rect(0, 0, 240, 3, C_ACCENT)

# 日期下划线（居中 60px）
tft.line(90, 42, 150, 42, C_ACCENT)

# 时间卡片边框 + 填充
CARD_X, CARD_Y, CARD_W, CARD_H = 32, 52, 176, 78
tft.fill_rect(CARD_X, CARD_Y, CARD_W, CARD_H, C_CARD)
tft.rect(CARD_X, CARD_Y, CARD_W, CARD_H, C_ACCENT)
# 卡片内发光效果：内缩 2px 再画一圈暗色
tft.rect(CARD_X + 2, CARD_Y + 2, CARD_W - 4, CARD_H - 4, C_LINE)

# 中部分割线
tft.line(40, 137, 200, 137, C_LINE)

# 底部 accent 线
tft.fill_rect(0, 237, 240, 3, C_ACCENT)

# 星期映射（MicroPython weekday: 0=Mon ... 6=Sun）
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# ================= 6. 阻塞式网络握手 =================
tft.text(font_small, "WIFI & PORTAL...", 40, 110, C_ACCENT, C_BG)

try:
    net_weather.setup_network(WIFI_SSID, WIFI_PASS)
except Exception as e:
    tft.text(font_small, "NET ERROR, REBOOT", 40, 110, gc9a01.color565(255, 0, 0), C_BG)
    print("网络错误:", e)
    time.sleep(5)
    machine.reset()

wdt = machine.WDT(timeout=8000)
tft.fill(C_BG)

# 重绘静态元素（网络握手期间可能被覆盖）
tft.fill_rect(0, 0, 240, 3, C_ACCENT)
tft.line(90, 42, 150, 42, C_ACCENT)
tft.fill_rect(CARD_X, CARD_Y, CARD_W, CARD_H, C_CARD)
tft.rect(CARD_X, CARD_Y, CARD_W, CARD_H, C_ACCENT)
tft.rect(CARD_X + 2, CARD_Y + 2, CARD_W - 4, CARD_H - 4, C_LINE)
tft.line(40, 137, 200, 137, C_LINE)
tft.fill_rect(0, 237, 240, 3, C_ACCENT)

# ================= 7. 主循环 =================
last_time_update = 0
last_weather_update = -1800000
last_date_str = ""  # 检测日期变化，避免每日重复绘制

while True:
    wdt.feed()
    current_ms = time.ticks_ms()

    # [协程 1]: 1Hz 时间刷新
    if time.ticks_diff(current_ms, last_time_update) >= 1000:
        last_time_update = current_ms
        t = time.localtime(time.time() + 8 * 3600)

        # 日期（仅变化时重绘）
        date_str = f"{t[1]:02d}/{t[2]:02d} {WEEKDAYS[t[6]]}"
        if date_str != last_date_str:
            last_date_str = date_str
            # 擦除旧日期
            tft.fill_rect(0, 15, 240, 26, C_BG)
            # 重绘下划线
            tft.line(90, 42, 150, 42, C_ACCENT)
            # 日期文本居中
            date_w = len(date_str) * 8
            tft.text(font_small, date_str, (240 - date_w) // 2, 20, C_DATE, C_BG)

        # 时间（每秒重绘，text 自带背景覆写无需先擦除）
        time_str = f"{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
        time_w = len(time_str) * 16
        time_x = (240 - time_w) // 2
        tft.text(font_big, time_str, time_x, CARD_Y + 23, C_TIME, C_CARD)

    # [协程 2]: 30Min 天气更新
    if time.ticks_diff(current_ms, last_weather_update) >= 1800000:
        last_weather_update = current_ms

        code, temp, text = net_weather.fetch_weather(API_KEY, CITY)

        if code and temp:
            # 擦除天气区域
            tft.fill_rect(0, 145, 240, 90, C_BG)

            # 左列：图标 (y=148)，描述在其下方 (y=184)
            icon_y = 148
            # 右列：温度 (y=158)，居中对齐左列整体 (图标顶148→描述底199, 中心174)
            temp_y = 158

            temp_str = str(temp)
            # 计算图标+温度整行宽度，居中排列
            temp_group_w = len(temp_str) * 16 + 4 + 6 + 16  # 数字 + 间距 + o + C
            row_w = ICON_SIZE + 16 + temp_group_w           # 图标 + 间距 + 温度组
            row_x = (240 - row_w) // 2
            icon_x = row_x
            temp_x = row_x + ICON_SIZE + 16

            try:
                with open(f"icons/{code}.bin", "rb") as f:
                    f.readinto(icon_buf)
                tft.blit_buffer(icon_buf, icon_x, icon_y, ICON_SIZE, ICON_SIZE)
            except OSError:
                tft.text(font_small, "[X]", icon_x, icon_y + 8, gc9a01.color565(255, 0, 0), C_BG)

            # 描述：居中于图标下方
            if text:
                desc = text[0].upper() + text[1:]
                desc_w = len(desc) * 8
                tft.text(font_small, desc, icon_x + (ICON_SIZE - desc_w) // 2, 184, C_DESC, C_BG)

            # 温度数字
            tft.text(font_big, temp_str, temp_x, temp_y, C_TEMP, C_BG)
            deg_x = temp_x + len(temp_str) * 16 + 4
            tft.text(font_small, "o", deg_x, temp_y - 4, C_TEMP, C_BG)
            tft.text(font_big, "C", deg_x + 6, temp_y, C_TEMP, C_BG)

    time.sleep_ms(50)
