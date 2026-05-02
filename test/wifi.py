import socket
import gc
import network

def fetch_weather(api_key, city="beijing"):
    gc.collect() 
    s = socket.socket()
    s.settimeout(3.0) 
    
    try:
        addr = socket.getaddrinfo('api.seniverse.com', 80)[0][-1]
        s.connect(addr)
        
        req = f"GET /v3/weather/now.json?key={api_key}&location={city}&language=en&unit=c HTTP/1.0\r\nHost: api.seniverse.com\r\nConnection: close\r\n\r\n"
        s.send(req.encode('utf-8'))
        
        buffer = b""
        weather_code = None
        temp = None
        
        while True:
            chunk = s.recv(64)
            if not chunk:
                break
            buffer += chunk
            
            if weather_code is None and b'"code":"' in buffer:
                try:
                    weather_code = buffer.split(b'"code":"')[1].split(b'"')[0]
                except IndexError:
                    pass
            
            if temp is None and b'"temperature":"' in buffer:
                try:
                    temp = buffer.split(b'"temperature":"')[1].split(b'"')[0]
                except IndexError:
                    pass
            
            # 极限优化：只要拿到这两个核心字段，直接强行断开 Socket，拒绝接收多余的垃圾数据
            if weather_code and temp:
                break
                
            if len(buffer) > 128:
                buffer = buffer[-64:]
                
        return weather_code.decode() if weather_code else None, temp.decode() if temp else None

    except Exception as e:
        print("Net Hard Fault:", e)
        return None, None
    finally:
        s.close()
        gc.collect()

# ========== 独立测试入口 ==========
if __name__ == "__main__":
    # 假设你的 boot.py 已经连上了 Wi-Fi
    API_KEY = "your-seniverse-api-key" 
    
    print("--- 内存压力测试 ---")
    print("RAM Before:", gc.mem_free())
    
    code, temperature = fetch_weather(API_KEY, "wuhan")
    
    print(f"提取结果: IconCode={code}, Temp={temperature}")
    print("RAM After:", gc.mem_free())