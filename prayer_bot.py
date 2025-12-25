import telebot
from telebot import types
from flask import Flask
from threading import Thread
import os
import time
import random
from datetime import datetime
from hijri_converter import convert
import pymongo
from pymongo import MongoClient
import requests

# --- 1. إعدادات الاتصال بقاعدة البيانات ---
# تأكد أن هذا الرابط هو الصحيح (الذي يحتوي على Omar12345)
MONGO_URL = "mongodb+srv://omarxazzam:Omar12345@azzam.o5lxlsj.mongodb.net/?retryWrites=true&w=majority&appName=AZZAM"

try:
    client = MongoClient(MONGO_URL)
    db = client['omar_bot_db']
    users_collection = db['users']
    print("✅ تم الاتصال بقاعدة البيانات بنجاح!")
except Exception as e:
    print(f"❌ فشل الاتصال بقاعدة البيانات: {e}")

# --- 2. إعدادات البوت والسيرفر ---
app = Flask('')
@app.route('/')
def home(): return "<b>Omar Smart Bot V8.0 (Auto Reminders) is Online! 🚀</b>"
def run(): app.run(host='0.0.0.0', port=8080)

def keep_alive(): 
    t = Thread(target=run)
    t.start()

TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

# --- 3. نظام التذكيرات التلقائية (الجديد) ---
def start_auto_reminders():
    # دالة التذكير بالصلاة على النبي (كل 30 دقيقة)
    def remind_prophet():
        while True:
            time.sleep(1800)  # انتظار 30 دقيقة (1800 ثانية)
            users = users_collection.find({})
            for user in users:
                try:
                    bot.send_message(user['_id'], "🌸 **تذكير:**\nاللهم صلِّ وسلم على نبينا محمد وعلى آله وصحبه أجمعين ﷺ")
                except: pass # تجاهل المستخدمين الذين حظروا البوت

    # دالة التذكير بذكر الله (كل 40 دقيقة)
    def remind_dhikr():
        while True:
            time.sleep(2400)  # انتظار 40 دقيقة (2400 ثانية)
            dhikr_list = [
                "✨ **ذكر الله:**\nلا إله إلا الله وحده لا شريك له.",
                "✨ **ذكر الله:**\nسبحان الله وبحمده، سبحان الله العظيم.",
                "✨ **ذكر الله:**\nأستغفر الله العظيم وأتوب إليه.",
                "✨ **ذكر الله:**\nلا حول ولا قوة إلا بالله العلي العظيم."
            ]
            msg = random.choice(dhikr_list)
            users = users_collection.find({})
            for user in users:
                try:
                    bot.send_message(user['_id'], msg, parse_mode="Markdown")
                except: pass

    # تشغيل المنبهات في خيوط منفصلة (Threads)
    t1 = Thread(target=remind_prophet)
    t2 = Thread(target=remind_dhikr)
    t1.start()
    t2.start()

# --- 4. بيانات الأذكار (الصباح والمساء) ---
MORNING_ADHKAR = [
    {"text": "اللّهُ لاَ إِلَـهَ إِلاَّ هُوَ الْحَيُّ الْقَيُّومُ...", "count": 1},
    {"text": "قُلْ هُوَ ٱللَّهُ أَحَدٌ... (3 مرات)", "count": 3},
    {"text": "قُلْ أَعُوذُ بِرَبِّ ٱلْفَلَقِ... (3 مرات)", "count": 3},
    {"text": "قُلْ أَعُوذُ بِرَبِّ ٱلنَّاسِ... (3 مرات)", "count": 3},
    {"text": "أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ...", "count": 1},
    {"text": "سُبْحَانَ اللهِ وَبِحَمْدِهِ. (100 مرة)", "count": 100},
    {"text": "يا حي يا قيوم برحمتك أستغيث...", "count": 1}
]

EVENING_ADHKAR = [
    {"text": "اللّهُ لاَ إِلَـهَ إِلاَّ هُوَ الْحَيُّ الْقَيُّومُ...", "count": 1},
    {"text": "قُلْ هُوَ ٱللَّهُ أَحَدٌ... (3 مرات)", "count": 3},
    {"text": "قُلْ أَعُوذُ بِرَبِّ ٱلْفَلَقِ... (3 مرات)", "count": 3},
    {"text": "قُلْ أَعُوذُ بِرَبِّ ٱلنَّاسِ... (3 مرات)", "count": 3},
    {"text": "أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ...", "count": 1},
    {"text": "أعوذ بكلمات الله التامات من شر ما خلق. (3 مرات)", "count": 3}
]

user_adhkar_state = {}

# --- 5. الوظائف المساعدة ---
def get_hijri_date():
    try:
        today = datetime.now()
        h = convert.Gregorian(today.year, today.month, today.day).to_hijri()
        return f"{h.day} {h.month_name()} {h.year}"
    except: return "غير متاح"

def get_prayer_timings():
    url = "http://api.aladhan.com/v1/timingsByCity"
    params = {'city': 'Cairo', 'country': 'Egypt', 'method': 5}
    try:
        response = requests.get(url, params=params, timeout=3).json()
        return response['data']['timings']
    except: return None

def calculate_delay(prayer_name, prayer_time_str):
    try:
        now = datetime.now()
        # تعديل الوقت ليكون بنفس تاريخ اليوم
        prayer_time = datetime.strptime(prayer_time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
        
        # لو الوقت الحالي قبل وقت الصلاة (تعديل بسيط للمنطق)
        if now < prayer_time:
            # قد يكون المستخدم يسجل صلاة الفجر قبل الشروق بقليل أو يسجل بأثر رجعي لليوم السابق
            # للتبسيط سنعتبرها في وقتها إذا كان الفارق بسيطاً
            return 0, "في وقتها ✅"

        diff = now - prayer_time
        minutes = int(diff.total_seconds() / 60)
        
        if minutes < 20: return minutes, "ممتاز! في أول الوقت 🥇"
        elif minutes < 60: return minutes, "جيد، تقبل الله 🥈"
        else:
            h = minutes // 60
            m = minutes % 60
            return minutes, f"تأخير {h} ساعة و {m} دقيقة ⚠️"
    except: return 0, "تم التسجيل"

# --- 6. وظائف قاعدة البيانات ---
def register_user(chat_id, name):
    cid = str(chat_id)
    if not users_collection.find_one({"_id": cid}):
        users_collection.insert_one({
            "_id": cid, "name": name, 
            "join_date": datetime.now().strftime("%Y-%m-%d"), 
            "points": 0
        })

# --- 7. القوائم والتفاعل ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("🕌 مواقيت الصلاة"), types.KeyboardButton("📝 تسجيل العبادات"))
    markup.add(types.KeyboardButton("☀️ أذكار الصباح"), types.KeyboardButton("🌙 أذكار المساء"))
    markup.add(types.KeyboardButton("🏆 إحصائياتي"), types.KeyboardButton("💡 حديث عشوائي"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    register_user(message.chat.id, message.from_user.first_name)
    bot.send_message(message.chat.id, f"أهلاً بك يا **{message.from_user.first_name}** 👋\n\nتم تفعيل التذكيرات التلقائية (كل 30 و 40 دقيقة) ⏳", reply_markup=main_menu(), parse_mode="Markdown")

# --- معالجة الأذكار (العداد) ---
def send_dhikr(chat_id, dhikr_type, index):
    lst = MORNING_ADHKAR if dhikr_type == "morning" else EVENING_ADHKAR
    if index >= len(lst):
        bot.send_message(chat_id, "🎉 **تم بحمد الله!**", parse_mode="Markdown")
        if chat_id in user_adhkar_state: del user_adhkar_state[chat_id]
        return

    dhikr = lst[index]
    user_adhkar_state[chat_id] = {'type': dhikr_type, 'index': index, 'count': dhikr['count']}
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"📿 تكرار: {dhikr['count']}", callback_data="cnt"))
    if index > 0: markup.add(types.InlineKeyboardButton("⬅️ السابق", callback_data="prev"))
    
    title = "☀️ الصباح" if dhikr_type == "morning" else "🌙 المساء"
    bot.send_message(chat_id, f"**{title} ({index+1}/{len(lst)})**\n\n{dhikr['text']}", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "cnt")
def count_dhikr_btn(call):
    cid = call.message.chat.id
    if cid not in user_adhkar_state: return
    
    st = user_adhkar_state[cid]
    st['count'] -= 1
    
    if st['count'] > 0:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"📿 تكرار: {st['count']}", callback_data="cnt"))
        if st['index'] > 0: markup.add(types.InlineKeyboardButton("⬅️ السابق", callback_data="prev"))
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=markup)
    else:
        bot.delete_message(cid, call.message.message_id)
        send_dhikr(cid, st['type'], st['index'] + 1)

@bot.callback_query_handler(func=lambda call: call.data == "prev")
def prev_dhikr_btn(call):
    cid = call.message.chat.id
    if cid in user_adhkar_state:
        st = user_adhkar_state[cid]
        bot.delete_message(cid, call.message.message_id)
        send_dhikr(cid, st['type'], st['index'] - 1)

# --- معالجة الأوامر ---
@bot.message_handler(func=lambda m: True)
def handle_all(m):
    text = m.text
    cid = m.chat.id
    
    if text == "☀️ أذكار الصباح": send_dhikr(cid, "morning", 0)
    elif text == "🌙 أذكار المساء": send_dhikr(cid, "evening", 0)
    
    elif text == "📝 تسجيل العبادات":
        markup = types.InlineKeyboardMarkup(row_width=3)
        btns = [types.InlineKeyboardButton(n, callback_data=f"rec_{e}") for n,e in [("الفجر","Fajr"),("الظهر","Dhuhr"),("العصر","Asr"),("المغرب","Maghrib"),("العشاء","Isha")]]
        markup.add(*btns)
        bot.reply_to(m, "ماذا صليت؟", reply_markup=markup)
        
    elif text == "🕌 مواقيت الصلاة":
        t = get_prayer_timings()
        if t:
            msg = f"🕌 **مواقيت الصلاة:**\n"
            for k in ['Fajr','Dhuhr','Asr','Maghrib','Isha']: msg += f"🔹 {k}: {t[k]}\n"
            bot.reply_to(m, msg)
            
    elif text == "🏆 إحصائياتي":
        u = users_collection.find_one({"_id": str(cid)})
        p = u.get('points', 0) if u else 0
        bot.reply_to(m, f"🏅 نقاطك: {p}")
        
    elif text == "💡 حديث عشوائي":
        bot.reply_to(m, f"💡 {random.choice(['الدين النصيحة', 'المسلم من سلم المسلمون من لسانه ويده'])}")

@bot.callback_query_handler(func=lambda c: c.data.startswith('rec_'))
def rec_prayer(c):
    cid = str(c.message.chat.id)
    p_name = c.data.split('_')[1]
    
    t = get_prayer_timings()
    delay, msg = calculate_delay(p_name, t[p_name]) if t else (0, "تم التسجيل")
    
    dt = datetime.now().strftime("%Y-%m-%d")
    users_collection.update_one({"_id": cid}, 
        {"$set": {f"prayers.{dt}.{p_name}": {"time": datetime.now().strftime("%H:%M"), "delay": delay}}, 
         "$inc": {"points": 10}}, upsert=True)
         
    bot.edit_message_text(f"✅ تم تسجيل {p_name}\n⏱️ {msg}\n💰 +10 نقاط", c.message.chat.id, c.message.message_id)

# --- 8. التشغيل ---
if __name__ == "__main__":
    keep_alive()          # تشغيل سيرفر الويب
    start_auto_reminders() # تشغيل التذكيرات التلقائية (الجديد)
    bot.infinity_polling()
