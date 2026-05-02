import re
import struct
import os

def xbm_to_rgb565_bin(xbm_path, bin_path, fg_color=0xFFFF, bg_color=0x0000):
    with open(xbm_path, 'r') as f:
        content = f.read()

    hex_vals = re.findall(r'0x[0-9a-fA-F]{2}', content)
    if len(hex_vals) != 128:
        print(f"跳过 {xbm_path}：分辨率非 32x32，字节数 {len(hex_vals)} 异常。")
        return

    print(f"正在转换: {xbm_path} -> {bin_path}")
    with open(bin_path, 'wb') as out_f:
        for hex_str in hex_vals:
            byte_val = int(hex_str, 16)
            for i in range(8):
                bit = (byte_val >> i) & 1
                color = fg_color if bit else bg_color
                out_f.write(struct.pack('>H', color))

# ================= 映射与执行区 =================
# 心知天气全量代码映射 (0-38)
icon_map = {
    # 晴 / 晴间多云
    "0": "sun.xbm",
    "1": "moon.xbm",
    "2": "cloud_sun.xbm",
    "3": "cloud_moon.xbm",
    # 多云
    "4": "cloud_sun.xbm",
    "5": "cloud_moon.xbm",
    # 阴间多云 / 阴
    "6": "clouds.xbm",
    "7": "clouds.xbm",
    "8": "clouds.xbm",
    "9": "clouds.xbm",
    # 阵雨 / 中雨
    "10": "rain1.xbm",
    "11": "rain1_moon.xbm",
    "12": "rain1.xbm",
    "13": "rain1_moon.xbm",
    # 大雨 / 暴雨
    "14": "rain2.xbm",
    "15": "rain2.xbm",
    "16": "rain2.xbm",
    "17": "rain2.xbm",
    # 雷阵雨
    "18": "rain_lightning.xbm",
    "19": "rain_lightning.xbm",
    # 冰雹 / 雨夹雪
    "20": "rain_snow.xbm",
    "21": "rain_snow.xbm",
    "22": "rain_snow.xbm",
    "23": "rain_snow.xbm",
    # 小雪 / 中雪 / 大雪
    "24": "snow.xbm",
    "25": "snow_moon.xbm",
    "26": "snow.xbm",
    "27": "snow_moon.xbm",
    "28": "snow.xbm",
    "29": "snow_moon.xbm",
    # 雾
    "30": "cloud.xbm",
    "31": "cloud.xbm",
    # 沙尘 / 浮尘 / 扬沙 / 沙尘暴
    "32": "wind.xbm",
    "33": "wind.xbm",
    "34": "wind.xbm",
    "35": "wind.xbm",
    "36": "wind.xbm",
    "37": "wind.xbm",
    "38": "wind.xbm",
}

SRC_DIR = "wether_UI"
OUT_DIR = "esp32_image"

if not os.path.exists(SRC_DIR):
    print(f"致命错误: 找不到素材文件夹 '{SRC_DIR}'")
elif not os.path.exists(OUT_DIR):
    print(f"致命错误: 找不到输出文件夹 '{OUT_DIR}'")
else:
    for code, xbm_name in icon_map.items():
        xbm_file = os.path.join(SRC_DIR, xbm_name)
        out_file = os.path.join(OUT_DIR, f"{code}.bin")
        if os.path.exists(xbm_file):
            xbm_to_rgb565_bin(xbm_file, out_file, fg_color=0xFD20, bg_color=0x0000)
        else:
            print(f"缺失素材: 找不到 {xbm_file}")

    print(f"转换结束。{len(icon_map)} 个 .bin 文件已生成到 {OUT_DIR}/")
