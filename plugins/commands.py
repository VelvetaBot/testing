import os
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from database import users_db
import config
from datetime import datetime

def get_header(user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    if plan == "PREMIUM": return "<blockquote>💎 <b>Velveta Premium User</b>                            </blockquote>\n"
    elif plan == "ADS_PREMIUM": return "<blockquote>💎 <b>Velveta Semi Premium User</b></blockquote>\n"
    else: return ""

async def check_joined(client, user_id):
    try:
        await client.get_chat_member(config.Config.UPDATE_CHANNEL, user_id)
        return True
    except UserNotParticipant: return False
    except Exception: return False

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    user_id = message.from_user.id
    if not users_db.find_one({"user_id": user_id}):
        users_db.insert_one({"user_id": user_id, "plan": "FREE", "plan_started": datetime.now().strftime("%Y-%m-%d"), "bot_count": 0, "group_count": 0, "last_limit_date": datetime.now().strftime("%Y-%m-%d")})

    is_joined = await check_joined(client, user_id)
    if not is_joined:
        text = "⛔️ <b>Access Denied</b> ⛔️\n\n🙋‍♂️ Hey User, You Must Join <b>@Velvetabots</b> Telegram Channel To Use This BOT. So, Please Join it 🤗. Thank You 🤝"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Update Channel", url="https://t.me/Velvetabots")], [InlineKeyboardButton("☑️ Joined", callback_data="check_joined_button")]])
        await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
        return

    users_db.update_one({"user_id": user_id}, {"$set": {"state": None}})
    header = get_header(user_id)
    welcome_text = f"{header}🌟 <u><b>Welcome to Velveta YouTube Downloader (Pro)!</b></u>🌟\nI can download YouTube videos up to <b>2GB</b> with <b>fast, smooth & premium performance</b>🚀\n\n<u><b>How to use:</b></u>\n1️⃣ Send a YouTube link 🔗\n2️⃣ Get your file instantly 📥\n3️⃣ For more details, send /help"
    await message.reply_text(welcome_text, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("my_plan") & filters.private)
async def my_plan_command(client, message):
    user = users_db.find_one({"user_id": message.from_user.id}) or {}
    plan = user.get("plan", "FREE")
    started = user.get("plan_started", str(datetime.now().date()))
    header = get_header(message.from_user.id)
    text = f"{header}👤 <b>User Dashboard</b>\n🆔 ID: <code>{message.from_user.id}</code>\n📦 Plan: <b>{plan}</b>\n📅 Started: {started}\n⏳ Validity: Unlimited\n━━━━━━━━━━━━━━\n🚀 <b>Features:</b>\n✔️ 5 Downloadings\n✔️ Basic support\n✔️ Standard speed\n✔️ Extra 5 Downloadings on Group\n✔️ Reliable interference \n✔️ Best Quality\n━━━━━━━━━━━━━━\n💬 Need help? @Velvetasupport"
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("schedule") & filters.private)
async def schedule_cmd(client, message):
    users_db.update_one({"user_id": message.from_user.id}, {"$set": {"state": "schedule_link"}})
    header = get_header(message.from_user.id)
    await message.reply_text(f"{header}🎬 Please send the YouTube link you want to schedule\n\n👉 Make sure it is a valid link (https://)", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("save") & filters.private)
async def save_cmd(client, message):
    users_db.update_one({"user_id": message.from_user.id}, {"$set": {"state": "save_link"}})
    header = get_header(message.from_user.id)
    await message.reply_text(f"{header}📩 Please send the YouTube link or video\n\n📌 So we can process and save your content", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("set_preferred_quality") & filters.private)
async def set_pref_quality(client, message):
    header = get_header(message.from_user.id)
    text = f"{header}🎥 Please choose your preferred quality\n\n📌 Select one of the options below"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 4K (Ultra HD)", callback_data="pref_dl|4k"), InlineKeyboardButton("🌟 2K (Mini Ultra HD)", callback_data="pref_dl|2k")],
        [InlineKeyboardButton("🖥 1080p (Full HD)", callback_data="pref_dl|1080p"), InlineKeyboardButton("💻 720p (HD)", callback_data="pref_dl|720p")],
        [InlineKeyboardButton("📺 480p (Clear)", callback_data="pref_dl|480p"), InlineKeyboardButton("📱 360p (Best Mobile)", callback_data="pref_dl|360p")],
        [InlineKeyboardButton("📟 240p (Ok Ok)", callback_data="pref_dl|240p"), InlineKeyboardButton("📉 144p (Data Saver)", callback_data="pref_dl|144p")],
        [InlineKeyboardButton("🎵 Audio Only (MP3)", callback_data="pref_dl|audio")]
    ])
    await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^pref_dl\|(.*)$"))
async def save_pref_quality(client, callback_query):
    q = callback_query.data.split("|")[1]
    users_db.update_one({"user_id": callback_query.from_user.id}, {"$set": {"preferred_quality": q}})
    header = get_header(callback_query.from_user.id)
    await callback_query.message.edit_text(f"{header}✅ Your preferred quality has been set successfully\n\n⚠️ Important Note:\nIf the selected quality is not available, the downloader will automatically switch to the nearest available quality\n\n🔄 If you use the command /set_preferred_quality again, your previous setting will be automatically removed and replaced with the new one.", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("set_FreeBot") & filters.private)
async def set_freebot(client, message):
    header = get_header(message.from_user.id)
    text = f"{header}🚀 Please select the premium free bot you want to use\n\n⚠️ Note:\nYou can select only one bot at a time. Once selected, it cannot be changed.\nPlease choose carefully\n\n🎯 Choose a bot below:"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 YouTube Downloader Bot", callback_data="freebot|yt")],
        [InlineKeyboardButton("🎵 TikTok Downloader Bot", callback_data="freebot|tiktok")],
        [InlineKeyboardButton("🐦 X Downloader Bot", callback_data="freebot|x")],
        [InlineKeyboardButton("📘 Facebook Downloader Bot", callback_data="freebot|fb")],
        [InlineKeyboardButton("📸 Instagram Downloader Bot", callback_data="freebot|insta")]
    ])
    await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^freebot\|(.*)$"))
async def save_freebot(client, callback_query):
    bot_type = callback_query.data.split("|")[1]
    users_db.update_one({"user_id": callback_query.from_user.id}, {"$set": {"free_bot": bot_type}})
    header = get_header(callback_query.from_user.id)
    await callback_query.message.edit_text(f"{header}✅ Your settings have been updated successfully\n\n📌 You can now check them anytime", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("wallpaper") & filters.private)
async def wallpaper_cmd(client, message):
    user = users_db.find_one({"user_id": message.from_user.id})
    header = get_header(message.from_user.id)
    if user.get("plan", "FREE") == "FREE":
        await message.reply_text(f"{header}⚠️ You need to be a PREMIUM member to use this feature.", parse_mode=enums.ParseMode.HTML)
        return
    users_db.update_one({"user_id": message.from_user.id}, {"$set": {"state": "wallpaper_link"}})
    await message.reply_text(f"{header}📩 Please send a YouTube link or video\n\n📌 This will help us create your wallpaper and send it to you", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("setcookies") & filters.private)
async def set_cookies_command(client, message):
    header = get_header(message.from_user.id)
    await message.reply_text(f"{header}🍪 <b>Cookies Updater</b>\nPlease upload your fresh <code>cookies.txt</code> file here as a document.", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.document & filters.private)
async def receive_cookies_file(client, message):
    if message.document.file_name and message.document.file_name.lower() == "cookies.txt":
        header = get_header(message.from_user.id)
        msg = await message.reply_text(f"{header}📥 Downloading cookies...", parse_mode=enums.ParseMode.HTML)
        file_path = os.path.join(os.getcwd(), "cookies.txt")
        if os.path.exists(file_path): os.remove(file_path)
        await client.download_media(message, file_name=file_path)
        await msg.edit_text(f"{header}✅ Cookies Updated Successfully!", parse_mode=enums.ParseMode.HTML)
