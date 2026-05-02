import machine
import time
import gc
gc.threshold(16384)
import gc9a01
import vga2_16x32 as font_big   
import vga1_8x16 as font_small  
from common import net_weather

# ================= 1. 环境配置 =================
WIFI_SSID = "WHU-STU"            # ⚠️ 替换为你校园网的 Wi-Fi 名字
WIFI_PASS = ""                    # 校园网通常留空
API_KEY = "your-seniverse-api-key"     # 心知天气 API
CITY = "wuhan"                    # 城市拼音

# ================= 2. 防死锁后门 =================
boot_btn = machine.Pin(9, machine.Pin.IN, machine.Pin.PULL_UP)
print("[BOOT] 3秒后启动主引擎... (如遇死锁请按住 BOOT 键或狂按 Ctrl+C)")
time.sleep(3)
if boot_btn.value() == 0:
    print("[SAFE BOOT] 检测到 BOOT 键按下，挂起程序进入 REPL！")
    import sys
    sys.exit()

# ================= 3. 硬件与显存初始化 =================
gc.collect()
# 预分配 32x32 图标贴图池，防止碎片化
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
tft.fill(gc9a01.BLACK)

# ================= 4. 阻塞式网络握手 =================
tft.text(font_small, "WIFI & PORTAL...", 40, 110, gc9a01.color565(0, 255, 255), gc9a01.BLACK)

try:
    net_weather.setup_network(WIFI_SSID, WIFI_PASS)
except Exception as e:
    tft.text(font_small, "NET ERROR, REBOOT", 40, 110, gc9a01.color565(255, 0, 0), gc9a01.BLACK)
    print("网络错误:", e)
    time.sleep(5)
    machine.reset()
# 联网与认证彻底通过后，再挂载看门狗
wdt = machine.WDT(timeout=8000) 
tft.fill(gc9a01.BLACK) 

# 绘制静态赛博朋克分割线
tft.line(30, 80, 210, 80, gc9a01.color565(50, 50, 50))
tft.line(30, 160, 210, 160, gc9a01.color565(50, 50, 50))

# ================= 5. 单调非阻塞主循环 =================
last_time_update = 0
last_weather_update = -1800000 # 负数确保开机首秒强制刷天气

while True:
    wdt.feed() 
    current_ms = time.ticks_ms()
    
    # [协程 1]: 1Hz 时钟刷新
    if time.ticks_diff(current_ms, last_time_update) >= 1000:
        last_time_update = current_ms
        t = time.localtime(time.time() + 8 * 3600) # UTC+8
        
        # 顶部：日期
        date_str = f"{t[0]}-{t[1]:02d}-{t[2]:02d}"
        tft.text(font_small, date_str, 75, 50, gc9a01.color565(200, 200, 200), gc9a01.BLACK)
        
        # 中部：大号时间
        time_str = f"{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
        tft.text(font_big, time_str, 50, 110, gc9a01.color565(0, 255, 128), gc9a01.BLACK)

    # [协程 2]: 30Min 天气面板更新
    if time.ticks_diff(current_ms, last_weather_update) >= 1800000:
        last_weather_update = current_ms
        
        code, temp = net_weather.fetch_weather(API_KEY, CITY)
        
        if code and temp:
            # 渲染温度 (带尾部空格抹除旧数据)
            temp_str = f"{temp} C  "
            tft.text(font_small, temp_str, 120, 180, gc9a01.color565(255, 165, 0), gc9a01.BLACK)
            
            # 读取 Flash 中的 .bin 图标推入显存
            try:
                with open(f"{code}.bin", "rb") as f:
                    f.readinto(icon_buf)
                tft.blit_buffer(icon_buf, 75, 172, ICON_SIZE, ICON_SIZE)
            except OSError:
                # 若无对应的图标文件，显示报错替代
                tft.text(font_small, "[X]", 75, 180, gc9a01.color565(255, 0, 0), gc9a01.BLACK)
            
    time.sleep_ms(50)