import network
import time
import ntptime
import gc

# 1. 强行清理内存碎片
gc.collect()

def setup_network(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    time.sleep(0.5)
    wlan.active(True)
    
    # ⚠️ 架构师级硬件补丁：锁死发射功率，防止劣质供电导致的瞬态崩盘
    wlan.config(txpower=5)
    print("射频发射功率已限制在 5dBm...")
    time.sleep(2.0) 
    
    wlan.disconnect()
    
    if not wlan.isconnected():
        print(f"正在尝试握手加密热点: {ssid} ...")
        wlan.connect(ssid, password)
        
        timeout = 15
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
            print(f"等待分配 IP... 剩余 {timeout} 秒")
            
        if not wlan.isconnected():
            raise Exception(f"致命错误: WiFi 握手失败! 底层状态码: {wlan.status()}")
            
    print("WiFi 就绪! IP:", wlan.ifconfig()[0])
    
    # 2. 对齐时间基准
    ntptime.host = "ntp.aliyun.com"
    try:
        print("正在同步 NTP 时间...")
        ntptime.settime()
        # 换算北京时间 (UTC+8)
        current_time = time.localtime(time.time() + 8 * 3600)
        print("RTC 对时成功! 当前时间:", current_time)
    except Exception as e:
        print("NTP 同步失败:", e)

# 填入你真实的带密码热点信息
setup_network("PCHotspot", "12345678")