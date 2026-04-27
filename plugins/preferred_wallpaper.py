import os
import time
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import MessageNotModified
from database import users_db

# ఇంజిన్ నుండి డౌన్‌లోడ్ ఫంక్షన్స్ తీసుకుంటున్నాం
from plugins.engine import download_media_with_fallback, get_yt_metadata, progress_bar, get_header, extract_yt_id

# యూజర్ ఏ స్టెప్ లో ఉన్నాడో గుర్తుపెట్టుకోవడానికి కంట్రోల్ రూమ్
WALLPAPER_SESSIONS = {}

# 🌟 PREMIUM CHECKER 🌟
def is_premium(user_id):
    user = users_db.find_one({"user_id": user_id})
    return user and user.get("plan") == "PREMIUM"

def get_premium_alert(header):
    text = (
        f"{header}💎 **Premium Feature Exclusively!**\n\n"
        "This feature is exclusively available for **Velveta Premium** users only. 🚫\n"
        "Upgrade your plan to unlock Custom Wallpapers and Default Quality settings! 🌟"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Upgrade to Premium", callback_data="upgrade_cmd")]])
    return text, kb

async def safe_edit(msg, text, reply_markup=None):
    try:
        if reply_markup: await msg.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=reply_markup)
        else: await msg.edit_text(text, parse_mode=enums.ParseMode.HTML)
    except MessageNotModified: pass

# ==========================================
# 🌟 1. PREFERRED QUALITY COMMAND 🌟
# ==========================================
@Client.on_message(filters.command("set_preferred_quality") & filters.private)
async def set_pref_quality_cmd(client, message):
    user_id = message.from_user.id
    header = get_header(user_id)
    
    if not is_premium(user_id):
        alert_text, alert_kb = get_premium_alert(header)
        await message.reply_text(alert_text, reply_markup=alert_kb)
        return

    text = (
        f"{header}🎥 Please choose your preferred quality\n\n"
        "📌 Select one of the options below"
    )
    
    buttons = [
        [InlineKeyboardButton("🚀 4K (Ultra HD)", callback_data="setpq|4k"), InlineKeyboardButton("🌟 2K (Mini Ultra HD)", callback_data="setpq|2k")],
        [InlineKeyboardButton("🖥 1080p (Full HD)", callback_data="setpq|1080p"), InlineKeyboardButton("💻 720p (HD)", callback_data="setpq|720p")],
        [InlineKeyboardButton("📺 480p (Clear)", callback_data="setpq|480p"), InlineKeyboardButton("📱 360p (Best Mobile)", callback_data="setpq|360p")],
        [InlineKeyboardButton("📟 240p (Ok Ok)", callback_data="setpq|240p"), InlineKeyboardButton("📉 144p (Data Saver)", callback_data="setpq|144p")],
        [InlineKeyboardButton("🎵 Audio Only (MP3)", callback_data="setpq|audio")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_pref_q")]
    ]
    
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^setpq\|(.*)$"))
async def save_pref_quality(client, callback_query):
    quality = callback_query.data.split("|")[1]
    user_id = callback_query.from_user.id
    header = get_header(user_id)
    
    # పాతదాన్ని తీసేసి కొత్తది పెడుతుంది
    users_db.update_one({"user_id": user_id}, {"$set": {"pref_quality": quality}})
    
    text = (
        f"{header}✅ Your preferred quality has been set successfully\n\n"
        "⚠️ **Important Note:**\n"
        "If the selected quality is not available, the downloader will automatically switch to the nearest available quality\n\n"
        "🔄 If you use the command /set_preferred_quality again, your previous setting will be automatically removed and replaced with the new one."
    )
    await safe_edit(callback_query.message, text)

@Client.on_callback_query(filters.regex(r"^cancel_pref_q$"))
async def cancel_pref_q(client, callback_query):
    await callback_query.message.delete()


# ==========================================
# 🌟 2. CUSTOM WALLPAPER WIZARD COMMAND 🌟
# ==========================================
@Client.on_message(filters.command("wallpaper") & filters.private)
async def wallpaper_cmd(client, message):
    user_id = message.from_user.id
    header = get_header(user_id)
    
    if not is_premium(user_id):
        alert_text, alert_kb = get_premium_alert(header)
        await message.reply_text(alert_text, reply_markup=alert_kb)
        return

    # వాల్‌పేపర్ విజార్డ్ స్టార్ట్
    WALLPAPER_SESSIONS[user_id] = {'step': 'wait_media'}
    
    text = (
        f"{header}📩 Please send a YouTube link or video\n\n"
        "📌 This will help us create your wallpaper and send it to you"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_wp_wizard")]])
    await message.reply_text(text, reply_markup=kb)

@Client.on_callback_query(filters.regex(r"^cancel_wp_wizard$"))
async def cancel_wp_wizard(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id in WALLPAPER_SESSIONS:
        del WALLPAPER_SESSIONS[user_id]
    await callback_query.message.delete()

# 🌟 వాల్‌పేపర్ విజార్డ్ కంట్రోలర్ (రూట్ మ్యాప్) 🌟
@Client.on_message(filters.private & ~filters.command(["start", "help", "reveal", "setcookies", "setproxy", "schedule", "save", "delete", "wallpaper", "set_preferred_quality", "users", "notify", "problems", "set_FreeBot", "set_freebot"]), group=-3)
async def wallpaper_state_manager(client, message):
    user_id = message.from_user.id
    header = get_header(user_id)
    
    if user_id not in WALLPAPER_SESSIONS:
        return # మామూలు ఇంజిన్ కి వెళ్ళిపోతుంది
        
    session = WALLPAPER_SESSIONS[user_id]
    step = session.get('step')
    
    # ---------------- STEP 1: MEDIA ----------------
    if step == 'wait_media':
        yt_id = extract_yt_id(message.text if message.text else "")
        
        # లింక్ ఇస్తే.. క్వాలిటీ అడుగుతుంది
        if yt_id:
            session['type'] = 'link'
            session['data'] = message.text
            session['yt_id'] = yt_id
            session['step'] = 'wait_quality'
            
            text = f"{header}🎥 Please choose your preferred quality for this custom download:"
            buttons = [
                [InlineKeyboardButton("🚀 4K (Ultra HD)", callback_data="wpq|4k"), InlineKeyboardButton("🌟 2K (Mini Ultra HD)", callback_data="wpq|2k")],
                [InlineKeyboardButton("🖥 1080p (Full HD)", callback_data="wpq|1080p"), InlineKeyboardButton("💻 720p (HD)", callback_data="wpq|720p")],
                [InlineKeyboardButton("📺 480p (Clear)", callback_data="wpq|480p"), InlineKeyboardButton("📱 360p (Best Mobile)", callback_data="wpq|360p")],
                [InlineKeyboardButton("📟 240p (Ok Ok)", callback_data="wpq|240p"), InlineKeyboardButton("📉 144p (Data Saver)", callback_data="wpq|144p")],
                [InlineKeyboardButton("🎵 Audio Only (MP3)", callback_data="wpq|audio")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_wp_wizard")]
            ]
            await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
            message.stop_propagation()
            
        # వీడియో ఇస్తే.. డైరెక్ట్ గా ఫోటో అడుగుతుంది
        elif message.video or message.document:
            session['type'] = 'video'
            session['data'] = message.message_id
            session['step'] = 'wait_photo'
            
            text = f"{header}🖼️ Please send the wallpaper you want to set\n\n📌 Supported format: .jpg"
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_wp_wizard")]])
            await message.reply_text(text, reply_markup=kb)
            message.stop_propagation()
            
        else:
            await message.reply_text(f"{header}❌ Invalid input. Please send a valid YouTube link or a Video.")
            message.stop_propagation()

    # ---------------- STEP 3: PHOTO & PROCESSING ----------------
    elif step == 'wait_photo':
        if message.photo or (message.document and message.document.mime_type.startswith('image/')):
            
            # విజార్డ్ క్లోజ్
            del WALLPAPER_SESSIONS[user_id]
            
            # ప్రాసెసింగ్ మెసేజ్
            proc_msg = await message.reply_text(
                f"{header}📥 Your photo has been received\n\n"
                "⏳ Please wait a moment while we process your request"
            )
            
            try:
                # 1. డౌన్‌లోడ్ కస్టమ్ ఫోటో
                if not os.path.exists("downloads"): os.makedirs("downloads")
                photo_path = await message.download(file_name=f"downloads/custom_{user_id}_{int(time.time())}.jpg")
                
                # 2. యూట్యూబ్ లింక్ అయితే ఇంజిన్ ద్వారా డౌన్‌లోడ్
                if session['type'] == 'link':
                    url = session['data']
                    quality = session['quality']
                    yt_id = session['yt_id']
                    
                    title, _ = get_yt_metadata(yt_id)
                    video_title = title if title != "YouTube Video" else f"Downloaded Video"
                    
                    user = users_db.find_one({"user_id": user_id}) or {}
                    proxy = user.get("proxy")
                    
                    file_path, v_width, v_height, v_duration = await asyncio.to_thread(download_media_with_fallback, url, quality, yt_id, proxy)
                    
                    start_time = time.time()
                    if quality == "audio":
                        await client.send_audio(
                            chat_id=user_id, audio=file_path, thumb=photo_path, duration=v_duration,
                            caption=f"{header}🎬 <b>{video_title}</b>\n\n🙏 Thank you for using @VelvetaYTDownloaderBot",
                            progress=progress_bar, progress_args=(proc_msg, video_title, header, start_time)
                        )
                    else:
                        await client.send_video(
                            chat_id=user_id, video=file_path, thumb=photo_path, width=v_width, height=v_height, duration=v_duration,
                            caption=f"{header}🎬 <b>{video_title}</b>\n\n🙏 Thank you for using @VelvetaYTDownloaderBot",
                            supports_streaming=True, progress=progress_bar, progress_args=(proc_msg, video_title, header, start_time)
                        )
                        
                    if os.path.exists(file_path): os.remove(file_path)

                # 3. టెలిగ్రామ్ వీడియో అయితే
                elif session['type'] == 'video':
                    video_msg = await client.get_messages(user_id, session['data'])
                    video_title = "Custom Wallpaper Video"
                    
                    # డౌన్‌లోడ్ వీడియో
                    await safe_edit(proc_msg, f"{header}📥 Downloading your video...")
                    file_path = await video_msg.download()
                    
                    # అప్‌లోడ్ విత్ కస్టమ్ ఫోటో
                    start_time = time.time()
                    await client.send_video(
                        chat_id=user_id, video=file_path, thumb=photo_path,
                        caption=f"{header}🎬 <b>{video_title}</b>\n\n🙏 Thank you for using @VelvetaYTDownloaderBot",
                        supports_streaming=True, progress=progress_bar, progress_args=(proc_msg, video_title, header, start_time)
                    )
                    
                    if os.path.exists(file_path): os.remove(file_path)

                # ప్రాసెసింగ్ మెసేజ్ డిలీట్ (మీరు అడిగినట్లు)
                await proc_msg.delete()
                if os.path.exists(photo_path): os.remove(photo_path)
                
            except Exception as e:
                await safe_edit(proc_msg, f"{header}❌ **Error processing custom request:**\n`{str(e)}`")
            
            message.stop_propagation()
        else:
            await message.reply_text(f"{header}❌ Please send a valid Image (.jpg) file.")
            message.stop_propagation()

# 🌟 వాల్‌పేపర్ విజార్డ్ లో క్వాలిటీ సెలెక్ట్ చేస్తే 🌟
@Client.on_callback_query(filters.regex(r"^wpq\|(.*)$"))
async def handle_wp_quality(client, callback_query):
    quality = callback_query.data.split("|")[1]
    user_id = callback_query.from_user.id
    header = get_header(user_id)
    
    if user_id in WALLPAPER_SESSIONS and WALLPAPER_SESSIONS[user_id].get('step') == 'wait_quality':
        WALLPAPER_SESSIONS[user_id]['quality'] = quality
        WALLPAPER_SESSIONS[user_id]['step'] = 'wait_photo'
        
        text = f"{header}🖼️ Please send the wallpaper you want to set\n\n📌 Supported format: .jpg"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_wp_wizard")]])
        await safe_edit(callback_query.message, text, reply_markup=kb)
    else:
        await callback_query.message.delete()
