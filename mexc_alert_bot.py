import os
import time
import requests
import schedule
from datetime import datetime

# إعدادات البوت
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
BASE_URL = "https://api.mexc.com/api/v3"

# معايير التتبع
VOLUME_MIN = 50000
VOLUME_MAX = 700000
PRICE_CHANGE_UP = 5
PRICE_CHANGE_DOWN = 20
VOLUME_CHANGE = 2000

# تخزين البيانات
coin_history = {}

def send_telegram(message):
    """إرسال رسالة عبر Telegram API مباشرة"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {
        'chat_id': CHAT_ID,
        'text': message
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            print(f"تم إرسال الإشعار: {message[:50]}...")
        else:
            print(f"فشل إرسال الإشعار: {response.status_code}")
    except Exception as e:
        print(f"خطأ في إرسال الإشعار: {e}")

def get_coin_data(symbol):
    """الحصول على بيانات العملة"""
    try:
        response = requests.get(f"{BASE_URL}/ticker/24hr?symbol={symbol}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def check_coins():
    """فحص جميع العملات"""
    try:
        response = requests.get(f"{BASE_URL}/ticker/24hr", timeout=10)
        coins = response.json() if response.status_code == 200 else []
        return coins
    except:
        return []

def monitor():
    """المراقبة الرئيسية"""
    coins = check_coins()
    if not coins:
        print("لم يتم الحصول على بيانات العملات")
        return
    
    current_time = datetime.now()
    
    for coin in coins:
        symbol = coin['symbol']
        try:
            volume = float(coin['quoteVolume'])
            price = float(coin['lastPrice'])
        except:
            continue
            
        # تصفية حسب حجم التداول
        if VOLUME_MIN <= volume <= VOLUME_MAX:
            # إذا كانت العملة جديدة
            if symbol not in coin_history:
                coin_history[symbol] = {
                    'price': price,
                    'volume': volume,
                    'time': current_time
                }
                continue
                
            # حساب التغيرات
            prev = coin_history[symbol]
            price_change = ((price - prev['price']) / prev['price']) * 100
            volume_change = volume - prev['volume']
            
            # إشعار تغير السعر
            if price_change >= PRICE_CHANGE_UP:
                message = f"🚀 صعود {price_change:.2f}% في 5 دقائق\n"
                message += f"العملة: {symbol}\n"
                message += f"السعر: {price}\n"
                message += f"الحجم: ${volume:,.0f}"
                send_telegram(message)
                
            elif price_change <= -PRICE_CHANGE_DOWN:
                message = f"🔻 هبوط {abs(price_change):.2f}% في 5 دقائق\n"
                message += f"العملة: {symbol}\n"
                message += f"السعر: {price}\n"
                message += f"الحجم: ${volume:,.0f}"
                send_telegram(message)
                
            # إشعار تغير الحجم
            if volume_change >= VOLUME_CHANGE:
                message = f"📈 زيادة حجم +${volume_change:,.0f}\n"
                message += f"العملة: {symbol}\n"
                message += f"الحجم الجديد: ${volume:,.0f}\n"
                message += f"السعر: {price}"
                send_telegram(message)
            
            # تحديث البيانات
            coin_history[symbol] = {
                'price': price,
                'volume': volume,
                'time': current_time
            }

def job():
    """المهمة المجدولة"""
    print(f"\n{datetime.now().strftime('%H:%M:%S')} - بدء الفحص")
    monitor()

if __name__ == "__main__":
    print("بدأ تشغيل بوت مراقبة MEXC...")
    print(f"حجم التداول: ${VOLUME_MIN:,.0f}-${VOLUME_MAX:,.0f}")
    print(f"تغير السعر: +{PRICE_CHANGE_UP}% / -{PRICE_CHANGE_DOWN}%")
    print(f"تغير الحجم: +${VOLUME_CHANGE:,.0f}")
    
    # تشغيل كل 5 دقائق
    schedule.every(5).minutes.do(job)
    
    # تشغيل فوري
    job()
    
    while True:
        schedule.run_pending()
        time.sleep(1)
