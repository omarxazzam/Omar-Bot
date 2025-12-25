import telebot
import requests
from telebot import types
from flask import Flask
from threading import Thread
import json
import os
import time
from datetime import datetime, timedelta

# --- 1. إعدادات السيرفر (مجهز للسيرفرات السحابية) ---
app = Flask('')

@app.route('/')
def home():
    return "<b>Omar Smart Bot V4.1 is Online!</b>"

def run():
    # هذا التعديل مهم جداً لـ Render
    # يجعل السيرفر يختار البورت المتاح تلقائياً
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
    t2 = Thread(target=schedule_checker)
    t2.start()

# قراءة التوكن من إعدادات الموقع الآمنة
TOKEN = os.environ.get('TELEGRAM_TOKEN')

if not TOKEN:
    print("Error: TELEGRAM_TOKEN not found!")
else:
    bot = telebot.TeleBot(TOKEN)

# --- 3. قاعدة بيانات الأذكار (النص الكامل) ---
AZKAR_DB = {
    'morning': [
        {'t': '🌸 **آية الكرسي:**\n\n(اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ ۚ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ...)', 'c': 1},
        {'t': '🌸 **الإخلاص والمعوذتين:**\n\n(قُلْ هُوَ ٱللَّهُ أَحَدٌ...)\n(قُلْ أَعُوذُ بِرَبِّ ٱلْفَلَقِ...)\n(قُلْ أَعُوذُ بِرَبِّ ٱلنَّاسِ...)', 'c': 3},
        {'t': '🌸 **أذكار الصباح:**\n\nأَصْبَحْنا وَأَصْبَحَ المُلْكُ لله وَالحَمدُ لله، لا إلهَ إلاّ اللّهُ وَحدَهُ لا شَريكَ لهُ...', 'c': 1},
        {'t': '🌸 **سيد الاستغفار:**\n\nاللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ، خَلَقْتَنِي وَأَنَا عَبْدُكَ...', 'c': 1},
        {'t': '🌸 **الحفظ:**\n\nبِسْمِ اللهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ...', 'c': 3},
        {'t': '🌸 **الرضا:**\n\nرَضِيتُ بِاللهِ رَبًّا، وَبِالْإِسْلَامِ دِينًا، وَبِمُحَمَّدٍ صَلَّى اللهُ عَلَيْهِ وَسَلَّمَ نَبِيًّا.', 'c': 3},
        {'t': '🌸 **التسبيح:**\n\nسُبْحَانَ اللهِ وَبِحَمْدِهِ: عَدَدَ خَلْقِهِ، وَرِضَا نَفْسِهِ، وَزِنَةَ عَرْشِهِ، وَمِدَادَ كَلِمَاتِهِ.', 'c': 3},
        {'t': '🌸 **يا حي يا قيوم:**\n\nيا حَيُّ يا قَيُّومُ بِرَحْمَتِكَ أستَغيثُ، أصلِحْ لي شَأني كُلَّهُ، ولا تَكِلْني إلى نَفْسي طَرْفةَ عَيْن.', 'c': 1},
        {'t': '🌸 **التهليل:**\n\nلا إلَهَ إلاَّ اللَّهُ وحْدَهُ لا شَرِيكَ لَهُ، لَهُ المُلْكُ ولَهُ الحَمْدُ، وهُوَ علَى كُلِّ شيءٍ قَدِيرٌ.', 'c': 10}
    ],
    'evening': [
        {'t': '🌙 **آية الكرسي:**\n\n(اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ...)', 'c': 1},
        {'t': '🌙 **الإخلاص والمعوذتين:**\n\n(قُلْ هُوَ ٱللَّهُ أَحَدٌ...)\n(قُلْ أَعُوذُ بِرَبِّ ٱلْفَلَقِ...)\n(قُلْ أَعُوذُ بِرَبِّ ٱلنَّاسِ...)', 'c': 3},
        {'t': '🌙 **أذكار المساء:**\n\nأَمْسَيْنا وَأَمْسَى المُلْكُ لله وَالحَمدُ لله، لا إلهَ إلاّ اللّهُ وَحدَهُ لا شَريكَ لهُ...', 'c': 1},
        {'t': '🌙 **سيد الاستغفار:**\n\nاللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ، خَلَقْتَنِي وَأَنَا عَبْدُكَ...', 'c': 1},
        {'t': '🌙 **الحفظ:**\n\nبِسْمِ اللهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ...', 'c': 3},
        {'t': '🌙 **التعوذ:**\n\nأَعُوذُ بِكَلِمَاتِ اللهِ التَّامَّاتِ مِنْ شَرِّ مَا خَلَقَ.', 'c': 3},
        {'t': '🌙 **الرضا:**\n\nرَضِيتُ بِاللهِ رَبًّا، وَبِالْإِسْلَامِ دِينًا، وَبِمُحَمَّدٍ صَلَّى اللهُ عَلَيْهِ وَسَلَّمَ نَبِيًّا.', 'c': 3},
        {'t': '🌙 **العافية:**\n\nاللَّهُمَّ عَافِنِي فِي بَدَنِي، اللَّهُمَّ عَافِنِي فِي سَمْعِي، اللَّهُمَّ عَافِنِي فِي بَصَرِي، لَا إِلَهَ إِلَّا أَنْتَ.', 'c': 3}
    ]
}

# --- 4. ملفات البيانات ---
DB_FILE = "user_data.json"
USERS_FILE = "users_ids.json"
sessions = {}

def load_json(filename):
    if not os.path.exists(filename): return {}
    with open(filename, 'r') as f:
        try: return json.load(f)
        except: return {}

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f)

def register_user(chat_id):
    users = load_json(USERS_FILE)
    if str(chat_id) not in users:
        users[str(chat_id)] = {"active": True}
        save_json(USERS_FILE, users)

def clear_user_data(user_id):
    data = load_json(DB_FILE)
    uid = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    if uid in data and today in data[uid]:
        del data[uid][today]
        save_json(DB_FILE, data)
        return True
    return False

# --- 5. منطق الوقت ---
def get_egypt_time():
    return datetime.utcnow() + timedelta(hours=2)

def convert_to_12h(time24):
    try:
        t = datetime.strptime(time24, "%H:%M")
        return t.strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")
    except:
        return time24

def get_prayers_raw():
    url = "http://api.aladhan.com/v1/timingsByCity"
    params = {'city': 'Cairo', 'country': 'Egypt', 'method': 5}
    try:
        response = requests.get(url, params=params, timeout=5)
        return response.json()['data']['timings']
    except:
        return None

def calculate_delay(prayer_time_str):
    current = get_egypt_time()
    p_time = datetime.strptime(prayer_time_str, "%H:%M")
    p_date = current.replace(hour=p_time.hour, minute=p_time.minute, second=0)
    diff = (current - p_date).total_seconds() / 60
    
    if diff < -20: return "بدري جداً ⚠️"
    elif -20 <= diff <= 40: return "في وقتها 🟢"
    elif 40 < diff < 60: return f"تأخير {int(diff)} د 🟠"
    else: 
        h = int(diff // 60)
        m = int(diff % 60)
        return f"تأخير {h} س {m} د 🔴"

def log_activity(user_id, name, status):
    data = load_json(DB_FILE)
    uid = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if uid not in data: data[uid] = {}
    if today not in data[uid]: data[uid][today] = []
    
    data[uid][today] = [x for x in data[uid][today] if x['name'] != name]
    entry = {"name": name, "status": status, "time": datetime.now().strftime("%I:%M %p")}
    data[uid][today].append(entry)
    save_json(DB_FILE, data)
    return True

# --- 6. منطق العداد الذكي ---
def start_dhikr_session(chat_id, type_key):
    sessions[chat_id] = {'type': type_key, 'index': 0, 'count': 0}
    send_dhikr_card(chat_id)

def send_dhikr_card(chat_id):
    session = sessions.get(chat_id)
    if not session: return
    
    zkr_list = AZKAR_DB[session['type']]
    index = session['index']
    
    if index >= len(zkr_list):
        name = "أذكار الصباح" if session['type'] == 'morning' else "أذكار المساء"
        log_activity(chat_id, name, "تمت كاملة ✅")
        bot.send_message(chat_id, f"🎉 **تقبل الله يا عمر!**\nتم الانتهاء من {name} وتسجيلها.", reply_markup=main_menu())
        del sessions[chat_id]
        return

    current_zkr = zkr_list[index]
    text = current_zkr['t']
    required = current_zkr['c']
    current_count = session['count']
    
    msg_text = f"📿 **{index + 1} / {len(zkr_list)}**\n\n{text}"
    
    markup = types.InlineKeyboardMarkup()
    btn_text = f"سبح ({current_count}/{required}) 👆"
    if current_count >= required: btn_text = "✅ اكتمل - التالي"
    
    markup.add(types.InlineKeyboardButton(btn_text, callback_data="zkr_count"))
    
    if current_count == 0:
        bot.send_message(chat_id, msg_text, reply_markup=markup)

# --- 7. التفاعل ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("🕌 مواقيت الصلاة"), types.KeyboardButton("📝 تسجيل العبادات"))
    markup.add(types.KeyboardButton("📊 تقريري اليوم"), types.KeyboardButton("🏆 إحصائياتي"))
    markup.add(types.KeyboardButton("🗑️ تصفير البيانات")) 
    markup.add(types.KeyboardButton("☀️ أذكار الصباح"), types.KeyboardButton("🌙 أذكار المساء"))
    return markup

def tracking_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ الفجر", callback_data='done_Fajr'),
        types.InlineKeyboardButton("✅ الظهر", callback_data='done_Dhuhr'),
        types.InlineKeyboardButton("✅ العصر", callback_data='done_Asr'),
        types.InlineKeyboardButton("✅ المغرب", callback_data='done_Maghrib'),
        types.InlineKeyboardButton("✅ العشاء", callback_data='done_Isha')
    )
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    register_user(message.chat.id)
    bot.send_message(message.chat.id, "أهلاً بك يا عمر 🌹\nبوت المساعد الإسلامي جاهز.", reply_markup=main_menu())

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    text = message.text
    chat_id = message.chat.id
    
    if text == "🕌 مواقيت الصلاة":
        timings = get_prayers_raw()
        if timings:
            msg = "🕌 **مواقيت الصلاة اليوم:**\n\n"
            for p in ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
                msg += f"🔹 {name_to_ar(p)}: `{convert_to_12h(timings[p])}`\n"
            bot.reply_to(message, msg)

    elif text == "📝 تسجيل العبادات":
        bot.reply_to(message, "سجل صلاتك:", reply_markup=tracking_menu())

    elif text == "📊 تقريري اليوم":
        data = load_json(DB_FILE)
        today = datetime.now().strftime("%Y-%m-%d")
        uid = str(chat_id)
        if uid in data and today in data[uid] and data[uid][today]:
            msg = f"📈 **تقرير عمر اليوم ({today}):**\n\n"
            for item in data[uid][today]:
                msg += f"▫️ **{item['name']}**: {item['status']}\n"
            bot.reply_to(message, msg)
        else:
            bot.reply_to(message, "التقرير فارغ.")

    elif text == "🗑️ تصفير البيانات":
        clear_user_data(chat_id)
        bot.reply_to(message, "تم مسح البيانات.", reply_markup=main_menu())

    elif text == "🏆 إحصائياتي":
        data = load_json(DB_FILE)
        uid = str(chat_id)
        today = datetime.now().strftime("%Y-%m-%d")
        if uid in data and today in data[uid] and data[uid][today]:
            total = len(data[uid][today])
            on_time = sum(1 for x in data[uid][today] if "🟢" in x['status'])
            score = int((on_time / max(total, 1)) * 100)
            bot.reply_to(message, f"🏆 نسبة التزامك: {score}%")
        else:
            bot.reply_to(message, "لا توجد بيانات.")

    elif text == "☀️ أذكار الصباح":
        start_dhikr_session(chat_id, 'morning')
        
    elif text == "🌙 أذكار المساء":
        start_dhikr_session(chat_id, 'evening')

@bot.callback_query_handler(func=lambda call: call.data == "zkr_count")
def handle_counter(call):
    chat_id = call.message.chat.id
    session = sessions.get(chat_id)
    if not session:
        bot.answer_callback_query(call.id, "انتهت الجلسة.")
        return

    session['count'] += 1
    zkr_list = AZKAR_DB[session['type']]
    index = session['index']
    required = zkr_list[index]['c']
    
    if session['count'] >= required:
        session['index'] += 1
        session['count'] = 0
        if session['index'] < len(zkr_list):
            try: bot.delete_message(chat_id, call.message.message_id)
            except: pass
            send_dhikr_card(chat_id)
        else:
            try: bot.delete_message(chat_id, call.message.message_id)
            except: pass
            send_dhikr_card(chat_id)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"سبح ({session['count']}/{required}) 👆", callback_data="zkr_count"))
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('done_'))
def handle_prayer_log(call):
    try:
        action = call.data
        timings = get_prayers_raw()
        prayer_map = {
            'done_Fajr': ('صلاة الفجر', timings['Fajr'] if timings else None),
            'done_Dhuhr': ('صلاة الظهر', timings['Dhuhr'] if timings else None),
            'done_Asr': ('صلاة العصر', timings['Asr'] if timings else None),
            'done_Maghrib': ('صلاة المغرب', timings['Maghrib'] if timings else None),
            'done_Isha': ('صلاة العشاء', timings['Isha'] if timings else None),
        }
        if action in prayer_map:
            name, p_time = prayer_map[action]
            status = calculate_delay(p_time) if p_time else "تم"
            log_activity(call.from_user.id, name, status)
            bot.answer_callback_query(call.id, f"تم تسجيل {name} ({status})", show_alert=True)
    except:
        pass

def name_to_ar(name):
    maps = {'Fajr': 'الفجر', 'Dhuhr': 'الظهر', 'Asr': 'العصر', 'Maghrib': 'المغرب', 'Isha': 'العشاء'}
    return maps.get(name, name)

def schedule_checker():
    while True:
        try:
            now = get_egypt_time()
            if now.second < 5:
                timings = get_prayers_raw()
                if timings:
                    for name, time_str in timings.items():
                        if name in ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
                            p_time = datetime.strptime(time_str, "%H:%M")
                            p_now = now.replace(hour=p_time.hour, minute=p_time.minute, second=0)
                            diff_min = (p_now - now).total_seconds() / 60
                            if 9.5 < diff_min < 10.5:
                                send_broadcast(f"⏳ باقي 10 دقائق على صلاة {name_to_ar(name)} يا عمر!")
                                time.sleep(60)
        except: pass
        time.sleep(10)

def send_broadcast(text):
    users = load_json(USERS_FILE)
    for chat_id in users:
        try: bot.send_message(chat_id, text)
        except: pass

keep_alive()

bot.infinity_polling()
