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
MONGO_URL = "mongodb+srv://omarxazzam:Omar12345@azzam.o5lxlsj.mongodb.net/?retryWrites=true&w=majority&appName=AZZAM"

try:
    client = MongoClient(MONGO_URL)
    db = client['omar_bot_db']
    users_collection = db['users']
    print("✅ تم الاتصال بقاعدة البيانات بنجاح!")
except Exception as e:
    print(f"❌ فشل الاتصال بقاعدة البيانات: {e}")

# --- 2. رسائل التشجيع والمحاسبة ---
GOOD_MSGS = [
    "يا مقلب القلوب ثبت قلبي على دينك.",
    "استمر يا بطل، فالجنة سلعة الله الغالية.",
    "ما شاء الله.. زادك الله حرصاً وتوفيقاً.",
    "أحب الأعمال إلى الله أدومها وإن قل.",
    "بيض الله وجهك يوم تبيض وجوه وتسود وجوه.",
    "هذا من فضل ربي.. حافظ على هذا النور.",
    "اللهم كما أنعمت عليه بالطاعة فأتمم عليه بالقبول.",
    "سيروا إلى الله عرجاً ومكاسير.. ولا تنتظروا الصحة فإن انتظار الصحة بطالة.",
    "اثبت.. فإن الموعد الجنة بإذن الله.",
    "رزقك الله لذة النظر إلى وجهه الكريم."
]

BAD_MSGS = [
    "وَالَّذِينَ جَاهَدُوا فِينَا لَنَهْدِيَنَّهُمْ سُبُلَنَا.. جاهد نفسك يا عزام!",
    "ألم يأن للذين آمنوا أن تخشع قلوبهم لذكر الله؟",
    "تدارك نفسك قبل فوات الأوان، الصلاة هي الصلة.",
    "الجنة حلوة.. وتستاهل التعب، لا تكسل.",
    "يا ابن آدم، لو بلغت ذنوبك عنان السماء ثم استغفرتني غفرت لك.",
    "من ترك الصلاة فقد برئت منه ذمة الله.. راجع نفسك.",
    "قم الآن وتوضأ.. واكسر حاجز الشيطان.",
    "الدنيا ساعة.. فاجعلها طاعة.",
    "ماذا ستقول لربك غداً؟ استعد للقاء.",
    "إن الصلاة كانت على المؤمنين كتاباً موقوتاً."
]

# --- 3. بيانات الأذكار (كاملة 100%) ---
MORNING_ADHKAR = [
    {
        "text": " أعوذ بالله من الشيطان الرجيم\n💎 **آية الكرسي:**\n{اللّهُ لاَ إِلَـهَ إِلاَّ هُوَ الْحَيُّ الْقَيُّومُ لاَ تَأْخُذُهُ سِنَةٌ وَلاَ نَوْمٌ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الأَرْضِ مَن ذَا الَّذِي يَشْفَعُ عِنْدَهُ إِلاَّ بِإِذْنِهِ يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ وَلاَ يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلاَّ بِمَا شَاء وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالأَرْضَ وَلاَ يَؤُودُهُ حِفْظُهُمَا وَهُوَ الْعَلِيُّ الْعَظِيمُ}",
        "count": 1
    },
    {
        "text": "💎 **سورة الإخلاص:**\n{قُلْ هُوَ ٱللَّهُ أَحَدٌ (1) ٱللَّهُ ٱلصَّمَدُ (2) لَمْ يَلِدْ وَلَمْ يُولَدْ (3) وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌ (4)}",
        "count": 3
    },
    {
        "text": "💎 **سورة الفلق:**\n{قُلْ أَعُوذُ بِرَبِّ ٱلْفَلَقِ (1) مِن شَرِّ مَا خَلَقَ (2) وَمِن شَرِّ غَاسِقٍ إِذَا وَقَبَ (3) وَمِن شَرِّ ٱلنَّفَّٰثَٰتِ فِى ٱلْعُقَدِ (4) وَمِن شَرِّ حَاسِدٍ إِذَا حَسَدَ (5)}",
        "count": 3
    },
    {
        "text": "💎 **سورة الناس:**\n{قُلْ أَعُوذُ بِرَبِّ ٱلنَّاسِ (1) مَلِكِ ٱلنَّاسِ (2) إِلَٰهِ ٱلنَّاسِ (3) مِن شَرِّ ٱلْوَسْوَاسِ ٱلْخَنَّاسِ (4) ٱلَّذِى يُوَسْوِسُ فِى صُدُورِ ٱلنَّاسِ (5) مِنَ ٱلْجِنَّةِ وَٱلنَّاسِ (6)}",
        "count": 3
    },
    {
        "text": "أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ لا إِلَهَ إِلا اللَّهُ وَحْدَهُ لا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ، رَبِّ أَسْأَلُكَ خَيْرَ مَا فِي هَذَا الْيَوْمِ وَخَيْرَ مَا بَعْدَهُ، وَأَعُوذُ بِكَ مِنْ شَرِّ مَا فِي هَذَا الْيَوْمِ وَشَرِّ مَا بَعْدَهُ، رَبِّ أَعُوذُ بِكَ مِنَ الْكَسَلِ وَسُوءِ الْكِبَرِ، رَبِّ أَعُوذُ بِكَ مِنْ عَذَابٍ فِي النَّارِ وَعَذَابٍ فِي الْقَبْرِ.",
        "count": 1
    },
    {
        "text": "اللَّهُمَّ بِكَ أَصْبَحْنَا وَبِكَ أَمْسَيْنَا، وَبِكَ نَحْيَا وَبِكَ نَمُوتُ وَإِلَيْكَ النُّشُورُ.",
        "count": 1
    },
    {
        "text": "اللهم أنت ربي لا إله إلا أنت خلقتني وأنا عبدك وأنا على عهدك ووعدك ما استطعت أعوذ بك من شر ما صنعت أبوء لك بنعمتك علي وأبوء بذنبي فاغفر لي فإنه لا يغفر الذنوب إلا أنت.",
        "count": 1
    },
    {
        "text": "سُبْحَانَ اللهِ وَبِحَمْدِهِ. (10 مرات)",
        "count": 10
    },
    {
        "text": "يا حي يا قيوم برحمتك أستغيث أصلح لي شأني كله ولا تكلني إلى نفسي طرفة عين.",
        "count": 1
    }
]

EVENING_ADHKAR = [
    {
        "text": " أعوذ بالله من الشيطان الرجيم\n💎 **آية الكرسي:**\n{اللّهُ لاَ إِلَـهَ إِلاَّ هُوَ الْحَيُّ الْقَيُّومُ لاَ تَأْخُذُهُ سِنَةٌ وَلاَ نَوْمٌ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الأَرْضِ مَن ذَا الَّذِي يَشْفَعُ عِنْدَهُ إِلاَّ بِإِذْنِهِ يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ وَلاَ يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلاَّ بِمَا شَاء وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالأَرْضَ وَلاَ يَؤُودُهُ حِفْظُهُمَا وَهُوَ الْعَلِيُّ الْعَظِيمُ}",
        "count": 1
    },
    {
        "text": "💎 **سورة الإخلاص:**\n{قُلْ هُوَ ٱللَّهُ أَحَدٌ (1) ٱللَّهُ ٱلصَّمَدُ (2) لَمْ يَلِدْ وَلَمْ يُولَدْ (3) وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌ (4)}",
        "count": 3
    },
    {
        "text": "💎 **سورة الفلق:**\n{قُلْ أَعُوذُ بِرَبِّ ٱلْفَلَقِ (1) مِن شَرِّ مَا خَلَقَ (2) وَمِن شَرِّ غَاسِقٍ إِذَا وَقَبَ (3) وَمِن شَرِّ ٱلنَّفَّٰثَٰتِ فِى ٱلْعُقَدِ (4) وَمِن شَرِّ حَاسِدٍ إِذَا حَسَدَ (5)}",
        "count": 3
    },
    {
        "text": "💎 **سورة الناس:**\n{قُلْ أَعُوذُ بِرَبِّ ٱلنَّاسِ (1) مَلِكِ ٱلنَّاسِ (2) إِلَٰهِ ٱلنَّاسِ (3) مِن شَرِّ ٱلْوَسْوَاسِ ٱلْخَنَّاسِ (4) ٱلَّذِى يُوَسْوِسُ فِى صُدُورِ ٱلنَّاسِ (5) مِنَ ٱلْجِنَّةِ وَٱلنَّاسِ (6)}",
        "count": 3
    },
    {
        "text": "أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ لا إِلَهَ إِلا اللَّهُ وَحْدَهُ لا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ، رَبِّ أَسْأَلُكَ خَيْرَ مَا فِي هَذِهِ اللَّيْلَةِ وَخَيْرَ مَا بَعْدَهَا، وَأَعُوذُ بِكَ مِنْ شَرِّ مَا فِي هَذِهِ اللَّيْلَةِ وَشَرِّ مَا بَعْدَهَا، رَبِّ أَعُوذُ بِكَ مِنَ الْكَسَلِ وَسُوءِ الْكِبَرِ، رَبِّ أَعُوذُ بِكَ مِنْ عَذَابٍ فِي النَّارِ وَعَذَابٍ فِي الْقَبْرِ.",
        "count": 1
    },
    {
        "text": "اللَّهُمَّ بِكَ أَمْسَيْنَا وَبِكَ أَصْبَحْنَا، وَبِكَ نَحْيَا وَبِكَ نَمُوتُ وَإِلَيْكَ الْمَصِيرُ.",
        "count": 1
    },
    {
        "text": "اللهم أنت ربي لا إله إلا أنت خلقتني وأنا عبدك وأنا على عهدك ووعدك ما استطعت أعوذ بك من شر ما صنعت أبوء لك بنعمتك علي وأبوء بذنبي فاغفر لي فإنه لا يغفر الذنوب إلا أنت.",
        "count": 1
    },
    {
        "text": "أَعُوذُ بِكَلِمَاتِ اللَّهِ التَّامَّاتِ مِنْ شَرِّ مَا خَلَقَ.",
        "count": 3
    },
    {
        "text": "بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ.",
        "count": 3
    },
    {
        "text": "رَضِيتُ بِاللَّهِ رَبًّا، وَبِالْإِسْلَامِ دِينًا، وَبِمُحَمَّدٍ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ نَبِيًّا.",
        "count": 3
    }
]

# --- 4. إعدادات البوت والسيرفر ---
app = Flask('')
@app.route('/')
def home(): return "<b>Omar Smart Bot V10.0 (Perfect Edition) is Online! 🚀</b>"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): t = Thread(target=run); t.start()

TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)
user_adhkar_state = {}

# --- 5. وظائف النظام والتحويل ---
def convert_to_12h(time_24):
    """تحويل الوقت من 24 ساعة إلى 12 ساعة (ص/م)"""
    try:
        t = datetime.strptime(time_24, "%H:%M")
        return t.strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")
    except:
        return time_24

def start_auto_reminders():
    def remind_prophet():
        while True:
            time.sleep(1800) 
            users = users_collection.find({})
            for user in users:
                try: bot.send_message(user['_id'], "🌸 **تذكير:**\nاللهم صلِّ وسلم على نبينا محمد ﷺ")
                except: pass

    def remind_dhikr():
        while True:
            time.sleep(2400)
            msg = random.choice(["لا إله إلا الله", "سبحان الله العظيم", "أستغفر الله وأتوب إليه"])
            users = users_collection.find({})
            for user in users:
                try: bot.send_message(user['_id'], f"✨ **ذكر الله:**\n{msg}")
                except: pass

    t1 = Thread(target=remind_prophet); t1.start()
    t2 = Thread(target=remind_dhikr); t2.start()

def get_prayer_timings():
    try:
        url = "http://api.aladhan.com/v1/timingsByCity?city=Cairo&country=Egypt&method=5"
        return requests.get(url, timeout=3).json()['data']['timings']
    except: return None

def register_user(chat_id, name):
    cid = str(chat_id)
    if not users_collection.find_one({"_id": cid}):
        users_collection.insert_one({"_id": cid, "name": name, "join_date": datetime.now().strftime("%Y-%m-%d"), "points": 0})

def get_today_report(chat_id):
    today = datetime.now().strftime("%Y-%m-%d")
    user = users_collection.find_one({"_id": str(chat_id)})
    
    if not user: return "لا توجد بيانات."
    
    prayers_done = user.get('prayers', {}).get(today, {})
    required_prayers = {'Fajr': 'الفجر', 'Dhuhr': 'الظهر', 'Asr': 'العصر', 'Maghrib': 'المغرب', 'Isha': 'العشاء'}
    
    report_msg = f"📅 **تقرير اليوم ({today}):**\n\n"
    done_count = 0
    
    for key, name in required_prayers.items():
        if key in prayers_done:
            # عرض وقت التسجيل بنظام 12 ساعة أيضاً
            rec_time = prayers_done[key].get("time", "تم")
            rec_time_12 = convert_to_12h(rec_time)
            report_msg += f"✅ {name} (تم: {rec_time_12})\n"
            done_count += 1
        else:
            report_msg += f"❌ {name}\n"
            
    total_required = 5
    ratio = done_count / total_required
    
    report_msg += "\n➖➖➖➖➖➖\n"
    
    if ratio >= 0.6: 
        quote = random.choice(GOOD_MSGS)
        report_msg += f"🌟 **رسالة لك:**\n{quote}"
    else: 
        quote = random.choice(BAD_MSGS)
        report_msg += f"⚠️ **رسالة تنبيه:**\n{quote}"
        
    return report_msg

# --- 6. القوائم والتفاعل ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("🕌 مواقيت الصلاة"), types.KeyboardButton("📝 تسجيل العبادات"))
    markup.add(types.KeyboardButton("☀️ أذكار الصباح"), types.KeyboardButton("🌙 أذكار المساء"))
    markup.add(types.KeyboardButton("📊 تقريري اليومي")) 
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    register_user(message.chat.id, message.from_user.first_name)
    bot.send_message(message.chat.id, f"أهلاً بك يا **{message.from_user.first_name}** 👋\n\nتم تحديث الوقت (12 ساعة) وأذكار المساء الكاملة ✅", reply_markup=main_menu(), parse_mode="Markdown")

# --- معالجة الأذكار ---
def send_dhikr(chat_id, dhikr_type, index):
    lst = MORNING_ADHKAR if dhikr_type == "morning" else EVENING_ADHKAR
    if index >= len(lst):
        bot.send_message(chat_id, "🎉 **تم بحمد الله!**\nتقبل الله طاعتك.", parse_mode="Markdown")
        del user_adhkar_state[chat_id]
        return

    dhikr = lst[index]
    user_adhkar_state[chat_id] = {'type': dhikr_type, 'index': index, 'count': dhikr['count']}
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"📿 العدد: {dhikr['count']}", callback_data="cnt"))
    if index > 0: markup.add(types.InlineKeyboardButton("⬅️ السابق", callback_data="prev"))
    
    title = "☀️ الصباح" if dhikr_type == "morning" else "🌙 المساء"
    bot.send_message(chat_id, f"**{title} ({index+1}/{len(lst)})**\n\n{dhikr['text']}", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "cnt")
def count_dhikr_btn(call):
    cid = call.message.chat.id
    if cid not in user_adhkar_state: return
    st = user_adhkar_state[cid]
    st['count'] -= 1
    if st['count'] > 0:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"📿 العدد: {st['count']}", callback_data="cnt"))
        if st['index'] > 0: markup.add(types.InlineKeyboardButton("⬅️ السابق", callback_data="prev"))
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=markup)
    else:
        bot.delete_message(cid, call.message.message_id)
        send_dhikr(cid, st['type'], st['index'] + 1)

@bot.callback_query_handler(func=lambda c: c.data == "prev")
def prev_dhikr(c):
    cid = c.message.chat.id
    if cid in user_adhkar_state:
        st = user_adhkar_state[cid]
        bot.delete_message(cid, c.message.message_id)
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
        bot.reply_to(m, "سجل صلاتك:", reply_markup=markup)
        
    elif text == "🕌 مواقيت الصلاة":
        t = get_prayer_timings()
        if t:
            msg = "🕌 **المواقيت (اليوم):**\n"
            # استخدام دالة التحويل هنا
            for k in ['Fajr','Dhuhr','Asr','Maghrib','Isha']: 
                msg += f"🔹 {k}: {convert_to_12h(t[k])}\n"
            bot.reply_to(m, msg)
            
    elif text == "📊 تقريري اليومي":
        report = get_today_report(cid)
        bot.reply_to(m, report, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith('rec_'))
def rec_prayer(c):
    cid = str(c.message.chat.id)
    p_name = c.data.split('_')[1]
    dt = datetime.now().strftime("%Y-%m-%d")
    
    users_collection.update_one({"_id": cid}, 
        {"$set": {f"prayers.{dt}.{p_name}": {"time": datetime.now().strftime("%H:%M")}}}, upsert=True)
         
    bot.edit_message_text(f"✅ تم تسجيل {p_name}\nتقبل الله منك.", c.message.chat.id, c.message.message_id)

if __name__ == "__main__":
    keep_alive()
    start_auto_reminders()
    bot.infinity_polling()
