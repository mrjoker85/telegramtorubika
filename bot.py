import os
import asyncio
import time
import sys
import socket
import aiohttp
from pyrogram import Client, filters
from rubpy import Client as RubikaClient

# خواندن اطلاعات امنیتی از Secrets گیت‌هاب
API_ID = int(os.getenv("API_ID", 21976897))
API_HASH = os.getenv("API_HASH", "0905826f369459a0a9d8d7c7e8be23ec")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8955555652:AAHUUDOuILmDD9TvEaOmtY-qmqM4Hf_KuIc")
RUBIKA_AUTH = os.getenv("RUBIKA_AUTH")

MAX_RUN_TIME = 19800  # ۵.۵ ساعت برای زنده ماندن سشن ابری
START_TIME = time.time()

async def test_connections():
    """تست اولیه اتصال به سرورهای اصلی تلگرام و روبیکا پیش از اجرای کلاینت‌ها"""
    print("🔍 در حال ارزیابی وضعیت شبکه و تست اتصال به سرورها...")
    
    targets = {
        "Telegram API": {"host": "api.telegram.org", "port": 443},
        "Rubika Core": {"host": "messengerg.rubika.ir", "port": 443}
    }
    
    all_ok = True
    
    for name, info in targets.items():
        try:
            # تست برقراری سوکت TCP در سطح شبکه
            stream = await asyncio.wait_for(
                asyncio.open_connection(info["host"], info["port"]), 
                timeout=5.0
            )
            writer = stream[1]
            writer.close()
            await writer.wait_closed()
            print(f"  🟢 اتصال به سرور {name} با موفقیت برقرار شد.")
        except Exception as e:
            print(f"  🔴 خطا در اتصال به سرور {name}: {e}")
            all_ok = False
            
    return all_ok

async def main():
    if not RUBIKA_AUTH:
        print("❌ خطای حیاتی: سکرت RUBIKA_AUTH در گیت‌هاب تنظیم نشده است!")
        sys.exit(1)

    # اجرای تست اتصال قبل از شروع هر کاری
    network_ready = await test_connections()
    if not network_ready:
        print("⚠️ هشدار: اختلال در دسترسی به سرورها شناسایی شد. با این حال تلاش برای اتصال آغاز می‌شود...")
    else:
        print("✅ وضعیت شبکه پایدار است. در حال لود کردن ربات‌ها...")

    # راه‌اندازی کلاینت تلگرام
    tg_app = Client("tg_session_cloud", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    await tg_app.start()
    print("✨ کلاینت تلگرام با موفقیت استارت خورد.")
    
    # راه‌اندازی و اتصال کلاینت روبیکا با Auth Token
    print("⚡ در حال اتصال به روبیکا از طریق Auth Token...")
    rub_app = RubikaClient(name="rubika_session_cloud", auth=RUBIKA_AUTH)
    
    # ورود به سشن و برقرار کردن ارتباط شبکه
    async with rub_app:
        me = await rub_app.get_me()
        user_info = me.get('user', {})
        print(f"🟢 روبیکا متصل شد! نام حساب: {user_info.get('first_name', 'کاربر روبیکا')}")
        print("\n🚀 ربات در سرور ابری گیت‌هاب آنلاین شد و آماده انتقال فایل است!")

        @tg_app.on_message(filters.document | filters.video | filters.audio | filters.photo)
        async def process_file(client, message):
            try:
                print("📥 در حال دریافت فایل از تلگرام...")
                file_path = await message.download()
                
                print("📤 در حال ارسال فایل به پیام‌های ذخیره شده روبیکا...")
                # ارسال فایل به Saved Messages (me) در روبیکا
                await rub_app.send_file(chat_id="me", file=file_path, caption="منتقل شده از سرور ابری")
                
                # حذف فایل از هارد دیسک گیت‌هاب برای پر نشدن فضا
                if os.path.exists(file_path): 
                    os.remove(file_path)
                print("✅ فایل با موفقیت منتقل و پاکسازی شد.")
            except Exception as e:
                print(f"❌ خطا در انتقال فایل: {e}")

        # حلقه زنده نگه داشتن اسکریپت تا سقف ۵.۵ ساعت
        while True:
            await asyncio.sleep(10)
            if time.time() - START_TIME > MAX_RUN_TIME:
                print("⏳ زمان اجرای ورک‌فلو به پایان رسید. ری‌استارت امن...")
                await tg_app.stop()
                sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
