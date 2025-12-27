import telebot
from telebot import types
from flask import Flask
from threading import Thread
import os
import time
import random
from datetime import datetime, timedelta
import pymongo
from pymongo import MongoClient
import requests
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- 1. إعدادات المفاتيح والاتصال ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
MONGO_URL = "mongodb+srv://omarxazzam:Omar12345@azzam.o5lxlsj.mongodb.net/?retryWrites=true&w=majority&appName=AZZAM"

# تهيئة الذكاء الاصطناعي (مع إلغاء الفلاتر)
try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # إعدادات الشخصية
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "max_output_tokens": 1000,
        }
        
        # 🟢 إعدادات الأمان (مهمة جداً لمنع الأخطاء)
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        print("✅ تم تفعيل الذكاء الاصطناعي (بدون قيود) بنجاح!")
    else:
        model = None
except Exception as e:
    print(f"⚠️ مشكلة AI: {e}")
    model = None

# الاتصال بقاعدة البيانات
try:
    client = MongoClient(MONGO_URL)
    db = client['omar_bot_db']
    users_collection = db['users']
except Exception as e: pass

# --- 2. البيانات والنصوص ---
GOOD_MSGS = ["يا مقلب القلوب ثبت قلبي.", "استمر يا بطل.", "ما شاء الله.", "أحب الأعمال أدومها.", "بيض الله وجهك."]
BAD_MSGS = ["جاهد نفسك.", "ألم يأن للذين آمنوا؟", "تدارك نفسك.", "الصلاة هي الصلة."]

# (الأذكار مختصرة هنا للعرض فقط، لكن انسخ قوائمك الكاملة السابقة كما هي)
MORNING_ADHKAR = [
    {"text": "أعوذ بالله من الشيطان الرجيم\n💎 **آية الكرسي:**\n{اللّهُ لاَ إِلَـهَ إِلاَّ هُوَ الْحَيُّ الْقَيُّومُ... (اقرأها كاملة)}", "count": 1},
    {"text": "💎 **سورة الإخلاص (3 مرات)**", "count": 3},
    {"text": "💎 **سورة الفلق (3 مرات)**", "count": 3},
    {"text": "💎 **سورة الناس (3 مرات)**", "count": 3},
    {"text": "أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ...", "count": 1},
    {"text": "اللَّهُمَّ بِكَ أَصْبَحْنَا...", "count": 1},
    {"text": "سيد الاستغفار...", "count": 1},
    {"text": "سُبْحَانَ اللهِ وَبِحَمْدِهِ (10 مرات).", "count": 10},
    {"text": "يا حي يا قيوم...", "count": 1}
]
EVENING_ADHKAR = [
    {"text": "أعوذ بالله من الشيطان الرجيم\n💎 **آية الكرسي:**\n{اللّهُ لاَ إِلَـهَ إِلاَّ هُوَ الْحَيُّ الْقَيُّومُ...}", "count": 1},
    {"text": "💎 **الإخلاص والمعوذتين (3 مرات)**", "count": 3},
    {"text": "أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ...", "count": 1},
    {"text": "اللَّهُمَّ بِكَ أَمْسَيْنَا...", "count": 1},
    {"text": "أعوذ بكلمات الله التامات...", "count": 3},
    {"text": "بسم الله الذي لا يضر...", "count": 3},
    {"text": "رضيت بالله ربا...", "count": 3}
]
SLEEP_ADHKAR = [
    {"text": "🛏️ **آية الكرسي**", "count": 1},
    {"text": "🛏️ **الإخلاص والمعوذتين (3 مرات)**", "count": 3},
    {"text": "باسمك اللهم أموت وأحيا.", "count": 1},
    {"text": "اللهم أسلمت نفسي إليك...", "count": 1},
    {"text": "التسبيح (33)، التحميد (33)، التكبير (34).", "count": 1}
]

# --- 3. السيرفر ---
app = Flask('')
@app.route('/')
def home(): return "<b>Omar Smart Bot V22.0 (Debug Mode) is Online! 🚀</b>"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): t = Thread(target=run); t.start()

TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)
user_adhkar_state = {}

# --- 4. الوظائف ---
def get_cairo_time(): return datetime.utcnow() + timedelta(hours=2)
def convert_to_12h(t):
    try: return datetime.strptime(t, "%H:%M").strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")
    except: return t
def get_prayer_timings():
    try: return requests.get("http://api.aladhan.com/v1/timingsByCity?city=Cairo&country=Egypt&method=5", timeout=3).json()['data']['timings']
    except: return None
def get_next_prayer_info():
    t = get_prayer_timings()
    if not t: return "تعذر جلب المواقيت."
    now = get_cairo_time()
    for k, v in [('Fajr','الفجر'),('Dhuhr','الظهر'),('Asr','العصر'),('Maghrib','المغرب'),('Isha','العشاء')]:
        pt = datetime.strptime(t[k], "%H:%M").replace(year=now.year, month=now.month, day=now.day)
        if pt > now:
            d = pt - now
            return f"⏳ **الصلاة القادمة:** {v}\n⏱️ **متبقي:** {d.seconds//3600} ساعة و {(d.seconds%3600)//60} دقيقة"
    return "⏳ **الصلاة القادمة:** الفجر (غداً)"

def start_auto_reminders():
    def remind():
        while True:
            time.sleep(1800)
            try:
                for u in users_collection.find({}):
                    bot.send_message(u['_id'], "🌸 صلِّ على النبي ﷺ")
            except: pass
    Thread(target=remind).start()

def get_today_report(chat_id):
    now = get_cairo_time()
    today = now.strftime("%Y-%m-%d")
    u = users_collection.find_one({"_id": str(chat_id)})
    if not u: return "لا بيانات."
    done = u.get('prayers', {}).get(today, {})
    msg = f"📅 **تقرير {today}:**\n"
    c = 0
    for k in ['Fajr','Dhuhr','Asr','Maghrib','Isha']:
        if k in done:
            msg += "✅\n"
            c += 1
        else: msg += "❌\n"
    msg += f"\n{random.choice(GOOD_MSGS) if c>=3 else random.choice(BAD_MSGS)}"
    return msg

# --- 5. التفاعل ---
def main_menu():
    m = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    m.add("⏳ كم باقي على الصلاة؟", "🕌 مواقيت الصلاة", "📝 تسجيل العبادات", "☀️ أذكار الصباح", "🌙 أذكار المساء", "😴 أذكار النوم", "📊 تقريري اليومي")
    return m

@bot.message_handler(commands=['start'])
def start(m):
    cid = str(m.chat.id)
    if not users_collection.find_one({"_id": cid}):
        users_collection.insert_one({"_id": cid, "name": m.from_user.first_name, "join_date": get_cairo_time().strftime("%Y-%m-%d")})
    bot.send_message(m.chat.id, f"أهلاً {m.from_user.first_name} 👋\n\n{get_next_prayer_info()}", reply_markup=main_menu(), parse_mode="Markdown")

def send_dhikr(chat_id, type_d, idx):
    if type_d == "morning": lst = MORNING_ADHKAR
    elif type_d == "evening": lst = EVENING_ADHKAR
    else: lst = SLEEP_ADHKAR
    if idx >= len(lst):
        bot.send_message(chat_id, "🎉 تم بحمد الله!")
        if chat_id in user_adhkar_state: del user_adhkar_state[chat_id]
        return
    user_adhkar_state[chat_id] = {'type': type_d, 'index': idx, 'count': lst[idx]['count']}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"📿 {lst[idx]['count']}", callback_data="cnt"))
    bot.send_message(chat_id, lst[idx]['text'], reply_markup=markup) # Removed Parse Mode here too just in case

@bot.callback_query_handler(func=lambda c: c.data == "cnt")
def count(c):
    cid = c.message.chat.id
    if cid not in user_adhkar_state: return
    st = user_adhkar_state[cid]
    st['count'] -= 1
    if st['count'] > 0:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"📿 {st['count']}", callback_data="cnt"))
        bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=markup)
    else:
        bot.delete_message(cid, c.message.message_id)
        send_dhikr(cid, st['type'], st['index'] + 1)

@bot.callback_query_handler(func=lambda c: c.data.startswith('rec_'))
def rec(c):
    cid = str(c.message.chat.id)
    p = c.data.split('_')[1]
    dt = get_cairo_time().strftime("%Y-%m-%d")
    users_collection.update_one({"_id": cid}, {"$set": {f"prayers.{dt}.{p}": {"time": get_cairo_time().strftime("%H:%M")}}}, upsert=True)
    bot.edit_message_text(f"✅ تم {p}", c.message.chat.id, c.message.message_id)

# --- 6. الدالة الذكية (Handle All) ---
@bot.message_handler(func=lambda m: True)
def handle_all(m):
    t = m.text
    cid = m.chat.id
    if t == "⏳ كم باقي على الصلاة؟": bot.reply_to(m, get_next_prayer_info(), parse_mode="Markdown")
    elif t == "☀️ أذكار الصباح": send_dhikr(cid, "morning", 0)
    elif t == "🌙 أذكار المساء": send_dhikr(cid, "evening", 0)
    elif t == "😴 أذكار النوم": send_dhikr(cid, "sleep", 0)
    elif t == "🕌 مواقيت الصلاة":
        pt = get_prayer_timings()
        msg = "🕌 المواقيت:\n"
        for k in ['Fajr','Dhuhr','Asr','Maghrib','Isha']: msg += f"{k}: {convert_to_12h(pt[k])}\n"
        bot.reply_to(m, msg)
    elif t == "📊 تقريري اليومي": bot.reply_to(m, get_today_report(cid), parse_mode="Markdown")
    elif t == "📝 تسجيل العبادات":
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(*[types.InlineKeyboardButton(n, callback_data=f"rec_{e}") for n,e in [("الفجر","Fajr"),("الظهر","Dhuhr"),("العصر","Asr"),("المغرب","Maghrib"),("العشاء","Isha")]])
        bot.reply_to(m, "سجل:", reply_markup=markup)
    else:
        # AI Part
        if model:
            try:
                bot.send_chat_action(cid, 'typing')
                prompt = f"أنت مساعد إسلامي. رد على: {t}"
                response = model.generate_content(prompt)
                
                # 🛑 هنا التغيير المهم: لو فيه خطأ، هيطبعهولك في الشات
                bot.reply_to(m, response.text)
            except Exception as e:
                # 🛑 طباعة الخطأ الحقيقي للمستخدم (عشان تصورهولي)
                bot.reply_to(m, f"❌ **خطأ تقني:**\n{str(e)}", parse_mode="Markdown")
                print(f"AI Error: {e}")
        else:
            bot.reply_to(m, "⚠️ خدمة AI غير مفعلة.")

if __name__ == "__main__":
    keep_alive()
    start_auto_reminders()
    bot.infinity_polling()
