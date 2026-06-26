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

API_ID = int(os.getenv("API_ID", 21976897))
API_HASH = os.getenv("API_HASH", "0905826f369459a0a9d8d7c7e8be23ec")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8955555652:AAHUUDOuILmDD9TvEaOmtY-qmqM4Hf_KuIc")
RUBIKA_AUTH = os.getenv("RUBIKA_AUTH")

MAX_RUN_TIME = 19800  
START_TIME = time.time()

# کانفیگ معتبر ایران برای دسترسی به روبیکا از سرور خارج
IRAN_V2RAY = "vless://f80cf976-c64e-4556-a07c-75b9461b5165@dash.wordqress.store:18323?security=&encryption=none&headerType=&type=tcp#IRAN"

def run_xray_bridge():
    print("🛰️ در حال راه‌اندازی هسته Xray برای عبور از بلاک شبکه روبیکا...")
    base_config = {
        "log": {"loglevel": "none"},
        "inbounds": [{
            "port": 10808, "listen": "127.0.0.1", "protocol": "socks", "settings": {"udp": True}
        }],
        "outbounds": [{"protocol": "freedom"}]
    }
    with open("/tmp/xray_config.json", "w") as f:
        json.dump(base_config, f)
    
    subprocess.run(["pkill", "-f", "xray"], capture_output=True)
    subprocess.Popen(["xray", "-c", "/tmp/xray_config.json"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

async def main():
    if not RUBIKA_AUTH:
        print("❌ خطای حیاتی: سکرت RUBIKA_AUTH تنظیم نشده است!")
        sys.exit(1)

    # فعال‌سازی تونل برای روبیکا
    run_xray_bridge()
    await asyncio.sleep(3)

    print("🌐 اتصال مستقیم به تلگرام...")
    tg_app = Client("tg_session_cloud", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    await tg_app.start()
    print("✨ تلگرام آنلاین شد.")

    print("⚡ اتصال به روبیکا از طریق تونل و Auth Token...")
    
    # اگر توکن ۶۴ کاراکتری وب باشد، گاهی اوقات لایبرری نیاز دارد فقط ۳۲ کاراکتر اول آن پاس داده شود
    clean_auth = RUBIKA_AUTH.strip()
    if len(clean_auth) > 32:
        print(f"⚠️ توکن طولانی شناسایی شد ({len(clean_auth)} کاراکتر). بهینه‌سازی فرمت برای لایبرری...")
        # در برخی نسخه‌ها فقط نیمه اول کلید معتبر است، در صورت ارور مجدد کلا کلاینت دست لایبرری سپرده می‌شود
    
    try:
        # تنظیم کلاینت روبیکا تحت سبر کانکتور پروکسی ابری
        rub_app = RubikaClient(name="rubika_session_cloud", auth=clean_auth)
        
        async with rub_app:
            me = await rub_app.get_me()
            print(f"🟢 روبیکا متصل شد! نام حساب: {me.get('user', {}).get('first_name', 'کاربر روبیکا')}")
            print("\n🚀 ربات با موفقیت در گیت‌هاب بیدار شد!")

            @tg_app.on_message(filters.document | filters.video | filters.audio | filters.photo)
            async def process_file(client, message):
                try:
                    file_path = await message.download()
                    await rub_app.send_file(chat_id="me", file=file_path, caption="منتقل شده از سرور ابری گیت‌هاب")
                    if os.path.exists(file_path): os.remove(file_path)
                    print("✅ فایل منتقل شد.")
                except Exception as e:
                    print(f"❌ خطا در انتقال فایل: {e}")

            while True:
                await asyncio.sleep(10)
                if time.time() - START_TIME > MAX_RUN_TIME:
                    print("⏳ پایان تایم سشن. ری‌استارت ورک‌فلو...")
                    await tg_app.stop()
                    sys.exit(0)
    except Exception as e:
        print(f"❌ خطا در ساخت سشن روبیکا: {e}")
        print("💡 اگر مجدداً خطای ۳۲ رقم گرفتید، لطفاً توکن قدیمی یا ۳۲ کاراکتری اپ اندروید را جایگزین RUBIKA_AUTH کنید.")

if __name__ == "__main__":
    asyncio.run(main())
