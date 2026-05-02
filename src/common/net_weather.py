import network
import time
import ntptime
import gc
import socket

# ==================== 校园网黑客探针 ====================
def login_portal(user_id, pass_enc):
    print("[NET] 1. 触发探针，动态获取 ESP32 专属加密特征...")
    s = socket.socket()
    s.settimeout(5.0)
    query_string = ""
    try:
        addr = socket.getaddrinfo('1.1.1.1', 80)[0][-1]
        s.connect(addr)
        s.send(b"GET / HTTP/1.1\r\nHost: 1.1.1.1\r\nConnection: close\r\n\r\n")
        res = b""
        while True:
            chunk = s.recv(512)
            if not chunk: break
            res += chunk
            if len(res) > 1024: break
        
        # 内存安全切割：从 JS 脚本中切出真实 queryString
        res_str = res.decode('utf-8', 'ignore')
        if 'index.jsp?' in res_str:
            query_string = res_str.split('index.jsp?')[1].split("'")[0]
            print("[PROBE] 加密参数提取成功！")
    except Exception as e:
        print("[PROBE] 探测失败:", e)
    finally:
        s.close()
        gc.collect()

    if not query_string:
        print("[PORTAL] 致命错误：未获取到加密参数，放弃 POST。")
        return

    print("[NET] 2. 构建 Payload 并执行 POST 注入...")
    # ePortal 的双重 URL 编码机制
    encoded_query = query_string.replace("=", "%253D").replace("&", "%2526")
    
    PORTAL_HOST = "172.19.1.9"
    PORTAL_PORT = 8080
    PORTAL_PATH = "/eportal/InterFace.do?method=login"
    
    PAYLOAD = f"userId={user_id}&password={pass_enc}&service=Internet&queryString={encoded_query}&operatorPwd=&operatorUserId=&validcode=&passwordEncrypt=true"
    
    s2 = socket.socket()
    s2.settimeout(5.0)
    try:
        addr = socket.getaddrinfo(PORTAL_HOST, PORTAL_PORT)[0][-1]
        s2.connect(addr)
        req = "POST " + PORTAL_PATH + " HTTP/1.1\r\n" + \
              "Host: " + PORTAL_HOST + ":" + str(PORTAL_PORT) + "\r\n" + \
              "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n" + \
              "Content-Type: application/x-www-form-urlencoded\r\n" + \
              "Content-Length: " + str(len(PAYLOAD)) + "\r\n" + \
              "Connection: close\r\n\r\n" + \
              PAYLOAD
               
        s2.send(req.encode('utf-8'))
        res = s2.recv(512)
        print("[PORTAL] 认证响应头:\n", res.decode('utf-8', 'ignore').split('\r\n\r\n')[0])
    except Exception as e:
        print("[PORTAL] 注入失败:", e)
    finally:
        s2.close()
        gc.collect()
def setup_network(ssid, password="", portal_user="", portal_pass=""):
    gc.collect()
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    time.sleep(0.5)
    wlan.active(True)
    wlan.config(txpower=5) # 锁死发射功率防断电
    
    wlan.disconnect()
    if not wlan.isconnected():
        print(f"[NET] 正在连接无加密校园网: {ssid} ...")
        # 校园网通常无密码，如果你们学校有统一的初始密码，填入 password 并改为 wlan.connect(ssid, password)
        wlan.connect(ssid) 
        timeout = 20
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
        
        if not wlan.isconnected():
            raise Exception("物理层 Wi-Fi 握手超时")
            
    print(f"[NET] 物理层连接成功，本机内网 IP: {wlan.ifconfig()[0]}")
    
   # ⚠️ 状态机：先测 NTP，通了直接跳过认证
    ntptime.host = "ntp.aliyun.com"
    try:
        ntptime.settime()
        print("[NET] 侦测到 MAC 无感知放行，跳过 Portal 注入！")
    except Exception:
        print("[NET] 外网阻断，执行 Portal 动态注入...")
        login_portal(portal_user, portal_pass)
        try:
            ntptime.settime()
            print("[NET] 注入完毕，NTP 同步成功！")
        except Exception:
            print("[NET] 致命错误：网络彻底死亡！")

def fetch_weather(api_key, city="wuhan"):
    gc.collect()
    s = socket.socket()
    s.settimeout(3.0) 
    
    try:
        addr = socket.getaddrinfo('api.seniverse.com', 80)[0][-1]
        s.connect(addr)
        
        req = f"GET /v3/weather/now.json?key={api_key}&location={city}&language=en&unit=c HTTP/1.0\r\nHost: api.seniverse.com\r\nConnection: close\r\n\r\n"
        s.send(req.encode('utf-8'))
        
        buffer = b""
        weather_code, temp, text = None, None, None

        while True:
            chunk = s.recv(64)
            if not chunk: break
            buffer += chunk

            if weather_code is None and b'"code":"' in buffer:
                try: weather_code = buffer.split(b'"code":"')[1].split(b'"')[0]
                except IndexError: pass

            if temp is None and b'"temperature":"' in buffer:
                try: temp = buffer.split(b'"temperature":"')[1].split(b'"')[0]
                except IndexError: pass

            if text is None and b'"text":"' in buffer:
                try: text = buffer.split(b'"text":"')[1].split(b'"')[0]
                except IndexError: pass

            if weather_code and temp and text: break
            if len(buffer) > 128: buffer = buffer[-64:]

        return (weather_code.decode() if weather_code else None,
                temp.decode() if temp else None,
                text.decode() if text else None)
    except Exception:
        return None, None, None
    finally:
        s.close()
        gc.collect()