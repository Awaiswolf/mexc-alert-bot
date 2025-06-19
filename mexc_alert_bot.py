import os
import time
import requests
import schedule
from telegram import Bot
from telegram.error import TelegramError

# إعدادات البوت
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
bot = Bot(token=TELEGRAM_TOKEN) if TELEGRAM_TOKEN else None

BASE_URL = "https://api.mexc.com/api/v3"
tracked_coins = {}

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
    if not coins: return
    
    for coin in coins:
        symbol = coin['symbol']
        volume = float(coin['quoteVolume'])
        price = float(coin['lastPrice'])
        
        # تصفية العملات الجديدة
        if 50000 <= volume <= 600000 and symbol not in tracked_coins:
            tracked_coins[symbol] = price
            print(f"بدأ تتبع: {symbol} | السعر: {price}")
        
        # التحقق من التغيرات
        elif symbol in tracked_coins:
            base_price = tracked_coins[symbol]
            change = ((price - base_price) / base_price) * 100
            
            if change >= 5 or change <= -20:
                send_alert(symbol, change, price, volume)
                del tracked_coins[symbol]  # توقف عن التتبع

def job():
    try:
        check_prices()
    except Exception as e:
        print(f"خطأ في المهمة: {e}")

if __name__ == "__main__":
    print("بدأ تشغيل بوت مراقبة MEXC...")
    schedule.every(1).minutes.do(job)
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(30)
        except KeyboardInterrupt:
            print("إيقاف البوت...")
            break
