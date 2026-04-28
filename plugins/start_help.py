import os
import asyncio
from pyrogram import Client, filters, enums, StopPropagation
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from database import users_db
import config
from datetime import datetime, timezone, timedelta

# IST Setup
IST = timezone(timedelta(hours=5, minutes=30))

# 🌟 ఫుల్ స్పేస్ & బోల్డ్ బ్రాండింగ్ 🌟
def get_header(user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    if plan == "PREMIUM": 
        return "<blockquote><b>💎 Velveta Premium User                                                                                                                                                                                                        </b>                                                                                                                    </blockquote>\n"
    elif plan == "ADS": 
        return "<blockquote><b> 📺 Velveta Semi Premium User                                                                                                                                                                                                                                                                             </b>                                                                                                                                                   </blockquote>\n"
    else: 
        return ""

async def check_joined(client, user_id):
    try:
        await client.get_chat_member("@Velvetabots", user_id)
        return True
    except UserNotParticipant: return False
    except Exception: return False

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    user_id = message.from_user.id
    
    if not users_db.find_one({"user_id": user_id}):
        users_db.insert_one({
            "user_id": user_id, 
            "plan": "FREE", 
            "plan_started": datetime.now(IST).strftime("%Y-%m-%d"),
            "trial_claimed": False
        })

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
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Our Updated Channel 📢", url="https://t.me/Velvetabots")]
    ])
    
    # 🌟 స్టార్ట్ చేయగానే బెదిరించకుండా కేవలం వెల్కమ్ చెప్తుంది 🌟
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
        f"👉 /my_plan – Check your plan\n"
        f"👉 /transfer_premium – Transfer your plan\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"💡 <b>Tip:</b> Send link → Select quality → Done ⚡\n\n"
        f"❓ <b>Support</b>\n"
        f"💬 @Velvetasupport"
    )
    await message.reply_text(help_text, parse_mode=enums.ParseMode.HTML)

# ==========================================
# 🌟 EXACT MY_PLAN FORMATS YOU REQUESTED 🌟
# ==========================================
@Client.on_message(filters.command("my_plan") & filters.private)
async def my_plan_cmd(client, message):
    user_id = message.from_user.id
    user_data = users_db.find_one({"user_id": user_id})
    plan = user_data.get("plan", "FREE") if user_data else "FREE"
    header = get_header(user_id)

    if plan == "PREMIUM":
        amount = user_data.get("amount_paid", "N/A")
        started = user_data.get("plan_started")
        expiry = user_data.get("expiry_date")
        
        started_str = started.replace(tzinfo=timezone.utc).astimezone(IST).strftime('%Y-%m-%d %I:%M %p') if started else "Unknown"
        expiry_str = expiry.replace(tzinfo=timezone.utc).astimezone(IST).strftime('%Y-%m-%d %I:%M %p') if expiry else "Unknown"

        text = (
            f"{header}"
            f"👤 User Dashboard\n"
            f"🆔 ID: {user_id}\n"
            f"📦 Plan: PREMIUM\n"
            f"🧾 Amount Paid: {amount}\n"
            f"📅 Started: {started_str}\n"
            f"⏳ Validity: {expiry_str} (IST)\n\n"
            f"━━━━━━━━━━━━━━\n"
            f"🚀 Features:\n"
            f"✔️ Unlimited Downloads\n"
            f"✔️ Playlist Downloads\n"
            f"✔️ Fast Download Speed\n"
            f"✔️ High Priority Support\n"
            f"✔️ Premium Banner Access\n"
            f"✔️ Scheduled Downloads\n"
            f"✔️ Save Videos\n"
            f"✔️ Transfer Premium\n"
            f"✔️ Multi-Platform Access (YT, TikTok, FB, X, Instagram)\n"
            f"✔️ Auto Repair Link\n"
            f"✔️ Wallpaper Setup\n"
            f"✔️ Advanced Content Downloads\n"
            f"✔️ Quality Selection\n"
            f"✔️ Set Preferred Quality\n\n"
            f"━━━━━━━━━━━━━━\n"
            f"💬 Need help? @Velvetasupport"
        )
        await message.reply_text(text, parse_mode=enums.ParseMode.HTML)

    elif plan == "ADS":
        amount = user_data.get("amount_paid", "1 Ad")
        started = user_data.get("plan_started")
        expiry = user_data.get("expiry_date")
        
        started_str = started.replace(tzinfo=timezone.utc).astimezone(IST).strftime('%Y-%m-%d') if started else "Unknown"
        
        time_left = expiry.replace(tzinfo=timezone.utc).astimezone(IST) - datetime.now(IST) if expiry else timedelta(0)
        days, seconds = time_left.days, time_left.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        validity_str = f"{days}d {hours}h {minutes}m" if days > 0 else f"{hours}h {minutes}m"

        text = (
            f"{header}"
            f"👤 User Dashboard\n"
            f"🆔 ID: {user_id}\n"
            f"📦 Plan: ADS\n"
            f"🧾 Payment: {amount}\n"
            f"📅 Started On: {started_str}\n\n"
            f"⏳ Time Remaining: {validity_str}\n\n"
            f"━━━━━━━━━━━━━━\n"
            f"🚀 Features:\n"
            f"✔️ Unlimited Downloads\n"
            f"✔️ Fast Download Speed\n"
            f"✔️ Basic Support (Group)\n"
            f"✔️ Premium Banner Access\n"
            f"✔️ Anti Crash Protection\n"
            f"✔️ Quality Selection\n\n"
            f"━━━━━━━━━━━━━━\n"
            f"📊 Status: Active ✅\n\n"
            f"👉 Send a YouTube link to start downloading\n"
            f"👉 Use my_plan to check remaining time anytime"
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade", callback_data="show_upgrade")]])
        await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

    else:
        started = user_data.get("plan_started") if user_data else "Unknown"
        if isinstance(started, datetime):
            started = started.replace(tzinfo=timezone.utc).astimezone(IST).strftime('%Y-%m-%d')
        
        text = (
            f"{header}"
            f"👤 User Dashboard\n"
            f"🆔 ID: {user_id}\n"
            f"📦 Plan: FREE\n"
            f"📅 Started: {started}\n"
            f"⏳ Validity: Unlimited\n"
            f"━━━━━━━━━━━━━━\n"
            f"🚀 Features:\n"
            f"✔️ Limited Downloads per day\n"
            f"✔️ Standard Speed\n"
            f"✔️ Basic Support\n"
            f"✔️ Manual Quality Selection\n"
            f"✔️ Access up to 720p\n"
            f"✔️ Save Videos (Limited)\n"
            f"━━━━━━━━━━━━━━\n"
            f"⚠️ Limitations:\n"
            f"❌ No 1080p / 2K / 4K\n"
            f"❌ No Priority Speed\n"
            f"❌ No Scheduling (or Limited)\n"
            f"❌ No Wallpaper Feature\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 Upgrade to unlock full features 🚀\n"
            f"💬 Need help? @Velvetasupport"
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade", callback_data="show_upgrade")]])
        await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

# ==========================================
# 🌟 GLOBAL FORCE SUB INTERCEPTOR (10 Mins Background Check) 🌟
# ==========================================
@Client.on_message(filters.incoming & filters.private & ~filters.command(["start"]), group=-9)
async def force_sub_interceptor(client, message):
    user_id = message.from_user.id
    
    if await check_joined(client, user_id):
        return # యూజర్ జాయిన్ అయితే వేరే బాట్ ఫైల్స్ కి మెసేజ్ ని పంపిస్తుంది
        
    # జాయిన్ అవ్వకపోతే మెసేజ్ ని పట్టుకుంటుంది
    text = "⛔️ <b>Access Denied</b> ⛔️\n\n🙋‍♂️ Hey User, You Must Join <b>@Velvetabots</b> Telegram Channel To Use This BOT. So, Please Join it 🤗. Thank You 🤝"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Update Channel", url="https://t.me/Velvetabots")], 
        [InlineKeyboardButton("☑️ Joined", callback_data="force_sub_joined")]
    ])
    
    sent_msg = await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
    
    # బాట్ ప్రాసెస్ ని ఇక్కడే ఆపేస్తుంది (వేరే ఫైల్స్ కి వెళ్లనివ్వదు)
    message.stop_propagation()

    # 🌟 10 నిమిషాల ఆటో చెక్కర్ (యూజర్ జాయిన్ అవ్వగానే వెంటనే స్టార్ట్ చేస్తుంది) 🌟
    for _ in range(600):
        await asyncio.sleep(1)
        if await check_joined(client, user_id):
            try: await sent_msg.delete()
            except: pass
            
            # యూజర్ ఏ లింక్/కమాండ్ పెట్టాడో దాన్ని ఆటోమేటిక్ గా రన్ చేస్తుంది
            from plugins.engine import text_handler
            if "youtube.com" in message.text or "youtu.be" in message.text:
                await text_handler(client, message)
            else:
                await message.reply_text("✅ <b>Verified!</b> You can now use the bot.")
            return
