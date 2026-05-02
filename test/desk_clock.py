import machine
import gc
import time
import gc9a01
import vga2_16x32 as font  # 确保存入根目录后，这里才能 import 成功

# 严格对齐你的物理信号线
spi = machine.SPI(1, baudrate=40000000, sck=machine.Pin(4), mosi=machine.Pin(5))
tft = gc9a01.GC9A01(
    spi,
    width=240,   # 新增：强制声明 X 轴分辨率
    height=240,  # 新增：强制声明 Y 轴分辨率
    dc=machine.Pin(2, machine.Pin.OUT),
    cs=machine.Pin(3, machine.Pin.OUT),
    reset=machine.Pin(1, machine.Pin.OUT),
    backlight=machine.Pin(11, machine.Pin.OUT),
    rotation=0
)

tft.init()
# 全局唯一一次清屏
tft.fill(gc9a01.BLACK) 

# 绘制边界测试框
tft.rect(50, 100, 140, 40, gc9a01.color565(0, 255, 0))

print("--- 脏矩阵覆写压测开始 ---")
counter = 0

while counter < 1000:
    time_str = f"{counter:04d}"
    
    # 局部脏矩阵底层覆写：强制传入 BLACK 作为背景色
    tft.text(
        font, 
        time_str, 
        88, 104, 
        gc9a01.color565(255, 255, 255), 
        gc9a01.BLACK                    
    )
    
    counter += 1