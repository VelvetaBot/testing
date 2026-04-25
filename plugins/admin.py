import os
import asyncio
from datetime import datetime
from pyrogram import Client, filters, enums
from pyrogram.types import ChatMemberUpdated
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from database import users_db
import config

# డేటాబేస్ నుండి అడ్మిన్ స్టాటిస్టిక్స్ కోసం సపరేట్ కలెక్షన్స్
stats_db = users_db.database["statistics"]
errors_db = users_db.database["error_logs"]

# బాట్ స్టార్ట్ అయినప్పుడు స్టాట్స్ డేటాబేస్ లేకపోతే క్రియేట్ చేయడానికి
if not stats_db.find_one({"_id": "bot_stats"}):
    stats_db.insert_one({
        "_id": "bot_stats",
        "total_links": 0,
        "success_downloads": 0,
        "failed_downloads": 0,
        "added_in_groups": 0,
        "group_msgs_deleted": 0,
        "ads_plan_users": 0,
        "money_plan_users": 0,
        "blocked_users_by_admin": 0
    })

def is_admin(user_id, username):
    """యూజర్ అడ్మిన్ అవునా కాదా అని చెక్ చేసే ఫంక్షన్"""
    admin_id = str(getattr(config.Config, "ADMIN_ID", ""))
    return str(user_id) == admin_id or str(username).lower() == admin_id.lower()

def log_bot_problem(error_message, module_name):
    """బాట్ లో ఏ సమస్య వచ్చినా డేటాబేస్ లో రికార్డ్ చేసే ఫంక్షన్"""
    errors_db.insert_one({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "module": module_name,
        "error": str(error_message)
    })

# ==========================================
# 🌟 DEACTIVATED USERS TRACKING (Live Tracking) 🌟
# ==========================================
@Client.on_chat_member_updated(filters.private)
async def track_user_status(client, update: ChatMemberUpdated):
    user_id = update.new_chat_member.user.id
    
    # యూజర్ బాట్‌ను బ్లాక్ చేస్తే (Deactivated)
    if update.new_chat_member.status == enums.ChatMemberStatus.BANNED:
        users_db.update_one({"user_id": user_id}, {"$set": {"deactivated": True}})
        
    # యూజర్ తిరిగి మళ్లీ బాట్‌ను స్టార్ట్ చేస్తే (Re-activated)
    elif update.new_chat_member.status == enums.ChatMemberStatus.MEMBER:
        users_db.update_one({"user_id": user_id}, {"$set": {"deactivated": False}})

# ==========================================
# 📊 USERS COMMAND (Advanced Stats) 📊
# ==========================================
@Client.on_message(filters.command("users") & filters.private)
async def users_stats_cmd(client, message):
    if not is_admin(message.from_user.id, message.from_user.username):
        return # అడ్మిన్ కాకపోతే సైలెంట్ గా వదిలేస్తుంది

    # యాక్టివ్ మరియు డీ-యాక్టివేటెడ్ యూజర్ల కౌంట్
    active_users = users_db.count_documents({"deactivated": {"$ne": True}})
    deactivated_users = users_db.count_documents({"deactivated": True})
    
    # స్టాటిస్టిక్స్ కలెక్షన్ నుండి డేటా తీసుకురావడం
    stats = stats_db.find_one({"_id": "bot_stats"}) or {}
    
    # డేటాబేస్ నుండి ప్లాన్స్ కౌంట్ తీసుకోవడం (డైనమిక్ గా)
    ads_users = users_db.count_documents({"plan": "ADS_PREMIUM"})
    money_users = users_db.count_documents({"plan": "PREMIUM"})

    stats_text = (
        "📊 <b>Advanced Bot Statistics</b>\n\n"
        f"👥 Total Users: {active_users}\n"
        f"🛑 Total Deactivated: {deactivated_users}\n"
        f"🔗 Total Links: {stats.get('total_links', 0)}\n"
        f"✅ Success Downloads: {stats.get('success_downloads', 0)}\n"
        f"❌ Failed Downloads: {stats.get('failed_downloads', 0)}\n"
        f"🏘 Added in Groups: {stats.get('added_in_groups', 0)}\n"
        f"🗑 Group Msgs Deleted: {stats.get('group_msgs_deleted', 0)}\n"
        f"📺 Ads plan:- {ads_users}\n"
        f"💎 Money plan:- {money_users}\n"
        f"🚫 Blocked Users: {stats.get('blocked_users_by_admin', 0)}\n"
    )
    
    await message.reply_text(stats_text, parse_mode=enums.ParseMode.HTML)

# ==========================================
# 📢 NOTIFY COMMAND (Broadcast System) 📢
# ==========================================
@Client.on_message(filters.command("notify") & filters.private)
async def notify_cmd(client, message):
    if not is_admin(message.from_user.id, message.from_user.username):
        return

    # '/notify' పదాన్ని కట్ చేసి మిగిలిన మెసేజ్ తీసుకోవడం
    if message.reply_to_message:
        # ఏదైనా మెసేజ్‌కి రిప్లై ఇస్తూ కమాండ్ ఇస్తే ఆ మెసేజ్‌ని తీసుకుంటుంది
        broadcast_msg = message.reply_to_message
        text_to_send = broadcast_msg.text or broadcast_msg.caption or ""
    else:
        # డైరెక్ట్ గా మెసేజ్ ఇస్తే (మీడియాతో సహా) దాన్ని తీసుకుంటుంది
        broadcast_msg = message
        if message.text:
            text_to_send = message.text.replace("/notify", "").strip()
        elif message.caption:
            text_to_send = message.caption.replace("/notify", "").strip()
        else:
            await message.reply_text("⚠️ Please provide a message or media to broadcast.")
            return

    if not text_to_send and not broadcast_msg.media:
        await message.reply_text("⚠️ Please provide a valid message to broadcast.")
        return

    # బ్రాడ్‌కాస్ట్ ప్రాసెస్ స్టార్ట్
    proc_msg = await message.reply_text("📢 <b>Broadcast Started...</b>\nPlease wait, sending to all users.", parse_mode=enums.ParseMode.HTML)
    
    success = 0
    failed = 0
    deactivated = 0
    
    # డేటాబేస్ లోని యూజర్లందరినీ లూప్ చేయడం
    users = users_db.find()
    
    for user in users:
        user_id = user["user_id"]
        try:
            # మీడియా ఉంటే మీడియా, టెక్స్ట్ ఉంటే టెక్స్ట్ పంపుతుంది
            if broadcast_msg.media and not message.reply_to_message:
                await broadcast_msg.copy(chat_id=user_id, caption=text_to_send, parse_mode=enums.ParseMode.HTML)
            elif broadcast_msg.media and message.reply_to_message:
                await broadcast_msg.copy(chat_id=user_id)
            else:
                await client.send_message(chat_id=user_id, text=text_to_send, parse_mode=enums.ParseMode.HTML)
            success += 1
            
            # టెలిగ్రామ్ స్పామ్ లిమిట్స్ తగలకుండా (Anti-Ban)
            await asyncio.sleep(0.1) 
            
        except FloodWait as e:
            await asyncio.sleep(e.value)
            failed += 1
        except (UserIsBlocked, InputUserDeactivated):
            # యూజర్ బ్లాక్ చేసి ఉంటే డేటాబేస్ లో డీ-యాక్టివేట్ కింద అప్‌డేట్ చేస్తుంది
            users_db.update_one({"user_id": user_id}, {"$set": {"deactivated": True}})
            deactivated += 1
            failed += 1
        except Exception:
            failed += 1

    await proc_msg.edit_text(
        f"📢 <b>Broadcast Completed!</b>\n\n"
        f"✅ Sent Successfully: {success}\n"
        f"❌ Failed: {failed}\n"
        f"🛑 Automatically Deactivated: {deactivated} users",
        parse_mode=enums.ParseMode.HTML
    )

# ==========================================
# 🛠 PROBLEMS COMMAND (Error Tracker) 🛠
# ==========================================
@Client.on_message(filters.command("problems") & filters.private)
async def problems_cmd(client, message):
    if not is_admin(message.from_user.id, message.from_user.username):
        return

    # డేటాబేస్ నుండి రీసెంట్ 10 ఎర్రర్స్ తీసుకురావడం
    recent_errors = list(errors_db.find().sort("_id", -1).limit(10))
    
    if not recent_errors:
        await message.reply_text("✅ <b>No Problems Found!</b>\nYour bot is running perfectly fine with 0 errors.", parse_mode=enums.ParseMode.HTML)
        return

    problems_text = "🛠 <b>Bot Error Logs (Recent 10)</b> 🛠\n\n"
    for i, err in enumerate(recent_errors, 1):
        problems_text += f"<b>{i}. Time:</b> {err.get('time')}\n"
        problems_text += f"<b>Module:</b> {err.get('module')}\n"
        problems_text += f"<b>Error:</b> <code>{err.get('error')}</code>\n"
        problems_text += "━━━━━━━━━━━━━━━━\n"

    # ఇక్కడ అడ్మిన్ కి లాగ్స్ క్లియర్ చేసుకునే అవకాశం కూడా ఇస్తున్నాను
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🗑 Clear All Logs", callback_data="clear_problems_log")]])
    await message.reply_text(problems_text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^clear_problems_log$"))
async def clear_logs_callback(client, callback_query):
    if not is_admin(callback_query.from_user.id, callback_query.from_user.username):
        return
    errors_db.delete_many({}) # లాగ్స్ అన్నీ క్లియర్
    await callback_query.message.edit_text("✅ <b>All Error Logs Cleared Successfully!</b>", parse_mode=enums.ParseMode.HTML)

