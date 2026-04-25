import os
import re
from datetime import datetime
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.exceptions import StopPropagation
from database import users_db
import config

# 🌟 ఫుల్ స్పేస్ & బోల్డ్ బ్రాండింగ్ 🌟
def get_header(user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    if plan == "PREMIUM": return "<blockquote><b>💎 Velveta Premium User</b>\n</blockquote>\n\n"
    elif plan == "ADS_PREMIUM": return "<blockquote><b>💎 Velveta Semi Premium User</b>\n</blockquote>\n\n"
    else: return ""

def extract_yt_id(text):
    match = re.search(r"(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})", text)
    return match.group(2) if match else None

# 🌟 క్యాన్సిల్ బటన్ లాజిక్ 🌟
@Client.on_callback_query(filters.regex(r"^cancel_action$"))
async def cancel_action_handler(client, callback_query):
    users_db.update_one({"user_id": callback_query.from_user.id}, {"$set": {"state": None}})
    await callback_query.message.edit_text(f"{get_header(callback_query.from_user.id)}❌ Action cancelled.", parse_mode=enums.ParseMode.HTML)

# ==========================================
# 1. SCHEDULE COMMAND & LOGIC
# ==========================================
@Client.on_message(filters.command("schedule") & filters.private)
async def schedule_cmd(client, message):
    users_db.update_one({"user_id": message.from_user.id}, {"$set": {"state": "schedule_link"}})
    header = get_header(message.from_user.id)
    text = f"{header}🎬 Please send the YouTube link you want to schedule\n\n👉 Make sure it is a valid link (https://)"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]])
    await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

# ==========================================
# 2. SAVE COMMAND & LOGIC
# ==========================================
@Client.on_message(filters.command("save") & filters.private)
async def save_cmd(client, message):
    users_db.update_one({"user_id": message.from_user.id}, {"$set": {"state": "save_content"}})
    header = get_header(message.from_user.id)
    text = f"{header}📩 Please send the YouTube link or video\n\n📌 So we can process and save your content"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]])
    await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

# ==========================================
# 3. DELETE COMMAND LOGIC
# ==========================================
@Client.on_message(filters.command(["delete", "delete_save"]) & filters.private)
async def delete_save_cmd(client, message):
    users_db.update_one({"user_id": message.from_user.id}, {"$set": {"saved_link": None}})
    header = get_header(message.from_user.id)
    text = f"{header}🗑️ Your saved content has been deleted successfully\n\n📌 You no longer have any saved items\n\n👉 Send /save to add new content"
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)

# ==========================================
# 4. STATE MANAGER (ప్రాధాన్యత: engine.py కంటే ముందు రన్ అవుతుంది)
# ==========================================
@Client.on_message((filters.text | filters.video) & filters.private, group=-2)
async def state_manager(client, message):
    user_id = message.from_user.id
    user = users_db.find_one({"user_id": user_id}) or {}
    state = user.get("state")
    header = get_header(user_id)

    if not state:
        return # ఎలాంటి స్టేట్ లేకపోతే దీన్ని వదిలేసి engine.py కి పంపిస్తుంది.

    # --- SAVE LINK STATE ---
    if state == "save_content":
        if message.video:
            file_id = message.video.file_id
            users_db.update_one({"user_id": user_id}, {"$set": {"saved_link": f"vid:{file_id}", "state": None}})
        else:
            yt_id = extract_yt_id(message.text)
            if not yt_id:
                await message.reply_text(f"{header}❌ Invalid YouTube Link. Please try again or click Cancel.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]]), parse_mode=enums.ParseMode.HTML)
                raise StopPropagation
            # కేవలం లింక్‌ని మాత్రమే సేవ్ చేస్తున్నాం, డౌన్‌లోడ్ చేయము (Storage saves!)
            users_db.update_one({"user_id": user_id}, {"$set": {"saved_link": f"https://youtu.be/{yt_id}", "state": None}})
        
        text = f"{header}✅ Your content has been saved successfully\n\n📌 To view what you saved, please send this command: /reveal"
        await message.reply_text(text, parse_mode=enums.ParseMode.HTML)
        raise StopPropagation

    # --- SCHEDULE LINK STATE ---
    elif state == "schedule_link":
        if not message.text:
            raise StopPropagation
        yt_id = extract_yt_id(message.text)
        if not yt_id:
            await message.reply_text(f"{header}❌ Invalid YouTube Link. Please try again or click Cancel.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]]), parse_mode=enums.ParseMode.HTML)
            raise StopPropagation
        
        users_db.update_one({"user_id": user_id}, {"$set": {"state": "schedule_time", "temp_sched_link": yt_id}})
        text = f"{header}⏰ Please select your schedule date & time\n\n📌 Use this format: <b>DDMMYYYY HH:MM</b> (24-hour format)\n\n📍 Example:\n<b>25042026 08:40\n25042026 16:51</b>\n\n👉 Send your date and time now"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]])
        await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
        raise StopPropagation

    # --- SCHEDULE TIME STATE ---
    elif state == "schedule_time":
        if not message.text:
            raise StopPropagation
        try:
            dt_obj = datetime.strptime(message.text.strip(), "%d%m%Y %H:%M")
            time_str = dt_obj.strftime("%d%m%Y %H:%M")
        except ValueError:
            await message.reply_text(f"{header}❌ Invalid format. Please use <b>DDMMYYYY HH:MM</b>.\nExample: <b>25042026 08:40</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]]), parse_mode=enums.ParseMode.HTML)
            raise StopPropagation

        yt_id = user.get("temp_sched_link")
        pref_quality = user.get("preferred_quality")

        if pref_quality:
            # యూజర్‌కి డీఫాల్ట్ క్వాలిటీ ఉంటే, డైరెక్ట్ గా షెడ్యూల్ చేసి కింద మెసేజ్ పంపిస్తుంది
            task = {"link": yt_id, "quality": pref_quality, "time": time_str}
            users_db.update_one({"user_id": user_id}, {"$push": {"scheduled_tasks": task}, "$set": {"state": None, "temp_sched_link": None}})
            
            success_text = f"{header}✅ Your link has been scheduled successfully\n\n📌 Your content will be delivered at the selected date & time\n\n⏳ Please make sure the bot remains active to avoid any delays\n\n🙏 Thank you for using our service"
            await message.reply_text(success_text, parse_mode=enums.ParseMode.HTML)
        else:
            # డీఫాల్ట్ క్వాలిటీ లేకపోతే క్వాలిటీ అడుగుతుంది
            users_db.update_one({"user_id": user_id}, {"$set": {"state": None}})
            text = f"{header}🎬 📹 <b>Schedule Quality</b>\n\n👇 <b>Select Quality for Scheduled Video:</b>"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🖥 1080p", callback_data=f"sched_q|1080p|{yt_id}|{time_str}"), InlineKeyboardButton("💻 720p", callback_data=f"sched_q|720p|{yt_id}|{time_str}")],
                [InlineKeyboardButton("📺 480p", callback_data=f"sched_q|480p|{yt_id}|{time_str}"), InlineKeyboardButton("📱 360p", callback_data=f"sched_q|360p|{yt_id}|{time_str}")],
                [InlineKeyboardButton("🎵 Audio", callback_data=f"sched_q|audio|{yt_id}|{time_str}")]
            ])
            await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
        
        raise StopPropagation

# 🌟 క్వాలిటీ బటన్ క్లిక్ చేసిన తర్వాత వచ్చే షెడ్యూల్ సక్సెస్ మెసేజ్ 🌟
@Client.on_callback_query(filters.regex(r"^sched_q\|(.*)\|(.*)\|(.*)$"))
async def sched_quality_selection(client, callback_query):
    _, quality, yt_id, time_str = callback_query.data.split("|")
    user_id = callback_query.from_user.id
    header = get_header(user_id)
    
    task = {"link": yt_id, "quality": quality, "time": time_str}
    users_db.update_one({"user_id": user_id}, {"$push": {"scheduled_tasks": task}, "$set": {"temp_sched_link": None}})
    
    success_text = f"{header}✅ Your link has been scheduled successfully\n\n📌 Your content will be delivered at the selected date & time\n\n⏳ Please make sure the bot remains active to avoid any delays\n\n🙏 Thank you for using our service"
    await callback_query.message.edit_text(success_text, parse_mode=enums.ParseMode.HTML)
