import os
import time
import requests
import schedule
import threading
from telegram import Bot
from telegram.error import TelegramError

# إعدادات البوت
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
bot = Bot(token=TELEGRAM_TOKEN) if TELEGRAM_TOKEN else None

BASE_URL = "https://api.mexc.com/api/v3"
tracked_coins = {}

# وظيفة للحفاظ على الخدمة نشطة
def keep_alive():
    while True:
        try:
            # أرسل طلب ping للخادم للحفاظ على نشاط الخدمة
            requests.get("https://mexc-alert-bot.onrender.com", timeout=10)
            print("تم إرسال ping للحفاظ على الخدمة نشطة")
        except:
            print("فشل ping ولكن سيستمر البوت في العمل")
        time.sleep(300)  # كل 5 دقائق

# بدء وظيفة الحفاظ على النشاط في خلفية
threading.Thread(target=keep_alive, daemon=True).start()

def get_coins():
    try:
        response = requests.get(f"{BASE_URL}/ticker/24hr", timeout=10)
        return response.json() if response.status_code == 200 else []
    except:
        return []

def send_alert(symbol, change, price, volume):
    emoji = "🚀" if change > 0 else "🔻"
    direction = "صعود" if change > 0 else "هبوط"
    
    # تم تصحيح الأخطاء في صياغة f-string هنا
    message = (
        f"{emoji} {symbol}\n"
        f"{direction} بنسبة: {abs(change
