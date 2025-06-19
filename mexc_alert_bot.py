import os
import time
import requests
import schedule
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

# إعدادات البوت
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
bot = Bot(token=TELEGRAM_TOKEN) if TELEGRAM_TOKEN else None

BASE_URL = "https://api.mexc.com/api/v3"
VOLUME_MIN = 50000  # الحد الأدنى للحجم (50,000 دولار)
VOLUME_MAX = 700000  # الحد الأقصى للحجم (700,000 دولار)
VOLUME_CHANGE_THRESHOLD = 2000  # تغير حجم التداول (2,000 دولار)
PRICE_CHANGE_THRESHOLD_UP = 5  # تغير السعر للأعلى (5%)
PRICE_CHANGE_THRESHOLD_DOWN = 20  # تغير السعر للأسفل (20%)

# تخزين البيانات التاريخية
coin_history = {}

def get_5min_data(symbol):
    """الحصول على بيانات السعر والحجم للـ 5 دقائق الأخيرة"""
    try:
        # نهاية الفترة الزمنية (الآن)
        end_time = int(time.time() * 1000)
        # بداية الفترة الزمنية (قبل 5 دقائق)
        start_time = end_time - 5 * 60 * 1000
        
        params = {
            'symbol': symbol,
            'interval': '5m',
            'startTime': start_time,
            'endTime': end_time,
            'limit': 1
        }
        
        response = requests.get(f"{BASE_URL}/klines", params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                # [وقت الفتح, سعر الفتح, سعر الأعلى, سعر الأدنى, سعر الإغلاق, حجم التداول]
                return {
                    'open_time': data[0][0],
                    'open_price': float(data[0][1]),
                    'high_price': float(data[0][2]),
                    'low_price': float(data[0][3]),
                    'close_price': float(data[0][4]),
                    'volume': float(data[0][5])
                }
        return None
    except:
        return None

def get_coins():
    """الحصول على بيانات جميع العملات"""
    try:
        response = requests.get(f"{BASE_URL}/ticker/24hr", timeout=10)
        return response.json() if response.status_code == 200 else []
    except:
        return []

def send_alert(message):
    """إرسال إشعار عبر Telegram"""
    if bot:
        try:
            bot.send_message(chat_id=CHAT_ID, text=message)
            print(f"تم إرسال إشعار: {message[:50]}...")
        except TelegramError as e:
            print(f"خطأ في إرسال الإشعار: {e}")
    else:
        print(f"بدون إرسال: {message}")

def check_price_and_volume():
    """فحص تغيرات الأسعار وحجم التداول خلال 5 دقائق"""
    coins = get_coins()
    if not coins: 
        print("لم يتم الحصول على بيانات العملات")
        return
    
    current_time = datetime.now()
    
    for coin in coins:
        symbol = coin['symbol']
        volume_24h = float(coin['quoteVolume'])
        current_price = float(coin['lastPrice'])
        
        # تصفية العملات حسب حجم التداول اليومي
        if VOLUME_MIN <= volume_24h <= VOLUME_MAX:
            # الحصول على بيانات الـ 5 دقائق الأخيرة
            kline_data = get_5min_data(symbol)
            if not kline_data:
                continue
                
            # إذا كانت العملة جديدة في التتبع
            if symbol not in coin_history:
                coin_history[symbol] = {
                    'price': kline_data['open_price'],
                    'volume': kline_data['volume'],
                    'timestamp': current_time
                }
                continue
                
            # حساب التغيرات خلال 5 دقائق
            prev_data = coin_history[symbol]
            price_change = ((current_price - prev_data['price']) / prev_data['price']) * 100
            volume_change = kline_data['volume'] - prev_data['volume']
            
            # 1. إشعارات تغير السعر
            if price_change >= PRICE_CHANGE_THRESHOLD_UP:
                message = f"🚀 صعود حاد خلال 5 دقائق ({price_change:.2f}%)\n"
                message += f"العملة: {symbol}\n"
                message += f"السعر الحالي: {current_price}\n"
                message += f"السعر السابق: {prev_data['price']}\n"
                message += f"الحجم (24h): ${volume_24h:,.0f}"
                send_alert(message)
                
            elif price_change <= -PRICE_CHANGE_THRESHOLD_DOWN:
                message = f"🔻 هبوط حاد خلال 5 دقائق ({abs(price_change):.2f}%)\n"
                message += f"العملة: {symbol}\n"
                message += f"السعر الحالي: {current_price}\n"
                message += f"السعر السابق: {prev_data['price']}\n"
                message += f"الحجم (24h): ${volume_24h:,.0f}"
                send_alert(message)
                
            # 2. إشعارات تغير حجم التداول
            if volume_change >= VOLUME_CHANGE_THRESHOLD:
                message = f"📈 زيادة كبيرة في الحجم خلال 5 دقائق (+${volume_change:,.0f})\n"
                message += f"العملة: {symbol}\n"
                message += f"الحجم السابق: ${prev_data['volume']:,.0f}\n"
                message += f"الحجم الحالي: ${kline_data['volume']:,.0f}\n"
                message += f"الحجم (24h): ${volume_24h:,.0f}"
                send_alert(message)
                
            # تحديث البيانات التاريخية
            coin_history[symbol] = {
                'price': kline_data['open_price'],
                'volume': kline_data['volume'],
                'timestamp': current_time
            }

def job():
    """المهمة المجدولة"""
    try:
        print(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - بدء الفحص")
        check_price_and_volume()
    except Exception as e:
        print(f"خطأ في المهمة: {e}")

if __name__ == "__main__":
    print("بدأ تشغيل بوت مراقبة MEXC للأسعار وحجم التداول...")
    print(f"شروط التتبع: حجم ${VOLUME_MIN:,.0f}-${VOLUME_MAX:,.0f}")
    print(f"تغير السعر خلال 5 دقائق: +{PRICE_CHANGE_THRESHOLD_UP}% / -{PRICE_CHANGE_THRESHOLD_DOWN}%")
    print(f"تغير الحجم خلال 5 دقائق: +${VOLUME_CHANGE_THRESHOLD:,.0f}")
    
    # جدولة المهمة كل 5 دقائق
    schedule.every(5).minutes.do(job)
    
    # تشغيل المهمة فوراً عند البدء
    job()
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("إيقاف البوت...")
            break
