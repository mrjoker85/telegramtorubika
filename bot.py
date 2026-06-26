import os
import json
import subprocess
import asyncio
import aiohttp
import time
import sys
from aiohttp_socks import ProxyConnector
from pyrogram import Client, filters
from rubpy import Client as RubikaClient

# خواندن اطلاعات از Secrets محیط ابری (Heroku / GitHub)
API_ID = int(os.getenv("API_ID", 21976897))
API_HASH = os.getenv("API_HASH", "0905826f369459a0a9d8d7c7e8be23ec")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8955555652:AAHUUDOuILmDD9TvEaOmtY-qmqM4Hf_KuIc")
PHONE_NUMBER = os.getenv("PHONE_NUMBER", "09054009380")

MAX_RUN_TIME = 19800  # ۵.۵ ساعت به ثانیه (جهت دور زدن محدودیت ۶ ساعته گیت‌هاب اکشنز)
START_TIME = time.time()

V2RAY_CONFIGS = [
    "vless://f80cf976-c64e-4556-a07c-75b9461b5165@dash.wordqress.store:18323?security=&encryption=none&headerType=&type=tcp#%40filembad",
    "vless://fda0244a-80e6-4be3-9fe0-e522d4910e15@5.75.207.247:44004?type=tcp&encryption=none&security=reality&pbk=KTAuJl8Ga2u2IZmfizQj6yEw3fOcqxLeYVhCA_r1wmQ&fp=chrome&sni=www.intel.com&sid=77b0689f&spx=%2F&flow=xtls-rprx-vision#%40filembad",
    "trojan://Mitivpn@151.101.110.219:443?path=%2Fde%3Dmitivpn&security=tls&alpn=http%2F1.1&host=3-mitivpn.global.ssl.fastly.net&fp=firefox&type=ws&sni=global.fastly.com#%40filembad",
    "vless://39eb6d15-e27a-4f2e-b865-b49a15b2d5f6@93.114.98.241:443?security=reality&encryption=none&pbk=B_wBq5f4zAcNXK2nvrsOOV1Fz3Vb_I6VBV_VlNg7emA&headerType=none&fp=chrome&type=tcp&flow=xtls-rprx-vision&sni=play.google.com&sid=3026393990dbc6c9#%40filembad"
]

def run_xray_config_bridge(config_url):
    base_config = {
        "log": {"loglevel": "none"},
        "inbounds": [{
            "port": 10808, "listen": "127.0.0.1", "protocol": "socks", "settings": {"udp": True}
        }],
        "outbounds": [{"protocol": "freedom"}]
    }
    with open("/tmp/xray_config.json", "w") as f:
        json.dump(base_config, f)

async def check_connectivity():
    print(f"🔍 ارزیابی کانفیگ‌ها در محیط ابری...")
    HEROKU_URL = "https://id.heroku.com"
    GOOGLE_URL = "https://www.google.com"
    
    for index, config in enumerate(V2RAY_CONFIGS, 1):
        run_xray_config_bridge(config)
        subprocess.run(["pkill", "-f", "xray"], capture_output=True)
        # اجرای پس‌زمینه هسته Xray در لینوکس سرور ابری
        subprocess.Popen(["xray", "-c", "/tmp/xray_config.json"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await asyncio.sleep(2)
        
        connector = ProxyConnector.from_url("socks5://127.0.0.1:10808")
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                async with session.get(HEROKU_URL, timeout=4) as resp:
                    if resp.status in [200, 404, 302]:
                        print(f"  🟢 کانفیگ {index} برای هروکو موفقیت آمیز است!")
                        return "socks5://127.0.0.1:10808"
            except:
                try:
                    async with session.get(GOOGLE_URL, timeout=3) as resp:
                        if resp.status == 200:
                            print(f"  🟢 کانفیگ {index} برای گوگل/تلگرام موفقیت آمیز است!")
                            return "socks5://127.0.0.1:10808"
                except:
                    print(f"  🔴 کانفیگ {index} پاسخگو نبود.")
    return None

async def main():
    proxy_str = await check_connectivity()
    
    session_name = f"tg_session_cloud"
    tg_app = Client(session_name, api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    await tg_app.start()
    
    rub_app = RubikaClient(name=PHONE_NUMBER)
    await rub_app.start()
    
    print("\n🚀 ربات در سرور ابری با موفقیت آنلاین شد!")

    @tg_app.on_message(filters.document | filters.video | filters.audio | filters.photo)
    async def process_file(client, message):
        try:
            file_path = await message.download()
            await rub_app.send_file(chat_id="me", file=file_path, caption="منتقل شده از سرور ابری")
            if os.path.exists(file_path): os.remove(file_path)
        except Exception as e:
            print(f"Error: {e}")

    # سیستم پایش زمان برای جلوگیری از کرش گیت‌هاب اکشنز
    while True:
        await asyncio.sleep(10)
        if time.time() - START_TIME > MAX_RUN_TIME:
            print("⏳ زمان ۵.۵ ساعت به پایان رسید. ری‌استارت امن جهت حفظ پایداری ورک‌فلو...")
            await tg_app.stop()
            sys.exit(0) # خروج موفقیت‌آمیز تا گیت‌هاب ارور ندهد و ران بعدی اجرا شود.

if __name__ == "__main__":
    asyncio.run(main())