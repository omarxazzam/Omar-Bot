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

# --- 1. إعدادات المفاتيح والاتصال ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
MONGO_URL = "mongodb+srv://omarxazzam:Omar12345@azzam.o5lxlsj.mongodb.net/?retryWrites=true&w=majority&appName=AZZAM"

# تهيئة الذكاء الاصطناعي (مبدئياً)
try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        # سنترك تعريف الموديل فارغاً الآن حتى نختار الموديل الصحيح من الفحص
        model = None 
        print("✅ تم توصيل المفتاح بنجاح (بانتظار تحديد الموديل)")
    else:
        model = None
except Exception as e:
    print(f"⚠️ خطأ في المفتاح: {e}")
    model = None

# الاتصال بقاعدة البيانات
try:
    client = MongoClient(MONGO_URL)
    db = client['omar_bot_db']
    users_collection = db['users']
except Exception as e: pass

# --- 2. البيانات والنصوص (كاملة) ---
# (نفس القوائم السابقة - مختصرة هنا للعرض لكن انسخها كاملة من الكود السابق لو أحببت، 
# أو سأضع لك نسخة كاملة لتعمل مباشرة)
GOOD_MSGS = ["يا مقلب القلوب ثبت قلبي.", "استمر يا بطل.", "ما شاء الله.", "أحب الأعمال أدومها.", "بيض الله وجهك."]
BAD_MSGS = ["جاهد نفسك.", "ألم يأن للذين آمنوا؟", "تدارك نفسك.", "الصلاة هي الصلة."]

MORNING_ADHKAR = [{"text": "أصبحت وأصبح الملك لله", "count": 1}] # (اختصار للعرض، الكود سيعمل)
EVENING_ADHKAR = [{"text": "أمسيت وأمسى الملك لله", "count": 1}]
SLEEP_ADHKAR = [{"text": "باسمك اللهم أموت وأحيا", "count": 1}]

# --- 3. السيرفر ---
app = Flask('')
@app.route('/')
def home(): return "<b>Omar Bot - Diagnostic Mode 🛠️</b>"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): t = Thread(target=run); t.start()

TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)
user_adhkar_state = {}

# --- 4. وظائف الوقت ---
def get_cairo_time(): return datetime.utcnow() + timedelta(hours=2)
def convert_to_12h(t): return t 
def get_next_prayer_info(): return "⏳ (وضع الفحص)"

# --- 5. القوائم ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("🛠️ فحص الموديلات")) # زرار جديد للفحص
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "أهلاً عزام.. ده وضع الفحص 🛠️\nاضغط على الزر تحت عشان نشوف إيه الموديلات الشغالة.", reply_markup=main_menu())

# --- 6. أداة الفحص (الجديدة والمهمة) ---
@bot.message_handler(func=lambda m: m.text == "🛠️ فحص الموديلات" or m.text == "/check")
def check_models(message):
    cid = message.chat.id
    bot.send_chat_action(cid, 'typing')
    
    if not GEMINI_API_KEY:
        bot.reply_to(message, "❌ المفتاح غير موجود في Environment Variables!")
        return

    try:
        # كود يسأل جوجل عن الموديلات المتاحة
        bot.reply_to(message, "🔄 جاري الاتصال بجوجل لجلب القائمة...")
        
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(f"`{m.name}`")
        
        if available_models:
            msg = "✅ **تم العثور على الموديلات التالية:**\n\n" + "\n".join(available_models)
            msg += "\n\n💡 **انسخ اسم موديل من دول وقولي عليه.**"
        else:
            msg = "⚠️ اتصلت بجوجل بس ملقيتش موديلات تدعم الشات! غريبة جداً."
            
        bot.reply_to(message, msg, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"❌ **خطأ فادح:**\n{str(e)}")

# تشغيل البوت
if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
