import os
import re
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.exceptions import StopPropagation
from database import users_db

def get_header(user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    if plan == "PREMIUM": return "<blockquote><b>💎 Velveta Premium User                                                                                                                                                                                                        </b>                                                                                                                    </blockquote>"
    elif plan == "ADS_PREMIUM": return "<blockquote><b> 📺 Velveta Semi Premium User                                                                                                                                                                                                                                                                             </b>                                                                                                                                                   </blockquote>"
    else: return ""

def extract_yt_id(text):
    match = re.search(r"(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})", text)
    return match.group(2) if match else None

# Set Preferred Quality Command
@Client.on_message(filters.command("set_pref_quality") & filters.private)
async def set_pref_quality(client, message):
    user_id = message.from_user.id
    header = get_header(user_id)
    text = f"{header}⚙️ <b>Set Preferred Quality</b>\n\nChoose your default quality for fast downloads:"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("1080p", callback_data="pref|1080p"), InlineKeyboardButton("720p", callback_data="pref|720p")],
        [InlineKeyboardButton("480p", callback_data="pref|480p"), InlineKeyboardButton("360p", callback_data="pref|360p")],
        [InlineKeyboardButton("Audio", callback_data="pref|audio"), InlineKeyboardButton("None", callback_data="pref|none")]
    ])
    await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^pref\|(.*)$"))
async def save_pref_quality(client, callback_query):
    qual = callback_query.data.split("|")[1]
    user_id = callback_query.from_user.id
    header = get_header(user_id)
    if qual == "none":
        users_db.update_one({"user_id": user_id}, {"$unset": {"pref_quality": ""}})
        await callback_query.message.edit_text(f"{header}✅ Preferred quality removed! I will ask you every time.")
    else:
        users_db.update_one({"user_id": user_id}, {"$set": {"pref_quality": qual}})
        await callback_query.message.edit_text(f"{header}✅ Preferred quality set to <b>{qual}</b>!")

# Wallpaper Command
@Client.on_message(filters.command("wallpaper") & filters.private)
async def wallpaper_cmd(client, message):
    user_id = message.from_user.id
    header = get_header(user_id)
    
    user = users_db.find_one({"user_id": user_id}) or {}
    if user.get("plan", "FREE") == "FREE":
        await message.reply_text(f"{header}⚠️ <b>Premium Feature!</b>\n\nCustom Wallpapers are only available for Premium/Ads users.\n👉 Send /upgrade to unlock!", parse_mode=enums.ParseMode.HTML)
        return

    users_db.update_one({"user_id": user_id}, {"$set": {"state": "waiting_for_wallpaper"}})
    
    text = (
        f"{header}🖼 <b>Custom Wallpaper Setup</b>\n\n"
        "Please send me a <b>Photo</b> directly, or send a <b>YouTube Link</b> to extract its thumbnail as your wallpaper.\n\n"
        "<i>To cancel, send /cancel</i>"
    )
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)

# Wallpaper State Manager
@Client.on_message(filters.private & ~filters.command(["cancel", "start", "help"]), group=-3)
async def wallpaper_state_manager(client, message):
    user_id = message.from_user.id
    user = users_db.find_one({"user_id": user_id}) or {}
    
    if user.get("state") == "waiting_for_wallpaper":
        header = get_header(user_id)
        
        if message.photo:
            file_path = await message.download(file_name=f"downloads/{user_id}_wallpaper.jpg")
            users_db.update_one({"user_id": user_id}, {"$set": {"wallpaper_path": file_path, "state": None}})
            await message.reply_text(f"{header}✅ <b>Wallpaper Saved!</b>\nThis image will be used for your future downloads.", parse_mode=enums.ParseMode.HTML)
            raise StopPropagation
            
        elif message.text:
            text = message.text
            yt_id = extract_yt_id(text)
            
            if yt_id:
                from plugins.engine import get_yt_metadata
                import requests
                _, thumb_url = get_yt_metadata(yt_id)
                if thumb_url:
                    path = f"downloads/{user_id}_wallpaper.jpg"
                    if not os.path.exists("downloads"): os.makedirs("downloads")
                    try:
                        img_data = requests.get(thumb_url).content
                        with open(path, 'wb') as handler:
                            handler.write(img_data)
                        users_db.update_one({"user_id": user_id}, {"$set": {"wallpaper_path": path, "state": None}})
                        await message.reply_text(f"{header}✅ <b>Wallpaper Extracted & Saved!</b>\nThis YouTube thumbnail will be used for your downloads.", parse_mode=enums.ParseMode.HTML)
                        raise StopPropagation
                    except Exception as e:
                        await message.reply_text(f"{header}❌ Failed to download thumbnail: {e}")
                else:
                    await message.reply_text(f"{header}❌ Could not find a thumbnail for this video. Please send a photo instead.")
            else:
                await message.reply_text(f"{header}❌ Invalid input! Send a photo or a valid YouTube link.")
            raise StopPropagation

@Client.on_message(filters.command("cancel") & filters.private)
async def cancel_cmd(client, message):
    user_id = message.from_user.id
    header = get_header(user_id)
    users_db.update_one({"user_id": user_id}, {"$set": {"state": None}})
    await message.reply_text(f"{header}🚫 Action cancelled.", parse_mode=enums.ParseMode.HTML)
