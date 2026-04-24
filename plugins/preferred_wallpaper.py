import os
import re
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

# ==========================================
# 1. PREFERRED QUALITY COMMAND & LOGIC
# ==========================================
@Client.on_message(filters.command(["set_preferred_quality", "set_pref_quality"]) & filters.private)
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
    quality = callback_query.data.split("|")[1]
    users_db.update_one({"user_id": callback_query.from_user.id}, {"$set": {"preferred_quality": quality}})
    header = get_header(callback_query.from_user.id)
    
    text = (
        f"{header}✅ Your preferred quality has been set successfully\n\n"
        f"⚠️ Important Note:\nIf the selected quality is not available, the downloader will automatically switch to the nearest available quality\n\n"
        f"🔄 If you use the command /set_preferred_quality again, your previous setting will be automatically removed and replaced with the new one."
    )
    await callback_query.message.edit_text(text, parse_mode=enums.ParseMode.HTML)

# ==========================================
# 2. WALLPAPER COMMAND & LOGIC
# ==========================================
@Client.on_message(filters.command("wallpaper") & filters.private)
async def wallpaper_cmd(client, message):
    user_id = message.from_user.id
    user = users_db.find_one({"user_id": user_id}) or {}
    header = get_header(user_id)
    
    # 🌟 ప్రీమియం చెక్: ఫ్రీ యూజర్లయితే ఆపేస్తుంది 🌟
    if user.get("plan", "FREE") == "FREE":
        error_text = f"{header}🚫 <b>Premium Feature Only</b> 🚫\n\nDear user, you need to buy a Premium Plan to use this custom wallpaper service. Please upgrade your plan to unlock this feature!"
        await message.reply_text(error_text, parse_mode=enums.ParseMode.HTML)
        return

    users_db.update_one({"user_id": user_id}, {"$set": {"state": "wallpaper_link"}})
    text = f"{header}📩 Please send a YouTube link or video\n\n📌 This will help us create your wallpaper and send it to you"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]])
    await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

# ==========================================
# 3. WALLPAPER STATE MANAGER (Group -3)
# ==========================================
@Client.on_message((filters.text | filters.video | filters.photo | filters.document) & filters.private, group=-3)
async def wallpaper_state_manager(client, message):
    user_id = message.from_user.id
    user = users_db.find_one({"user_id": user_id}) or {}
    state = user.get("state")
    header = get_header(user_id)

    if not state:
        return

    # --- WALLPAPER LINK STATE ---
    if state == "wallpaper_link":
        if message.video:
            file_id = message.video.file_id
            users_db.update_one({"user_id": user_id}, {"$set": {"temp_wall_link": f"vid:{file_id}", "state": "wallpaper_photo"}})
        elif message.text:
            yt_id = extract_yt_id(message.text)
            if not yt_id:
                await message.reply_text(f"{header}❌ Invalid YouTube Link. Please try again or click Cancel.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]]), parse_mode=enums.ParseMode.HTML)
                raise StopPropagation
            users_db.update_one({"user_id": user_id}, {"$set": {"temp_wall_link": message.text, "state": "wallpaper_photo"}})
        else:
            raise StopPropagation
        
        text = f"{header}🖼️ Please send the wallpaper you want to set\n\n📌 Supported format: .jpg"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]])
        await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
        raise StopPropagation

    # --- WALLPAPER PHOTO STATE ---
    elif state == "wallpaper_photo":
        is_photo = bool(message.photo)
        is_jpg_doc = bool(message.document and message.document.file_name and message.document.file_name.lower().endswith('.jpg'))
        
        if not (is_photo or is_jpg_doc):
            await message.reply_text(f"{header}❌ Please send a valid .jpg photo.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]]), parse_mode=enums.ParseMode.HTML)
            raise StopPropagation

        proc_msg = await message.reply_text(f"{header}📥 Your photo has been received\n\n⏳ Please wait a moment while we process your request", parse_mode=enums.ParseMode.HTML)
        
        # ఫోటో డౌన్‌లోడ్ మరియు సేవింగ్
        if not os.path.exists("downloads"): os.makedirs("downloads")
        photo_path = os.path.join("downloads", f"{user_id}_wallpaper.jpg")
        if os.path.exists(photo_path): os.remove(photo_path)
        await client.download_media(message, file_name=photo_path)
        
        users_db.update_one({"user_id": user_id}, {"$set": {"wallpaper_path": photo_path, "state": None}})
        link = user.get("temp_wall_link")
        users_db.update_one({"user_id": user_id}, {"$set": {"temp_wall_link": None}})

        if link.startswith("vid:"):
            # డైరెక్ట్ గా టెలిగ్రామ్ వీడియో పంపితే దానికి వాల్‌పేపర్ అంటించి పంపుతుంది
            await client.send_video(user_id, link.split("vid:")[1], thumb=photo_path, caption=f"{header}🎬 Here is your video with custom wallpaper!")
            await proc_msg.delete() # మీరు అడిగినట్లుగా మెసేజ్ డిలీట్ అవుతుంది
        else:
            # యూట్యూబ్ లింక్ ఇస్తే (ప్రీమియం వాళ్ళే ఇక్కడికి వస్తారు కాబట్టి క్వాలిటీ బటన్స్ చూపిస్తుంది)
            from plugins.engine import show_quality_buttons, extract_yt_id
            yt_id = extract_yt_id(link)
            await proc_msg.delete() # ప్రాసెసింగ్ మెసేజ్ డిలీట్
            await show_quality_buttons(client, message, link, yt_id, user_id, header)
            
        raise StopPropagation
