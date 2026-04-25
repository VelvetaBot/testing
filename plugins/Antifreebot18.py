import os
import time
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from database import users_db

# ==========================================
# 🌟 MULTI-BOT TOKENS & DATABASES 🌟
# (మీరు తర్వాత మీ ఒరిజినల్ డీటెయిల్స్ ఇక్కడ పేస్ట్ చేసుకోండి)
# ==========================================

# TikTok Downloader
TIKTOK_BOT_TOKEN = "paste here"
TIKTOK_DB = "paste here"

# X (Twitter) Downloader
X_BOT_TOKEN = "paste here"
X_DB = "paste here"

# Facebook Downloader
FB_BOT_TOKEN = "paste here"
FB_DB = "paste here"

# Instagram Downloader
INSTA_BOT_TOKEN = "paste here"
INSTA_DB = "paste here"

# ==========================================
# 🌟 18+ (NSFW) CONTENT SUPPORT ENABLED 🌟
# ==========================================
# ఈ ఫ్లాగ్ ద్వారా సిస్టమ్ 18+ కంటెంట్ ని అలో చేస్తుంది.
# yt-dlp కుకీస్ తో కలిసి పనిచేసి ఏజ్-రిస్ట్రిక్షన్స్ ని బైపాస్ చేస్తుంది.
ALLOW_18PLUS_CONTENT = True 

# ==========================================
# 🌟 ANTI-SPEED (SPAM) & ANTI-CRASH SYSTEM 🌟
# ==========================================
SPAM_TRACKER = {}
COOLDOWN_SECONDS = 2 # యూజర్ ఒక మెసేజ్ కి, ఇంకో మెసేజ్ కి మధ్య కనీసం 2 సెకన్లు గ్యాప్ ఉండాలి

def check_anti_speed(user_id):
    """
    యూజర్ స్పామ్ చేస్తే (స్పీడ్ గా నొక్కితే) బాట్ క్రాష్ అవ్వకుండా అడ్డుకుంటుంది.
    """
    current_time = time.time()
    if user_id in SPAM_TRACKER:
        if current_time - SPAM_TRACKER[user_id] < COOLDOWN_SECONDS:
            return True # స్పామ్ జరుగుతోంది, దీన్ని ఇగ్నోర్ చేయాలి
    SPAM_TRACKER[user_id] = current_time
    return False

# 🌟 ఫుల్ స్పేస్ & బోల్డ్ బ్రాండింగ్ 🌟
def get_header(user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    if plan == "PREMIUM": return "<blockquote><b>💎 VELVETA PREMIUM USER 💎\n━━━━━━━━━━━━━━━━━━━━━</b></blockquote>\n\n"
    elif plan == "ADS_PREMIUM": return "<blockquote><b>📺 VELVETA SEMI PREMIUM 📺\n━━━━━━━━━━━━━━━━━━━━━</b></blockquote>\n\n"
    else: return ""

# ==========================================
# 🌟 FREE BOT SELECTION LOGIC 🌟
# ==========================================
@Client.on_message(filters.command(["set_FreeBot", "set_freebot"]) & filters.private)
async def freebot_selection_cmd(client, message):
    user_id = message.from_user.id
    
    # 🛡️ Anti-Speed Protection 🛡️
    if check_anti_speed(user_id):
        return # స్పామ్ చేస్తే సైలెంట్ గా వదిలేస్తుంది (క్రాష్ అవ్వదు)

    try:
        user = users_db.find_one({"user_id": user_id}) or {}
        header = get_header(user_id)

        # యూజర్ ఇప్పటికే బాట్‌ను ఎంచుకున్నారో లేదో చెక్ చేయడం (కండిషన్: Cannot be changed)
        if user.get("free_bot"):
            await message.reply_text(
                f"{header}⚠️ <b>Already Selected!</b>\n\n"
                f"You have already chosen the <b>{user.get('free_bot')}</b>.\n"
                f"As per our policy, you can select only one bot at a time, and once selected, it cannot be changed.",
                parse_mode=enums.ParseMode.HTML
            )
            return

        text = (
            f"{header}🚀 Please select the premium free bot you want to use\n\n"
            f"⚠️ Note:\n"
            f"You can select only one bot at a time. Once selected, it cannot be changed.\n"
            f"Please choose carefully\n\n"
            f"🎯 Choose a bot below:"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 YouTube Downloader Bot", callback_data="freebot|YouTube Downloader Bot")],
            [InlineKeyboardButton("🎵 TikTok Downloader Bot", callback_data="freebot|TikTok Downloader Bot")],
            [InlineKeyboardButton("🐦 X Downloader Bot", callback_data="freebot|X Downloader Bot")],
            [InlineKeyboardButton("📘 Facebook Downloader Bot", callback_data="freebot|Facebook Downloader Bot")],
            [InlineKeyboardButton("📸 Instagram Downloader Bot", callback_data="freebot|Instagram Downloader Bot")]
        ])

        await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

    # 🛡️ Anti-Crash Protection 🛡️
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        print(f"Anti-Crash System Saved Bot: {e}")

@Client.on_callback_query(filters.regex(r"^freebot\|(.*)$"))
async def save_freebot_selection(client, callback_query):
    user_id = callback_query.from_user.id
    
    # 🛡️ Anti-Speed Protection 🛡️
    if check_anti_speed(user_id):
        await callback_query.answer("Please wait a moment...", show_alert=False)
        return

    try:
        bot_choice = callback_query.data.split("|")[1]
        header = get_header(user_id)
        user = users_db.find_one({"user_id": user_id}) or {}

        # డబుల్ క్లిక్ ఎర్రర్స్ ని అడ్డుకోవడానికి మళ్ళీ ఒకసారి చెక్ చేయడం
        if user.get("free_bot"):
            await callback_query.answer("You have already selected a bot!", show_alert=True)
            return

        # డేటాబేస్‌లో యూజర్ ఎంచుకున్న బాట్‌ను సేవ్ చేయడం
        users_db.update_one({"user_id": user_id}, {"$set": {"free_bot": bot_choice}})
        
        success_text = (
            f"{header}✅ Your settings have been updated successfully\n\n"
            f"📌 You can now check them anytime"
        )
        await callback_query.message.edit_text(success_text, parse_mode=enums.ParseMode.HTML)

    # 🛡️ Anti-Crash Protection 🛡️
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        print(f"Anti-Crash System Triggered in Callback: {e}")
        await callback_query.answer("An error occurred. System is safe.", show_alert=True)
