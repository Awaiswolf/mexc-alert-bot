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
VOLUME_MIN = 50000    # الحد الأدنى لحجم التداول اليومي (50,000 دولار)
VOLUME_MAX = 550000   # الحد الأقصى لحجم التداول اليومي (550,000 دولار)
PRICE_CHANGE_UP = 5   # نسبة الصعود للإشعار (5%)
PRICE_CHANGE_DOWN = 30 # نسبة الهبوط للإشعار (30%)
VOLUME_CHANGE = 20000 # زيادة حجم التداول للإشعار (20,000 دولار)

# تخزين البيانات
coin_history = {}

def format_price(price_str):
    """تنسيق السعر لإظهار جميع الأصفار"""
    try:
        # تحويل السعر إلى عدد عشري
        price = float(price_str)
        
        # إذا كان السعر صغير جداً، نستخدم التنسيق العلمي مع إزالة أي تقريب
        if abs(price) < 0.0001:
            return format(price, '.20f').rstrip('0').rstrip('.')
        else:
            return str(price)
    except:
        return price_str

def send_telegram(message):
    """إرسال رسالة عبر Telegram API مباشرة"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'  # استخدام HTML للخط العريض
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
    
    for index, coin in enumerate(coins):
        symbol = coin['symbol']
        try:
            volume = float(coin['quoteVolume'])
            price_str = coin['lastPrice']  # الاحتفاظ بالسعر كسلسلة نصية لتجنب فقدان الأصفار
            price = float(price_str)
        except:
            continue
            
        # إضافة تأخير لتجنب حظر الطلبات
        if index % 10 == 0 and index > 0:
            time.sleep(0.5)  # تأخير 0.5 ثانية بعد كل 10 عملات
            
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
                formatted_price = format_price(price_str)
                message = "🚀🚀🚀🚀🚀🌚🌚🚀🚀🚀🚀🚀\n"
                message += "<b>صعود</b> {:.2f}% في 5 دقائق\n".format(price_change)
                message += "----------------------------------------------------\n"
                message += f"العملة: <b>{symbol}</b>\n"
                message += "----------------------------------------------------\n"
                message += f"السعر: {formatted_price}\n"
                message += "----------------------------------------------------\n"
                message += f"الحجم: ${volume:,.0f}"
                message = "بيع ولا تخلي اسمك يضيع 😎\n"
                send_telegram(message)
                
            elif price_change <= -PRICE_CHANGE_DOWN:
                formatted_price = format_price(price_str)
                message = "🔻🔻🔻🔻🔻🔻🩸🩸🩸🩸🩸🩸\n"
                message += "<b>هبوط</b> {:.2f}% في 5 دقائق\n".format(abs(price_change))
                message += "----------------------------------------------------\n"
                message += f"العملة: <b>{symbol}</b>\n"
                message += "----------------------------------------------------\n"
                message += f"السعر: {formatted_price}\n"
                message += "----------------------------------------------------\n"
                message += f"الحجم: ${volume:,.0f}"
                message = "بيع ولا تخلي اسمك يضيع 😎\n"
                send_telegram(message)
                
            # إشعار تغير الحجم
            if volume_change >= VOLUME_CHANGE:
                formatted_price = format_price(price_str)
                message = "📈📈📈📈📈📈📈📈📈📈📈📈\n"
                message += "<b>زيادة</b> حجم +${:,.0f}\n".format(volume_change)
                message += "----------------------------------------------------\n"
                message += f"العملة: <b>{symbol}</b>\n"
                message += "----------------------------------------------------\n"
                message += f"الحجم الجديد: ${volume:,.0f}\n"
                message += "----------------------------------------------------\n"
                message += f"السعر: {formatted_price}"
                message = "بيع ولا تخلي اسمك يضيع 😎\n"
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
