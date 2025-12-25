import telebot
from telebot import types
from flask import Flask
from threading import Thread
import os
import random
import time
from datetime import datetime
from hijri_converter import convert
import pymongo
from pymongo import MongoClient

# --- 1. إعدادات الاتصال بقاعدة البيانات (MongoDB) ---
# هذا هو الرابط السحري الخاص بك
MONGO_URL = "mongodb+srv://omarxazzam_db_user:Vg4JEVwQUdqkvBaP@azzam.o5lxlsj.mongodb.net/?retryWrites=true&w=majority&appName=AZZAM"

try:
    # محاولة الاتصال بالقاعدة
    client = MongoClient(MONGO_URL)
    db = client['omar_bot_db']  # اسم قاعدة البيانات
    users_collection = db['users']  # جدول المستخدمين
    print("✅ تم الاتصال بقاعدة البيانات بنجاح!")
except Exception as e:
    print(f"❌ فشل الاتصال بقاعدة البيانات: {e}")

# --- 2. إعدادات البوت والسيرفر ---
app = Flask('')

@app.route('/')
def home():
    return "<b>Omar Smart Bot V6.0 (Database Edition) is Online! 🚀</b>"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

# --- 3. وظائف التعامل مع البيانات (Database Functions) ---

def register_user(chat_id, first_name):
    """تسجيل مستخدم جديد في قاعدة البيانات أو تحديث بياناته"""
    cid = str(chat_id)
    now = datetime.now().strftime("%Y-%m-%d")
    
    # البحث عن المستخدم
    user = users_collection.find_one({"_id": cid})
    
    if not user:
        # إذا كان مستخدماً جديداً، ننشئ له ملفاً
        new_user = {
            "_id": cid,
            "name": first_name,
            "join_date": now,
            "points": 0,
            "prayers": {}  # سجل الصلوات
        }
        users_collection.insert_one(new_user)
        print(f"🆕 مستخدم جديد: {first_name}")
    else:
        # إذا كان موجوداً، فقط نحدث الاسم وتاريخ آخر ظهور
        users_collection.update_one({"_id": cid}, {"$set": {"last_active": now, "name": first_name}})

def record_prayer(chat_id, prayer_name):
    """تسجيل صلاة للمستخدم وزيادة نقاطه"""
    cid = str(chat_id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # المفتاح داخل قاعدة البيانات: prayers.2023-10-25.Fajr
    key = f"prayers.{today}.{prayer_name}"
    
    # التحقق هل سجلها سابقاً اليوم؟
    user = users_collection.find_one({"_id": cid})
    if user and 'prayers' in user and today in user['prayers'] and prayer_name in user['prayers'][today]:
        return False # مسجلة مسبقاً

    # تحديث القاعدة: وضع علامة صح للصلاة + زيادة 10 نقاط
    users_collection.update_one(
        {"_id": cid},
        {
            "$set": {key: True},
            "$inc": {"points": 10}
        },
        upsert=True
    )
    return True

def get_user_stats(chat_id):
    """جلب إحصائيات المستخدم من القاعدة"""
    user = users_collection.find_one({"_id": str(chat_id)})
    if not user:
        return 0, 0
    points = user.get('points', 0)
    # حساب عدد الصلوات المسجلة
    total_prayers = 0
    prayers_data = user.get('prayers', {})
    for day in prayers_data:
        total_prayers += len(prayers_data[day])
    return points, total_prayers

# --- 4. الوظائف المساعدة ---
def get_hijri_date():
    today = datetime.now()
    h = convert.Gregorian(today.year, today.month, today.day).to_hijri()
    return f"{h.day} {h.month_name()} {h.year}"

def get_prayers_raw():
    import requests
    url = "http://api.aladhan.com/v1/timingsByCity"
    params = {'city': 'Cairo', 'country': 'Egypt', 'method': 5}
    try:
        response = requests.get(url, params=params, timeout=3)
        return response.json()['data']['timings']
    except:
        return None

def convert_to_12h(time24):
    try:
        t = datetime.strptime(time24, "%H:%M")
        return t.strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")
    except:
        return time24

# --- 5. القوائم والتفاعل ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("🕌 مواقيت الصلاة"), types.KeyboardButton("📅 التاريخ الهجري"))
    markup.add(types.KeyboardButton("📝 تسجيل صلاة"), types.KeyboardButton("🏆 نقاطي وإحصائياتي"))
    markup.add(types.KeyboardButton("💡 حديث عشوائي"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    register_user(message.chat.id, message.from_user.first_name)
    welcome_msg = (
        f"أهلاً بك يا **{message.from_user.first_name}** في بوت عُمر الذكي (نسخة السحابة) ☁️\n\n"
        f"📅 التاريخ: {get_hijri_date()}\n"
        f"✅ الآن يتم حفظ عباداتك في قاعدة بيانات آمنة للأبد!"
    )
    bot.send_message(message.chat.id, welcome_msg, reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    text = message.text
    chat_id = message.chat.id
    
    # تأكيد التسجيل عند كل رسالة لضمان وجود البيانات
    register_user(chat_id, message.from_user.first_name)

    if text == "📅 التاريخ الهجري":
        bot.reply_to(message, f"📅 **التاريخ اليوم:**\n{get_hijri_date()}", parse_mode="Markdown")

    elif text == "🕌 مواقيت الصلاة":
        timings = get_prayers_raw()
        if timings:
            msg = f"🕌 **مواقيت الصلاة ({get_hijri_date()}):**\n\n"
            for p in ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
                ar_name = {'Fajr':'الفجر','Dhuhr':'الظهر','Asr':'العصر','Maghrib':'المغرب','Isha':'العشاء'}.get(p)
                msg += f"🔹 {ar_name}: `{convert_to_12h(timings[p])}`\n"
            bot.reply_to(message, msg, parse_mode="Markdown")
        else:
            bot.reply_to(message, "عذراً، تعذر جلب المواقيت.")

    elif text == "🏆 نقاطي وإحصائياتي":
        points, total_prayers = get_user_stats(chat_id)
        msg = (
            f"🏆 **لوحة الشرف الخاصة بك:**\n\n"
            f"💰 النقاط الحالية: **{points}**\n"
            f"🧎‍♂️ الصلوات المسجلة: **{total_prayers}**\n\n"
            f"استمر في الطاعة لزيادة رصيدك عند الله ثم هنا! ❤️"
        )
        bot.reply_to(message, msg, parse_mode="Markdown")

    elif text == "📝 تسجيل صلاة":
        markup = types.InlineKeyboardMarkup(row_width=3)
        btns = [
            types.InlineKeyboardButton("الفجر", callback_data="rec_Fajr"),
            types.InlineKeyboardButton("الظهر", callback_data="rec_Dhuhr"),
            types.InlineKeyboardButton("العصر", callback_data="rec_Asr"),
            types.InlineKeyboardButton("المغرب", callback_data="rec_Maghrib"),
            types.InlineKeyboardButton("العشاء", callback_data="rec_Isha"),
        ]
        markup.add(*btns)
        bot.reply_to(message, "ما هي الصلاة التي صليتها الآن؟", reply_markup=markup)
        
    elif text == "💡 حديث عشوائي":
        h = [
            "قال ﷺ: (من صلى البردين دخل الجنة).",
            "قال ﷺ: (الصلوات الخمس كفارة لما بينهن ما لم تغش الكبائر).",
            "قال ﷺ: (أقرب ما يكون العبد من ربه وهو ساجد)."
        ]
        bot.reply_to(message, f"💡 **حديث شريف:**\n\n{random.choice(h)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('rec_'))
def callback_record(call):
    prayer_code = call.data.split('_')[1] # استخراج اسم الصلاة
    ar_names = {'Fajr':'الفجر','Dhuhr':'الظهر','Asr':'العصر','Maghrib':'المغرب','Isha':'العشاء'}
    prayer_name = ar_names.get(prayer_code, prayer_code)
    
    # محاولة التسجيل في قاعدة البيانات
    success = record_prayer(call.message.chat.id, prayer_code)
    
    if success:
        bot.answer_callback_query(call.id, f"✅ تم تسجيل صلاة {prayer_name} (+10 نقاط)")
        bot.edit_message_text(f"✅ **تم تسجيل صلاة {prayer_name} بنجاح!**\nجزاك الله خيراً وزادك من فضله.", 
                              call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    else:
        bot.answer_callback_query(call.id, "⚠️ هذه الصلاة مسجلة مسبقاً لهذا اليوم!", show_alert=True)

# --- 6. تشغيل السيرفر ---
if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
