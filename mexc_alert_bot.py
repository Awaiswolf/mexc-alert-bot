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
    
    message = (
        f"{emoji} {symbol}\n"
        f"{direction} بنسبة: {abs(change):.2f}%\n"
        f"السعر: {price}\n"
        f"الحجم: ${volume:,.0f}"
    )
    
    if bot:
        try:
            bot.send_message(chat_id=CHAT_ID, text=message)
            print(f"تم إرسال تنبيه: {symbol}")
        except TelegramError as e:
            print(f"خطأ في إرسال التنبيه: {e}")
    else:
        print(f"بدون إرسال: {message}")

def check_prices():
    coins = get_coins()
    if not coins: 
        print("لم يتم الحصول على بيانات العملات")
        return
    
    print(f"جاري فحص {len(coins)} عملة...")
    
    for coin in coins:
        symbol = coin['symbol']
        volume = float(coin['quoteVolume'])
        price = float(coin['lastPrice'])
        
        # توسيع نطاق حجم التداول (30,000 - 700,000 دولار)
        if 30000 <= volume <= 700000:
            if symbol not in tracked_coins:
                tracked_coins[symbol] = price
                print(f"بدأ تتبع: {symbol} | السعر: {price} | الحجم: ${volume:,.0f}")
        
        # التحقق من التغيرات
        elif symbol in tracked_coins:
            base_price = tracked_coins[symbol]
            change = ((price - base_price) / base_price) * 100
            
            if change >= 5 or change <= -20:
                send_alert(symbol, change, price, volume)
                del tracked_coins[symbol]  # توقف عن التتبع

def job():
    try:
        print("\n" + "="*50)
        print(f"بدء المهمة: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"عدد العملات قيد التتبع: {len(tracked_coins)}")
        check_prices()
    except Exception as e:
        print(f"خطأ في المهمة: {e}")

if __name__ == "__main__":
    print("بدأ تشغيل بوت مراقبة MEXC مع تحسينات الأداء...")
    print(f"وضع التتبع: حجم 30K-700K$ | فحص كل 30 ثانية")
    
    # زيادة وتيرة الفحص إلى كل 30 ثانية
    schedule.every(30).seconds.do(job)
    
    # تشغيل المهمة فوراً عند البدء
    job()
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("إيقاف البوت...")
            break
