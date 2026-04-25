import os
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from database import users_db
import config
from datetime import datetime

# 🌟 ఫుల్ స్పేస్ & బోల్డ్ బ్రాండింగ్ 🌟
def get_header(user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    if plan == "PREMIUM": return "<blockquote><b>💎 Velveta Premium User                                                                                                                                                                                                        </b></blockquote>"
    elif plan == "ADS_PREMIUM": return "<blockquote><b> 📺 Velveta Semi Premium User                                                                                                                                                                                                                                                                             </b></blockquote>"
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
    
    # యూజర్ డేటాబేస్ రిజిస్ట్రేషన్
    if not users_db.find_one({"user_id": user_id}):
        users_db.insert_one({
            "user_id": user_id, 
            "plan": "FREE", 
            "plan_started": datetime.now().strftime("%Y-%m-%d"), 
            "bot_count": 0, 
            "group_count": 0, 
            "last_limit_date": datetime.now().strftime("%Y-%m-%d")
        })

    # ఫోర్స్ సబ్ (Force Sub) చెకింగ్
    is_joined = await check_joined(client, user_id)
    if not is_joined:
        text = "⛔️ <b>Access Denied</b> ⛔️\n\n🙋‍♂️ Hey User, You Must Join <b>@Velvetabots</b> Telegram Channel To Use This BOT. So, Please Join it 🤗. Thank You 🤝"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Update Channel", url="https://t.me/Velvetabots")], 
            [InlineKeyboardButton("☑️ Joined", callback_data="check_joined_button")]
        ])
        await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
        return

    users_db.update_one({"user_id": user_id}, {"$set": {"state": None}})
    header = get_header(user_id)
    
    welcome_text = (
        f"{header}"
        f"🌟 <u><b>Welcome to Velveta YouTube Downloader (Pro)!</b></u>🌟\n"
        f"I can download YouTube videos up to <b>2GB</b> with <b>fast, smooth & premium performance</b>🚀\n\n"
        f"<u><b>How to use:</b></u>\n"
        f"1️⃣ Send a YouTube link 🔗\n"
        f"2️⃣ Get your file instantly 📥\n"
        f"3️⃣ For more details, send <b>/help</b>"
    )
    
    # వెల్కమ్ మెసేజ్ కింద ఛానల్ బటన్
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Our Updated Channel 📢", url="https://t.me/Velvetabots")]
    ])
    
    await message.reply_text(welcome_text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    header = get_header(message.from_user.id)
    
    help_text = (
        f"{header}"
        f"🆘 <b>Help Centre</b>\n\n"
        f"🚀 <b>Getting Started</b>\n"
        f"👉 /start – Open the bot\n\n"
        f"🎬 <b>Downloading</b>\n"
        f"👉 Send a YouTube link to download\n"
        f"👉 Select quality and receive your file\n\n"
        f"⏰ <b>Extra Features</b>\n"
        f"👉 /schedule – Schedule a YouTube link\n"
        f"👉 /save – Save a link or video\n"
        f"👉 /reveal – View saved content\n"
        f"👉 /delete_save – Delete saved content\n\n"
        f"⚙️ <b>Settings</b>\n"
        f"👉 /set_preferred_quality – Set default quality\n"
        f"👉 /set_freebot – Select your bot\n"
        f"👉 /wallpaper – Create wallpaper\n\n"
        f"💳 <b>Plans & Account</b>\n"
        f"👉 /upgrade – View & upgrade plans\n"
        f"👉 /my_plan – Check your plan\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"💡 <b>Tip:</b> Send link → Select quality → Done ⚡\n\n"
        f"❓ <b>Support</b>\n"
        f"💬 @Velvetasupport"
    )
    
    await message.reply_text(help_text, parse_mode=enums.ParseMode.HTML)
