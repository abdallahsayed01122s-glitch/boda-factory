
import os
import shutil
import subprocess
import json
import sys
import asyncio
import time

# --- [ 1. نظام الإصلاح التلقائي للبيئة ] ---
# الوظيفة دي بتسطب كل حاجة ناقصة وبتجهز الفولدرات عشان مفيش خطأ يوقف البوت
def setup_everything():
    # تثبيت المكتبات اللي ظهرت ناقصة في سجلات Hugging Face
    libs = ["pyrogram", "tgcrypto", "requests"]
    for lib in libs:
        try:
            __import__(lib)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
    
    # حل مشكلة المجلد bots وتثبيته بملف placeholder
    if not os.path.exists("bots"):
        os.makedirs("bots")
    
    with open("bots/placeholder.txt", "w") as f:
        f.write("Source Boda Folder Protection - Active")

# تشغيل الإعدادات فوراً
setup_everything()

import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, FloodWait

# --- [ 2. البيانات الأساسية ] ---
API_ID = 39803336  
API_HASH = "0189392ec80e2444649d108fa030c006" 
BOT_TOKEN = "7685337176:AAFo-DD_-g9QXu2Hf70N2MS35eszqrNLN9M" 
SUDO_ID = 8501385357 # آيدي المطور عبد الله
CH_USERNAME = "SsaWeM" # قناة الاشتراك الإجباري

app = Client("BodaFactory", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# متغيرات التحكم
factory_status = True
admin_mode = {} # لتتبع نوع الإذاعة
line = "━━━━━━━━━━━━━━━━━━━━"

# --- [ 3. وظائف قاعدة البيانات والاتصال ] ---
def load_users():
    if not os.path.exists("boda_db.json"):
        with open("boda_db.json", "w") as f: json.dump({"users": []}, f)
    with open("boda_db.json", "r") as f: return json.load(f)

def add_new_user(uid):
    data = load_users()
    if uid not in data["users"]:
        data["users"].append(uid)
        with open("boda_db.json", "w") as f: json.dump(data, f)

# وظيفة فحص التوكن مع معالجة الـ Timeout (حل مشكلة الصورة 1000436511)
def safe_check_token(token):
    url = f"https://api.telegram.org/bot{token}/getMe"
    for attempt in range(3): # محاولة الاتصال 3 مرات
        try:
            res = requests.get(url, timeout=30) # زيادة مدة الانتظار لـ 30 ثانية
            return res.json()
        except Exception:
            if attempt == 2: return None
            time.sleep(2)
    return None

# --- [ 4. تصميم واجهات الأزرار ] ---
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ صـنـع بـوت جـديـد", callback_data="make")],
        [InlineKeyboardButton("➖ حـذف بـوتـي", callback_data="delete")],
        [InlineKeyboardButton("👨‍💻 الـمـطـور", url=f"tg://user?id={SUDO_ID}"),
         InlineKeyboardButton("📡 قـنـاة الـسـورس", url=f"https://t.me/{CH_USERNAME}")]
    ])

def admin_menu():
    btn_text = "🚫 إيـقـاف الـمـصـنـع" if factory_status else "✅ تـشـغـيـل الـمـصـنـع"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 الإحـصـائـيـات", callback_data="stats")],
        [InlineKeyboardButton("📢 إذاعـة عـامـة", callback_data="bc_all"),
         InlineKeyboardButton("👤 إذاعـة تـوجـيـه", callback_data="bc_fwd")],
        [InlineKeyboardButton(btn_text, callback_data="toggle")],
        [InlineKeyboardButton("🏠 الـرئـيـسـيـة", callback_data="home")]
    ])

# --- [ 5. معالجة الأوامر والرسائل ] ---

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    add_new_user(message.from_user.id)
    # التحقق من الاشتراك الإجباري
    try:
        await client.get_chat_member(CH_USERNAME, message.from_user.id)
    except Exception:
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("📡 اشـتـرك الآن", url=f"https://t.me/{CH_USERNAME}")]])
        return await message.reply(f"**{line}\n⚠️ عـذراً، يـجـب الاشـتـراك بـالـقـناة أولاً.\n{line}**", reply_markup=btn)
    
    await message.reply(
        f"**{line}\nأهـلاً بـك يـا بـودا فـي مـصـنـع الـبـوتـات 🛡️\n{line}\nاصـنـع بـوت حـمـايـة مـتـكـامـل الآن مـجـانـاً.\n{line}**",
        reply_markup=main_menu()
    )

@app.on_message(filters.command("admin") & filters.user(SUDO_ID))
async def admin_handler(client, message):
    await message.reply(f"**{line}\n⚙️ لـوحـة تـحـكـم الـمـطـور عـبـد الله\n{line}**", reply_markup=admin_menu())

@app.on_message(filters.text & ~filters.command(["start", "admin"]))
async def text_handler(client, message):
    uid = message.from_user.id
    
    # نظام الإذاعة المطور (بدون GetHistory لتجنب خطأ 400)
    if uid == SUDO_ID and admin_mode.get(uid):
        mode = admin_mode[uid]
        admin_mode[uid] = None
        users = load_users()["users"]
        success = 0
        status_msg = await message.reply("⏳ جـاري الإرسـال لـلـجـمـيـع...")
        
        for user in users:
            try:
                if mode == "copy": await message.copy(user)
                else: await message.forward(user)
                success += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except: continue
        return await status_msg.edit(f"✅ تـمـت الإذاعـة لـ {success} مـسـتـخـدم.")

    # معالجة التوكن وصنع البوت
    if ":" in message.text and len(message.text) > 30:
        if not factory_status and uid != SUDO_ID:
            return await message.reply("⚠️ الـمـصـنـع مـتـوقـف حـالـيـاً لـلـتـحـديـث.")
        
        status = await message.reply("⏳ جـاري فـحـص الـتـوكـن (انـتـظـر 30 ثـانـيـة)...")
        
        # الفحص الذكي للتوكن
        check = safe_check_token(message.text)
        
        if check is None:
            return await status.edit("❌ فـشل الاتـصال بـسيرفرات تليـجرام (Timeout). حاول مرة أخرى.")
        
        if not check.get("ok"):
            return await status.edit("❌ الـتوكـن غـيـر صـحيح، تأكد مـن @BotFather.")

        # إنشاء المجلد الفرعي للبوت
        bot_dir = f"bots/{uid}"
        if os.path.exists(bot_dir): shutil.rmtree(bot_dir)
        os.makedirs(bot_dir)

        # نسخ الملفات الأساسية (تأكد إن الملفات دي موجودة في المساحة عندك)
        for f in ["DOLLAR1.lua", "tg.py"]:
            if os.path.exists(f): shutil.copy(f, bot_dir)
        
        # التشغيل باستخدام Screen لضمان الاستمرارية
        subprocess.Popen(f"cd {bot_dir} && screen -dmS bot_{uid} lua DOLLAR1.lua {message.text} {uid}", shell=True)
        await status.edit(f"**✅ تـم تـشـغـيـل بـوتـك بـنـجـاح!\n{line}\nيـوزر الـبـوت: @{check[ result ][ username ]}\n{line}**")

# --- [ 6. معالجة الأزرار (Callbacks) ] ---
@app.on_callback_query()
async def callback_handler(client, query):
    global factory_status
    uid = query.from_user.id

    if query.data == "home":
        await query.message.edit_text(f"**{line}\nمـصـنـع سـورس بـودا 🛡️\n{line}**", reply_markup=main_menu())
    
    elif query.data == "make":
        await query.message.reply(f"**{line}\nأرسـل الآن (تـوكـن) بـوتـك مـن بـوت فـاذر\n{line}**")
        await query.answer()

    elif query.data == "stats" and uid == SUDO_ID:
        u_count = len(load_users()["users"])
        b_count = len(os.listdir("bots")) - 1 
        await query.answer(f"📊 الإحـصائـيات:\n• المستخدمين: {u_count}\n• البوتات: {max(0, b_count)}", show_alert=True)

    elif query.data == "bc_all" and uid == SUDO_ID:
        admin_mode[uid] = "copy"
        await query.message.reply("📢 أرسـل الآن الـرسـالـة لـلإذاعـة الـعـامـة:")

    elif query.data == "bc_fwd" and uid == SUDO_ID:
        admin_mode[uid] = "fwd"
        await query.message.reply("👤 أرسـل الآن الـرسـالـة لـلإذاعـة (تـوجـيـه):")

    elif query.data == "toggle" and uid == SUDO_ID:
        factory_status = not factory_status
        await query.edit_message_reply_markup(reply_markup=admin_menu())
        await query.answer("تـم تـغـيـيـر حـالـة الـمـصـنـع.")

    elif query.data == "delete":
        path = f"bots/{uid}"
        if os.path.exists(path):
            os.system(f"screen -S bot_{uid} -X quit")
            shutil.rmtree(path)
            await query.message.reply("✅ تـم حـذف بـوتـك وإيـقـاف الـتـشـغـيـل.")
        else: await query.answer("❌ لـيـس لـديـك بـوت مـصـنوع.", show_alert=True)

print("--- Source Boda Factory is FULLY ONLINE ---")
app.run()
