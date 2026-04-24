import re
import os
import time
import asyncio
import requests
import yt_dlp
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, MessageNotModified
from database import users_db
import config
from datetime import datetime

EDIT_TIME = {}
SCHEDULER_STARTED = False

# 🌟 ఫుల్ స్పేస్ & బోల్డ్ బ్రాండింగ్ 🌟
def get_header(user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    if plan == "PREMIUM": return "<blockquote><b>💎 VELVETA PREMIUM USER 💎\n━━━━━━━━━━━━━━━━━━━━━</b></blockquote>\n\n"
    elif plan == "ADS_PREMIUM": return "<blockquote><b>📺 VELVETA SEMI PREMIUM 📺\n━━━━━━━━━━━━━━━━━━━━━</b></blockquote>\n\n"
    else: return ""

def extract_yt_id(text):
    match = re.search(r"(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})", text)
    return match.group(2) if match else None

def get_yt_metadata(yt_id):
    try:
        api_key = getattr(config.Config, "YOUTUBE_API_KEY", None)
        if not api_key:
            return "YouTube Video", None
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={yt_id}&key={api_key}"
        response = requests.get(url, timeout=5).json()
        if response.get("items"):
            snippet = response["items"][0]["snippet"]
            title = snippet.get("title", "YouTube Video")
            thumbnails = snippet.get("thumbnails", {})
            thumb_url = None
            for quality in ["maxres", "high", "medium", "default"]:
                if quality in thumbnails:
                    thumb_url = thumbnails[quality]["url"]
                    break
            return title, thumb_url
        return "YouTube Video", None
    except Exception:
        return "YouTube Video", None

def get_available_formats(url, proxy=None):
    opts = {
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt',
        'nocheckcertificate': True,
        'skip_download': True,
        'format': 'bestvideo+bestaudio/best'
    }
    if proxy and proxy.lower() != "none":
        opts['proxy'] = proxy

    available_heights = set()
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            for f in formats:
                h = f.get('height')
                if h and isinstance(h, int):
                    available_heights.add(h)
    except Exception:
        pass
    return available_heights

# 🌟 ఆటో రిపేర్ (ఫాల్‌బ్యాక్) ఫంక్షన్ తో మీడియా డౌన్‌లోడ్ 🌟
def download_media_only(url, quality, yt_id, proxy=None):
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    
    opts = {
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt',
        'nocheckcertificate': True,
        'legacyserverconnect': True,
        'writethumbnail': False
    }
    if proxy and proxy.lower() != "none":
        opts['proxy'] = proxy

    res_map = {"4k": "2160", "2k": "1440", "1080p": "1080", "720p": "720", "480p": "480", "360p": "360", "240p": "240", "144p": "144"}
    target_res = res_map.get(quality, "720")
    
    if quality == "audio":
        opts['format'] = 'bestaudio/best'
        opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
    else:
        opts['format'] = f'bestvideo[height<={target_res}]+bestaudio/bestvideo[width<={target_res}]+bestaudio/bestvideo+bestaudio/best'
        opts['merge_output_format'] = 'mp4'
    
    opts['outtmpl'] = f'downloads/{yt_id}_%(title)s.%(ext)s'
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            fname = ydl.prepare_filename(info)
            width = info.get('width') or 0
            height = info.get('height') or 0
            duration = info.get('duration') or 0
            if quality == "audio" and not fname.endswith('.mp3'):
                fname = fname.rsplit('.', 1)[0] + '.mp3'
            return fname, width, height, duration
    except Exception:
        opts['format'] = 'bestvideo+bestaudio/best'
        opts['merge_output_format'] = 'mp4'
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            fname = ydl.prepare_filename(info)
            width = info.get('width') or 0
            height = info.get('height') or 0
            duration = info.get('duration') or 0
            return fname, width, height, duration

async def safe_edit_text(msg, text, reply_markup=None):
    try:
        if reply_markup:
            await msg.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=reply_markup)
        else:
            await msg.edit_text(text, parse_mode=enums.ParseMode.HTML)
    except MessageNotModified:
        pass
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await safe_edit_text(msg, text, reply_markup)
    except Exception:
        pass

async def progress_bar(current, total, msg, title, header):
    global EDIT_TIME
    if total > 0:
        if time.time() - EDIT_TIME.get(msg.id, 0) > 8:
            percent = int((current / total) * 100)
            done = int(percent / 10)
            bar = "🟩" * done + "⬜" * (10 - done)
            cmb = round(current / (1024 * 1024), 2)
            tmb = round(total / (1024 * 1024), 2)
            text = f"{header}📤 <b>Uploading...</b>\n🎬 {title}\n\n{bar} {percent}%\n⚡ Speed: Max\n📦 Size: {cmb} MiB / {tmb} MiB"
            await safe_edit_text(msg, text)
            EDIT_TIME[msg.id] = time.time()

async def start_download_process(client, event, quality, url, title=None, existing_msg=None):
    user_id = event.from_user.id
    header = get_header(user_id)
    yt_id = extract_yt_id(url)
    user = users_db.find_one({"user_id": user_id}) or {}
    proxy = user.get("proxy")
    
    if hasattr(event, "data"):
        reply_to_id = event.message.reply_to_message_id if event.message.reply_to_message else event.message.id
    else:
        reply_to_id = event.id

    sent_msg = existing_msg if existing_msg else (event.message if hasattr(event, "data") else await event.reply_text(f"{header}📥 <b>Processing...</b>", parse_mode=enums.ParseMode.HTML, reply_to_message_id=reply_to_id))

    try:
        api_title, yt_thumb_url = get_yt_metadata(yt_id)
        video_title = api_title if api_title != "YouTube Video" else (title or "YouTube Video")

        custom_thumb = user.get("wallpaper_path")
        final_thumb = custom_thumb if custom_thumb and os.path.exists(custom_thumb) else None

        if not final_thumb and yt_thumb_url:
            yt_thumb_path = f"downloads/{yt_id}_thumb.jpg"
            if not os.path.exists("downloads"): os.makedirs("downloads")
            try:
                img_data = requests.get(yt_thumb_url).content
                with open(yt_thumb_path, 'wb') as handler:
                    handler.write(img_data)
                final_thumb = yt_thumb_path
            except Exception: pass

        file_path, v_width, v_height, v_duration = await asyncio.to_thread(download_media_only, url, quality, yt_id, proxy)

        await safe_edit_text(sent_msg, f"{header}📤 <b>Uploading to Telegram...</b>")

        share_url = f"https://t.me/share/url?url={url}"
        share_markup = InlineKeyboardMarkup([[InlineKeyboardButton("📤 Share Video With Friends 📤", url=share_url)]])

        if quality == "audio":
            await client.send_audio(
                chat_id=user_id, 
                audio=file_path, 
                caption=f"{header}🎬 <b>{video_title}</b>", 
                thumb=final_thumb, 
                duration=v_duration,
                reply_to_message_id=reply_to_id,
                reply_markup=share_markup,
                progress=progress_bar, 
                progress_args=(sent_msg, video_title, header)
            )
        else:
            await client.send_video(
                chat_id=user_id, 
                video=file_path, 
                caption=f"{header}🎬 <b>{video_title}</b>", 
                thumb=final_thumb, 
                width=v_width,
                height=v_height,     
                duration=v_duration,
                reply_to_message_id=reply_to_id,
                reply_markup=share_markup,
                progress=progress_bar, 
                progress_args=(sent_msg, video_title, header), 
                supports_streaming=True
            )
        
        await sent_msg.delete()
        
        if os.path.exists(file_path): os.remove(file_path)
        if final_thumb and final_thumb != custom_thumb and os.path.exists(final_thumb): os.remove(final_thumb)

    except Exception as e:
        error_msg = f"{header}❌ <b>Download Failed!</b>\n\n`{str(e)}`"
        await safe_edit_text(sent_msg, error_msg)

@Client.on_message(filters.command("reveal") & filters.private)
async def reveal_cmd(client, message):
    user_id = message.from_user.id
    user = users_db.find_one({"user_id": user_id}) or {}
    saved_url = user.get("saved_link")
    header = get_header(user_id)
    if not saved_url:
        await message.reply_text(f"{header}❌ No saved content found.", parse_mode=enums.ParseMode.HTML)
        return
    if saved_url.startswith("vid:"):
        await client.send_video(user_id, saved_url.split("vid:")[1])
    else:
        yt_id = extract_yt_id(saved_url)
        if yt_id: await show_quality_buttons(client, message, saved_url, yt_id, user_id, header)

async def show_quality_buttons(client, message, url, yt_id, user_id, header):
    proc_msg = await message.reply_text(f"{header}🔍 <b>Checking available qualities...</b>", parse_mode=enums.ParseMode.HTML, reply_to_message_id=message.id)
    
    title, _ = get_yt_metadata(yt_id)
    proxy = (users_db.find_one({"user_id": user_id}) or {}).get("proxy")
    
    available_h = await asyncio.to_thread(get_available_formats, url, proxy)
    
    # 🌟 అన్ని బటన్స్ క్రియేట్ చేయడం మరియు లేని వాటికి 🔒 పెట్టడం 🌟
    btn_1080 = InlineKeyboardButton("🖥 1080p", callback_data=f"dl|1080p|{yt_id}") if (any(h >= 1080 for h in available_h) or not available_h) else InlineKeyboardButton("🔒 1080p", callback_data="locked_quality")
    btn_720 = InlineKeyboardButton("💻 720p", callback_data=f"dl|720p|{yt_id}") if (any(h >= 720 for h in available_h) or not available_h) else InlineKeyboardButton("🔒 720p", callback_data="locked_quality")
    btn_480 = InlineKeyboardButton("📺 480p", callback_data=f"dl|480p|{yt_id}") if (any(h >= 480 for h in available_h) or not available_h) else InlineKeyboardButton("🔒 480p", callback_data="locked_quality")
    btn_360 = InlineKeyboardButton("📱 360p", callback_data=f"dl|360p|{yt_id}") if (any(h >= 360 for h in available_h) or not available_h) else InlineKeyboardButton("🔒 360p", callback_data="locked_quality")
    
    buttons = [
        [btn_1080, btn_720],
        [btn_480, btn_360],
        [InlineKeyboardButton("🎵 Audio", callback_data=f"dl|audio|{yt_id}")]
    ]

    text = f"{header}🎬 📹 <b>{title}</b>\n\n👇 <b>Select Quality:</b>"
    keyboard = InlineKeyboardMarkup(buttons)
    await safe_edit_text(proc_msg, text, reply_markup=keyboard)

# 🌟 లాక్ చేయబడిన క్వాలిటీ నొక్కినప్పుడు వచ్చే పాప్-అప్ (Alert) మెసేజ్ 🌟
@Client.on_callback_query(filters.regex(r"^locked_quality$"))
async def locked_quality_alert(client, callback_query):
    alert_text = "🚫 OOPS! Sorry!\n\nThe requested quality is NOT available for this specific YouTube link. 😔\n\n👉 Please select an unlocked quality from the menu! 🎥"
    await callback_query.answer(alert_text, show_alert=True)

@Client.on_callback_query(filters.regex(r"^dl\|(.*)\|(.*)$"))
async def quality_selection(client, callback_query):
    _, quality, yt_id = callback_query.data.split("|")
    await start_download_process(client, callback_query, quality, f"https://youtu.be/{yt_id}")

@Client.on_message(filters.text & filters.private & ~filters.command(["start", "help", "reveal", "setcookies", "setproxy"]))
async def text_handler(client, message):
    yt_id = extract_yt_id(message.text)
    if yt_id:
        await show_quality_buttons(client, message, message.text, yt_id, message.from_user.id, get_header(message.from_user.id))

@Client.on_message(filters.private, group=-1)
async def start_scheduler_once(client, message):
    global SCHEDULER_STARTED
    if not SCHEDULER_STARTED:
        SCHEDULER_STARTED = True
