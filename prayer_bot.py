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

# تهيئة الذكاء الاصطناعي (Gemini 2.5 Flash - High Token Limit)
try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "max_output_tokens": 8000,
        }
        
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        print("✅ تم تفعيل الذكاء الاصطناعي (Long Context) بنجاح!")
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

# --- 2. البيانات والنصوص (كاملة 100%) ---
GOOD_MSGS = ["يا مقلب القلوب ثبت قلبي.", "استمر يا بطل.", "ما شاء الله.", "أحب الأعمال أدومها.", "بيض الله وجهك."]
BAD_MSGS = ["جاهد نفسك.", "ألم يأن للذين آمنوا؟", "تدارك نفسك.", "الصلاة هي الصلة."]

# أذكار الصباح (كاملة)
MORNING_ADHKAR = [
    {"text": " أعوذ بالله من الشيطان الرجيم\n💎 **آية الكرسي:**\n{اللّهُ لاَ إِلَـهَ إِلاَّ هُوَ الْحَيُّ الْقَيُّومُ لاَ تَأْخُذُهُ سِنَةٌ وَلاَ نَوْمٌ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الأَرْضِ مَن ذَا الَّذِي يَشْفَعُ عِنْدَهُ إِلاَّ بِإِذْنِهِ يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ وَلاَ يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلاَّ بِمَا شَاء وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالأَرْضَ وَلاَ يَؤُودُهُ حِفْظُهُمَا وَهُوَ الْعَلِيُّ الْعَظِيمُ}", "count": 1},
    {"text": "💎 **سورة الإخلاص:**\n{قُلْ هُوَ ٱللَّهُ أَحَدٌ (1) ٱللَّهُ ٱلصَّمَدُ (2) لَمْ يَلِدْ وَلَمْ يُولَدْ (3) وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌ (4)}", "count": 3},
    {"text": "💎 **سورة الفلق:**\n{قُلْ أَعُوذُ بِرَبِّ ٱلْفَلَقِ (1) مِن شَرِّ مَا خَلَقَ (2) وَمِن شَرِّ غَاسِقٍ إِذَا وَقَبَ (3) وَمِن شَرِّ ٱلنَّفَّٰثَٰتِ فِى ٱلْعُقَدِ (4) وَمِن شَرِّ حَاسِدٍ إِذَا حَسَدَ (5)}", "count": 3},
    {"text": "💎 **سورة الناس:**\n{قُلْ أَعُوذُ بِرَبِّ ٱلنَّاسِ (1) مَلِكِ ٱلنَّاسِ (2) إِلَٰهِ ٱلنَّاسِ (3) مِن شَرِّ ٱلْوَسْوَاسِ ٱلْخَنَّاسِ (4) ٱلَّذِى يُوَسْوِسُ فِى صُدُورِ ٱلنَّاسِ (5) مِنَ ٱلْجِنَّةِ وَٱلنَّاسِ (6)}", "count": 3},
    {"text": "أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ لا إِلَهَ إِلا اللَّهُ وَحْدَهُ لا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ، رَبِّ أَسْأَلُكَ خَيْرَ مَا فِي هَذَا الْيَوْمِ وَخَيْرَ مَا بَعْدَهُ، وَأَعُوذُ بِكَ مِنْ شَرِّ مَا فِي هَذَا الْيَوْمِ وَشَرِّ مَا بَعْدَهُ، رَبِّ أَعُوذُ بِكَ مِنَ الْكَسَلِ وَسُوءِ الْكِبَرِ، رَبِّ أَعُوذُ بِكَ مِنْ عَذَابٍ فِي النَّارِ وَعَذَابٍ فِي الْقَبْرِ.", "count": 1},
    {"text": "اللَّهُمَّ بِكَ أَصْبَحْنَا وَبِكَ أَمْسَيْنَا، وَبِكَ نَحْيَا وَبِكَ نَمُوتُ وَإِلَيْكَ النُّشُورُ.", "count": 1},
    {"text": "اللهم أنت ربي لا إله إلا أنت خلقتني وأنا عبدك وأنا على عهدك ووعدك ما استطعت أعوذ بك من شر ما صنعت أبوء لك بنعمتك علي وأبوء بذنبي فاغفر لي فإنه لا يغفر الذنوب إلا أنت. (سيد الاستغفار)", "count": 1},
    {"text": "سُبْحَانَ اللهِ وَبِحَمْدِهِ. (10 مرات)", "count": 10},
    {"text": "يا حي يا قيوم برحمتك أستغيث أصلح لي شأني كله ولا تكلني إلى نفسي طرفة عين.", "count": 1}
]

# أذكار المساء (كاملة)
EVENING_ADHKAR = [
    {"text": " أعوذ بالله من الشيطان الرجيم\n💎 **آية الكرسي:**\n{اللّهُ لاَ إِلَـهَ إِلاَّ هُوَ الْحَيُّ الْقَيُّومُ لاَ تَأْخُذُهُ سِنَةٌ وَلاَ نَوْمٌ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الأَرْضِ مَن ذَا الَّذِي يَشْفَعُ عِنْدَهُ إِلاَّ بِإِذْنِهِ يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ وَلاَ يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلاَّ بِمَا شَاء وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالأَرْضَ وَلاَ يَؤُودُهُ حِفْظُهُمَا وَهُوَ الْعَلِيُّ الْعَظِيمُ}", "count": 1},
    {"text": "💎 **سورة الإخلاص:**\n{قُلْ هُوَ ٱللَّهُ أَحَدٌ (1) ٱللَّهُ ٱلصَّمَدُ (2) لَمْ يَلِدْ وَلَمْ يُولَدْ (3) وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌ (4)}", "count": 3},
    {"text": "💎 **سورة الفلق:**\n{قُلْ أَعُوذُ بِرَبِّ ٱلْفَلَقِ (1) مِن شَرِّ مَا خَلَقَ (2) وَمِن شَرِّ غَاسِقٍ إِذَا وَقَبَ (3) وَمِن شَرِّ ٱلنَّفَّٰثَٰتِ فِى ٱلْعُقَدِ (4) وَمِن شَرِّ حَاسِدٍ إِذَا حَسَدَ (5)}", "count": 3},
    {"text": "💎 **سورة الناس:**\n{قُلْ أَعُوذُ بِرَبِّ ٱلنَّاسِ (1) مَلِكِ ٱلنَّاسِ (2) إِلَٰهِ ٱلنَّاسِ (3) مِن شَرِّ ٱلْوَسْوَاسِ ٱلْخَنَّاسِ (4) ٱلَّذِى يُوَسْوِسُ فِى صُدُورِ ٱلنَّاسِ (5) مِنَ ٱلْجِنَّةِ وَٱلنَّاسِ (6)}", "count": 3},
    {"text": "أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ لا إِلَهَ إِلا اللَّهُ وَحْدَهُ لا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ، رَبِّ أَسْأَلُكَ خَيْرَ مَا فِي هَذِهِ اللَّيْلَةِ وَخَيْرَ مَا بَعْدَهَا، وَأَعُوذُ بِكَ مِنْ شَرِّ مَا فِي هَذِهِ اللَّيْلَةِ وَشَرِّ مَا بَعْدَهَا، رَبِّ أَعُوذُ بِكَ مِنَ الْكَسَلِ وَسُوءِ الْكِبَرِ، رَبِّ أَعُوذُ بِكَ مِنْ عَذَابٍ فِي النَّارِ وَعَذَابٍ فِي الْقَبْرِ.", "count": 1},
    {"text": "اللَّهُمَّ بِكَ أَمْسَيْنَا وَبِكَ أَصْبَحْنَا، وَبِكَ نَحْيَا وَبِكَ نَمُوتُ وَإِلَيْكَ الْمَصِيرُ.", "count": 1},
    {"text": "اللهم أنت ربي لا إله إلا أنت خلقتني وأنا عبدك وأنا على عهدك ووعدك ما استطعت أعوذ بك من شر ما صنعت أبوء لك بنعمتك علي وأبوء بذنبي فاغفر لي فإنه لا يغفر الذنوب إلا أنت. (سيد الاستغفار)", "count": 1},
    {"text": "أَعُوذُ بِكَلِمَاتِ اللَّهِ التَّامَّاتِ مِنْ شَرِّ مَا خَلَقَ.", "count": 3},
    {"text": "بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ.", "count": 3},
    {"text": "رَضِيتُ بِاللَّهِ رَبًّا، وَبِالْإِسْلَامِ دِينًا، وَبِمُحَمَّدٍ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ نَبِيًّا.", "count": 3}
]

# أذكار النوم (كاملة)
SLEEP_ADHKAR = [
    {"text": "🛏️ **آية الكرسي:**\n{اللّهُ لاَ إِلَـهَ إِلاَّ هُوَ الْحَيُّ الْقَيُّومُ لاَ تَأْخُذُهُ سِنَةٌ وَلاَ نَوْمٌ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الأَرْضِ مَن ذَا الَّذِي يَشْفَعُ عِنْدَهُ إِلاَّ بِإِذْنِهِ يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ وَلاَ يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلاَّ بِمَا شَاء وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالأَرْضَ وَلاَ يَؤُودُهُ حِفْظُهُمَا وَهُوَ الْعَلِيُّ الْعَظِيمُ}", "count": 1},
    {"text": "🛏️ **يجمع كفيه وينفث فيهما ويقرأ:**\n(سورة الإخلاص، سورة الفلق، سورة الناس)\nثم يمسح بهما ما استطاع من جسده. (يفعل ذلك 3 مرات)", "count": 3},
    {"text": "بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا.", "count": 1},
    {"text": "اللَّهُمَّ أَسْلَمْتُ نَفْسِي إِلَيْكَ، وَفَوَّضْتُ أَمْرِي إِلَيْكَ، وَوَجَّهْتُ وَجْهِي إِلَيْكَ، وَأَلْجَأْتُ ظَهْرِي إِلَيْكَ، رَغْبَةً وَرَهْبَةً إِلَيْكَ، لَا مَلْجَأَ وَلَا مَنْجَا مِنْكَ إِلَّا إِلَيْكَ، آمَنْتُ بِكِتَابِكَ الَّذِي أَنْزَلْتَ، وَبِنَبِيِّكَ الَّذِي أَرْسَلْتَ.", "count": 1},
    {"text": "اللَّهُمَّ قِنِي عَذَابَكَ يَوْمَ تَبْعَثُ عِبَادَكَ. (3 مرات)", "count": 3},
    {"text": "سُبْحَانَ اللَّهِ (33 مرة)، وَالْحَمْدُ لِلَّهِ (33 مرة)، وَاللَّهُ أَكْبَرُ (34 مرة).", "count": 1}
]

# --- 3. إعدادات البوت والسيرفر ---
app = Flask('')
@app.route('/')
def home(): return "<b>Omar Smart Bot V26.0 (Fixed Report & Reminders) is Online! 🚀</b>"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): t = Thread(target=run); t.start()

TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)
user_adhkar_state = {}

# --- 4. الوظائف ---
def get_cairo_time(): return datetime.utcnow() + timedelta(hours=2)

def convert_to_12h(time_24):
    try: return datetime.strptime(time_24, "%H:%M").strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")
    except: return time_24

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

# --- 🟢 إصلاح التنبيهات (فصل الصلاة على النبي عن الأذكار) ---
def start_auto_reminders():
    def remind_prophet():
        while True:
            time.sleep(1800) # كل 30 دقيقة
            for user in users_collection.find({}):
                try: bot.send_message(user['_id'], "🌸 **تذكير:**\nاللهم صلِّ وسلم على نبينا محمد ﷺ")
                except: pass
    
    def remind_dhikr():
        while True:
            time.sleep(2400) # كل 40 دقيقة
            msg = random.choice(["لا إله إلا الله", "سبحان الله وبحمده", "أستغفر الله العظيم وأتوب إليه", "لا حول ولا قوة إلا بالله"])
            for user in users_collection.find({}):
                try: bot.send_message(user['_id'], f"✨ **ذكر الله:**\n{msg}")
                except: pass

    Thread(target=remind_prophet).start()
    Thread(target=remind_dhikr).start()

# --- 🟢 إصلاح التقرير اليومي (إظهار الأسماء والأوقات) ---
def get_today_report(chat_id):
    now = get_cairo_time()
    today = now.strftime("%Y-%m-%d")
    user = users_collection.find_one({"_id": str(chat_id)})
    if not user: return "لا توجد بيانات مسجلة."
    
    prayers_done = user.get('prayers', {}).get(today, {})
    req = {'Fajr':'الفجر','Dhuhr':'الظهر','Asr':'العصر','Maghrib':'المغرب','Isha':'العشاء'}
    
    msg = f"📅 **تقرير اليوم ({today}):**\n\n"
    count = 0
    for k, v in req.items():
        if k in prayers_done:
            # هنا التعديل: إظهار الاسم والوقت
            time_done = convert_to_12h(prayers_done[k].get('time'))
            msg += f"✅ {v} ({time_done})\n"
            count += 1
        else:
            msg += f"❌ {v}\n"
            
    msg += "\n➖➖➖➖➖➖\n"
    msg += f"🌟 **رسالة لك:**\n{random.choice(GOOD_MSGS)}" if count >= 3 else f"⚠️ **تنبيه:**\n{random.choice(BAD_MSGS)}"
    return msg

# دالة تقسيم الرسائل الطويلة
def send_long_message(chat_id, text):
    if len(text) <= 4000:
        bot.send_message(chat_id, text)
    else:
        for x in range(0, len(text), 4000):
            bot.send_message(chat_id, text[x:x+4000])

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
    bot.send_message(m.chat.id, f"أهلاً {m.from_user.first_name} 👋\n\n{get_next_prayer_info()}\n\n🤖 **مربوط بالموديل الأحدث (Gemini 2.5 Flash)!**", reply_markup=main_menu(), parse_mode="Markdown")

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
    bot.send_message(chat_id, lst[idx]['text'], reply_markup=markup)

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
    bot.edit_message_text(f"✅ تم تسجيل {p}", c.message.chat.id, c.message.message_id)

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
                
                # إرسال الرد (مع التقسيم إذا كان طويلاً)
                send_long_message(cid, response.text)
                
            except Exception as e:
                bot.reply_to(m, f"❌ خطأ: {str(e)}")
        else:
            bot.reply_to(m, "⚠️ خدمة AI غير مفعلة.")

if __name__ == "__main__":
    keep_alive()
    start_auto_reminders()
    bot.infinity_polling()
