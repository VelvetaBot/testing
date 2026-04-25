import os
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton # 🌟 ఈ లైన్ మిస్ అవ్వడం వల్లే ఎర్రర్ వచ్చింది 🌟
from pyrogram.exceptions import FloodWait
from database import users_db, logs_collection
import config
from datetime import datetime

# అడ్మిన్ ఐడీ చెక్ చేయడానికి ఫంక్షన్
def is_admin(user_id, username):
    admin_id = str(getattr(config.Config, "ADMIN_ID", ""))
    return str(user_id) == admin_id or str(username).lower() == admin_id.lower()

# ==========================================
# 🌟 1. USER TRACKING (స్టేటస్ కౌంట్ కోసం) 🌟
# ==========================================
@Client.on_chat_member_updated()
async def track_user_status(client, event):
    if event.chat.type != enums.ChatType.PRIVATE:
        return
        
    user_id = event.new_chat_member.user.id
    
    # యూజర్ బాట్‌ను స్టార్ట్ చేసినప్పుడు (లేదా అన్‌బ్లాక్ చేసినప్పుడు)
    if event.new_chat_member.status == enums.ChatMemberStatus.MEMBER:
        user = users_db.find_one({"user_id": user_id})
        if not user:
            # కొత్త యూజర్ అయితే ఫ్రీ ప్లాన్ తో డేటాబేస్ లో యాడ్ చేయడం
            users_db.insert_one({
                "user_id": user_id,
                "username": event.new_chat_member.user.username,
                "first_name": event.new_chat_member.user.first_name,
                "plan": "FREE",
                "bot_count": 0,
                "group_count": 0,
                "status": "active",
                "joined_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            # పాత యూజర్ మళ్ళీ వస్తే స్టేటస్ యాక్టివ్ గా మార్చడం
            users_db.update_one({"user_id": user_id}, {"$set": {"status": "active"}})
            
    # యూజర్ బాట్‌ను బ్లాక్ చేసినప్పుడు (లేదా డిలీట్ చేసినప్పుడు)
    elif event.new_chat_member.status == enums.ChatMemberStatus.BANNED:
        users_db.update_one({"user_id": user_id}, {"$set": {"status": "blocked"}})

# ==========================================
# 🌟 2. USERS STATS COMMAND (/users) 🌟
# ==========================================
@Client.on_message(filters.command("users") & filters.private)
async def users_stats_cmd(client, message):
    if not is_admin(message.from_user.id, message.from_user.username):
        return

    total_users = users_db.count_documents({})
    active_users = users_db.count_documents({"status": "active"})
    blocked_users = users_db.count_documents({"status": "blocked"})
    premium_users = users_db.count_documents({"plan": "PREMIUM"})
    ads_users = users_db.count_documents({"plan": "ADS_PREMIUM"})

    stats_text = (
        "📊 <b>Bot Users Statistics</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Users: <b>{total_users}</b>\n"
        f"🟢 Active Users: <b>{active_users}</b>\n"
        f"🔴 Blocked Users: <b>{blocked_users}</b>\n\n"
        "💳 <b>Subscription Stats</b>\n"
        f"💎 Premium Users: <b>{premium_users}</b>\n"
        f"📺 Ads Premium Users: <b>{ads_users}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    await message.reply_text(stats_text, parse_mode=enums.ParseMode.HTML)

# ==========================================
# 🌟 3. GLOBAL NOTIFY COMMAND (/notify) 🌟
# ==========================================
@Client.on_message(filters.command("notify") & filters.private)
async def notify_cmd(client, message):
    if not is_admin(message.from_user.id, message.from_user.username):
        return

    reply_msg = message.reply_to_message
    if not reply_msg:
        await message.reply_text("⚠️ <b>Format Error:</b>\nPlease reply to a message (text, photo, video, etc.) with /notify to send it to all active users.", parse_mode=enums.ParseMode.HTML)
        return

    status_msg = await message.reply_text("⏳ <b>Broadcasting message...</b>\nPlease wait, this might take a while.", parse_mode=enums.ParseMode.HTML)
    
    active_users = users_db.find({"status": "active"})
    success_count = 0
    fail_count = 0

    for user in active_users:
        try:
            await reply_msg.copy(chat_id=user["user_id"])
            success_count += 1
            await asyncio.sleep(0.5) # FloodWait రాకుండా ఉండటానికి ఒక చిన్న గ్యాప్
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
            await reply_msg.copy(chat_id=user["user_id"])
            success_count += 1
        except Exception:
            # మెసేజ్ వెళ్లకపోతే ఆ యూజర్ బ్లాక్ చేసినట్లు లెక్క
            users_db.update_one({"user_id": user["user_id"]}, {"$set": {"status": "blocked"}})
            fail_count += 1

    await status_msg.edit_text(
        f"✅ <b>Broadcast Completed!</b>\n\n"
        f"📬 Successfully sent to: <b>{success_count}</b> users.\n"
        f"❌ Failed (Blocked bot): <b>{fail_count}</b> users.",
        parse_mode=enums.ParseMode.HTML
    )

# ==========================================
# 🌟 4. PROBLEM LOGGING (ఫాల్‌బ్యాక్ ఫెయిల్ అయినప్పుడు) 🌟
# ==========================================
def log_bot_problem(error_message, location):
    """ఈ ఫంక్షన్ ద్వారా ఎక్కడ ఎర్రర్ వచ్చినా దాన్ని డేటాబేస్ లో సేవ్ చేస్తాం"""
    log_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "error": str(error_message),
        "location": str(location),
        "status": "Unresolved"
    }
    logs_collection.insert_one(log_data)

@Client.on_message(filters.command("problems") & filters.private)
async def problems_cmd(client, message):
    if not is_admin(message.from_user.id, message.from_user.username):
        return

    # పరిష్కరించబడని ఎర్రర్స్ ని లాగడం
    unresolved_logs = list(logs_collection.find({"status": "Unresolved"}).sort("_id", -1).limit(10))
    
    if not unresolved_logs:
        await message.reply_text("✅ <b>No Problems Found!</b>\nYour bot is running perfectly fine with 0 errors.", parse_mode=enums.ParseMode.HTML)
        return

    text = "🚨 <b>Recent Bot Problems (Internal Errors)</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for log in unresolved_logs:
        text += f"🕒 <b>Time:</b> {log['timestamp']}\n"
        text += f"📍 <b>Location:</b> {log['location']}\n"
        text += f"❌ <b>Error:</b> <code>{log['error']}</code>\n"
        text += "────────────────────\n"

    # ఇక్కడ కీబోర్డ్ లైన్ కోసం పైన ఇంపోర్ట్ యాడ్ చేశాం!
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🗑 Clear All Logs", callback_data="clear_problems_log")]])
    await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^clear_problems_log$"))
async def clear_logs_callback(client, callback_query):
    if not is_admin(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ You are not an admin!", show_alert=True)
        return

    # డేటాబేస్ లో ఉన్న లాగ్స్ అన్నింటినీ డిలీట్ చేయడం లేదా రిజాల్వ్ చేయడం
    logs_collection.update_many({"status": "Unresolved"}, {"$set": {"status": "Resolved"}})
    await callback_query.message.edit_text("✅ <b>All problem logs have been cleared!</b>", parse_mode=enums.ParseMode.HTML)
