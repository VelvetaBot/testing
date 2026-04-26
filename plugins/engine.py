import re
import os
import time
import asyncio
import requests
import yt_dlp
import youtube_dl 
from pytubefix import YouTube as PyTubeFixDL 
from pytube import YouTube as PyTubeDL 
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, MessageNotModified
from database import users_db
import config
from datetime import datetime

from plugins.cookie_manager import get_working_cookie_file

EDIT_TIME = {}
SCHEDULER_STARTED = False

def get_header(user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    if plan == "PREMIUM": return "<blockquote><b>💎 Velveta Premium User                                                                                                                                                                                                        </b></blockquote>\n\n"
    elif plan == "ADS_PREMIUM": return "<blockquote><b> 📺 Velveta Semi Premium User                                                                                                                                                                                                                                                                             </b></blockquote>\n\n"
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
            for res in ["maxres", "standard", "high", "medium", "default"]:
                if res in thumbnails:
                    thumb_url = thumbnails[res]["url"]
                    break
            return title, thumb_url
        return "YouTube Video", None
    except Exception:
        return "YouTube Video", None

# 🌟 YT-DLP క్రాష్ అవ్వకుండా ఆపడానికి కస్టమ్ లాగర్ 🌟
class MyLogger(object):
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg):
        raise Exception(msg)

def get_available_formats(url, proxy=None):
    opts = {
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt',
        'nocheckcertificate': True,
        'skip_download': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'tv', 'web']}},
        'logger': MyLogger() 
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

# ==========================================
# 🌟 4-LAYER MULTI-PACKAGE DOWNLOADER 🌟
# ==========================================
def download_media_with_fallback(url, quality, yt_id, proxy=None):
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    
    res_map = {"4k": 2160, "2k": 1440, "1080p": 1080, "720p": 720, "480p": 480, "360p": 360, "240p": 240, "144p": 144}
    target_res = res_map.get(quality, 720)
    
    # --- ATTEMPT 1: YT-DLP ---
    opts = {
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt',
        'nocheckcertificate': True,
        'outtmpl': f'downloads/{yt_id}_%(title)s.%(ext)s',
        'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'tv', 'web']}}, 
        'logger': MyLogger() 
    }
    if proxy and proxy.lower() != "none":
        opts['proxy'] = proxy

    if quality == "audio":
        opts['format'] = 'bestaudio/best'
        opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
    else:
        opts['format'] = f'bestvideo[height<={target_res}]+bestaudio/bestvideo[width<={target_res}]+bestaudio/best'
        opts['merge_output_format'] = 'mp4'
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            fname = ydl.prepare_filename(info)
            if quality == "audio" and not fname.endswith('.mp3'):
                fname = fname.rsplit('.', 1)[0] + '.mp3'
            return fname, info.get('width', 0), info.get('height', 0), info.get('duration', 0)
    except Exception as e1:
        print(f"YT-DLP Failed: {e1}")
        
        # --- ATTEMPT 2: PyTubeFix (Removed use_po_token to stop console prompts) ---
        try:
            yt = PyTubeFixDL(url) # 🌟 ఇక్కడ ఆ జామ్ చేసే ట్రిక్ ని తీసేశాను 🌟
            if quality == "audio":
                stream = yt.streams.get_audio_only()
                fname = stream.download(output_path="downloads", filename=f"{yt_id}_audio_pf.mp3")
                return fname, 0, 0, yt.length
            else:
                stream = yt.streams.filter(res=f"{target_res}p", file_extension='mp4').first()
                if not stream: stream = yt.streams.get_highest_resolution()
                fname = stream.download(output_path="downloads", filename=f"{yt_id}_video_pf.mp4")
                return fname, 1280, 720, yt.length
        except Exception as e2:
            print(f"PyTubeFix Failed: {e2}")
            
            # --- ATTEMPT 3: PyTube ---
            try:
                yt = PyTubeDL(url)
                if quality == "audio":
                    stream = yt.streams.get_audio_only()
                    fname = stream.download(output_path="downloads", filename=f"{yt_id}_audio_pt.mp3")
                    return fname, 0, 0, yt.length
                else:
                    stream = yt.streams.filter(res=f"{target_res}p", file_extension='mp4').first()
                    if not stream: stream = yt.streams.get_highest_resolution()
                    fname = stream.download(output_path="downloads", filename=f"{yt_id}_video_pt.mp4")
                    return fname, 1280, 720, yt.length
            except Exception as e3:
                print(f"PyTube Failed: {e3}")
                
                # --- ATTEMPT 4: Youtube-dl ---
                try:
                    ydl_opts = {
                        'quiet': True, 'no_warnings': True, 'nocheckcertificate': True,
                        'outtmpl': f'downloads/{yt_id}_ydl_%(title)s.%(ext)s',
                        'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'tv', 'web']}},
                        'logger': MyLogger()
                    }
                    if proxy and proxy.lower() != "none": ydl_opts['proxy'] = proxy
                    
                    if quality == "audio":
                        ydl_opts['format'] = 'bestaudio/best'
                        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
                    else:
                        ydl_opts['format'] = f'bestvideo[height<={target_res}]+bestaudio/best'
                        ydl_opts['merge_output_format'] = 'mp4'

                    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        fname = ydl.prepare_filename(info)
                        if quality == "audio" and not fname.endswith('.mp3'):
                            fname = fname.rsplit('.', 1)[0] + '.mp3'
                        return fname, info.get('width', 0), info.get('height', 0), info.get('duration', 0)
                except Exception as e4:
                    raise Exception(f"Ultimate Failure! All 4 Packages crashed. 1:{e1} | 2:{e2} | 3:{e3} | 4:{e4}")

def format_bytes(size):
    if not size: return "0.00"
    return f"{round(size / (1024 * 1024), 2)}"

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

async def progress_bar(current, total, msg, title, header, start_time):
    global EDIT_TIME
    if total > 0:
        if time.time() - EDIT_TIME.get(msg.id, 0) > 5:
            percent = int((current / total) * 100)
            done = int(percent / 10)
            bar = "🟩" * done + "⬜" * (10 - done)
            
            elapsed_time = time.time() - start_time
            speed = current / elapsed_time if elapsed_time > 0 else 0
            speed_mbps = round(speed / (1024 * 1024), 2)
            
            eta_seconds = int((total - current) / speed) if speed > 0 else 0
            eta_str = time.strftime('%H:%M:%S', time.gmtime(eta_seconds))
            
            cmb = format_bytes(current)
            tmb = format_bytes(total)
            
            text = (
                f"{header}📤 <b>Uploading...</b>\n"
                f"🎬 {title}\n\n"
                f"{bar} {percent}%\n"
                f"⚡ Speed: {speed_mbps} MB/s\n"
                f"📦 Size: {cmb} MiB / {tmb} MiB\n"
                f"⏳ ETA: {eta_str}"
            )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"), InlineKeyboardButton("🔙 Back", callback_data="cancel_action")]
            ])
            await safe_edit_text(msg, text, reply_markup=keyboard)
            EDIT_TIME[msg.id] = time.time()

# ==========================================
# 🌟 QUALITY BUTTONS GENERATOR 🌟
# ==========================================
async def show_quality_buttons(client, message, url, yt_id, user_id, header, edit_msg=None):
    proc_msg = edit_msg if edit_msg else await message.reply_text(f"{header}🔍 <b>Checking available qualities...</b>", parse_mode=enums.ParseMode.HTML, reply_to_message_id=message.id)
    
    title, _ = get_yt_metadata(yt_id)
    proxy = (users_db.find_one({"user_id": user_id}) or {}).get("proxy")
    
    get_working_cookie_file(0) 
    
    available_h = await asyncio.to_thread(get_available_formats, url, proxy)
    
    btn_4k = InlineKeyboardButton("🚀 4K (Ultra HD)", callback_data=f"dl|4k|{yt_id}") if any(h >= 2160 for h in available_h) else InlineKeyboardButton("🔒 4K (Ultra HD)", callback_data="locked_quality")
    btn_2k = InlineKeyboardButton("🌟 2K (Mini Ultra HD)", callback_data=f"dl|2k|{yt_id}") if any(h >= 1440 for h in available_h) else InlineKeyboardButton("🔒 2K (Mini HD)", callback_data="locked_quality")
    btn_1080 = InlineKeyboardButton("🖥 1080p (Full HD)", callback_data=f"dl|1080p|{yt_id}") if any(h >= 1080 for h in available_h) else InlineKeyboardButton("🔒 1080p (Full HD)", callback_data="locked_quality")
    btn_720 = InlineKeyboardButton("💻 720p (HD)", callback_data=f"dl|720p|{yt_id}") if any(h >= 720 for h in available_h) else InlineKeyboardButton("🔒 720p (HD)", callback_data="locked_quality")
    btn_480 = InlineKeyboardButton("📺 480p (Clear)", callback_data=f"dl|480p|{yt_id}") if any(h >= 480 for h in available_h) else InlineKeyboardButton("🔒 480p (Clear)", callback_data="locked_quality")
    btn_360 = InlineKeyboardButton("📱 360p (Best Mobile)", callback_data=f"dl|360p|{yt_id}") if any(h >= 360 for h in available_h) else InlineKeyboardButton("🔒 360p (Best Mobile)", callback_data="locked_quality")
    btn_240 = InlineKeyboardButton("📟 240p (Ok Ok)", callback_data=f"dl|240p|{yt_id}") if any(h >= 240 for h in available_h) else InlineKeyboardButton("🔒 240p (Ok Ok)", callback_data="locked_quality")
    btn_144 = InlineKeyboardButton("📉 144p (Data Saver)", callback_data=f"dl|144p|{yt_id}") if any(h >= 144 for h in available_h) else InlineKeyboardButton("🔒 144p (Data Saver)", callback_data="locked_quality")
    
    buttons = [
        [btn_4k, btn_2k],
        [btn_1080, btn_720],
        [btn_480, btn_360],
        [btn_240, btn_144],
        [InlineKeyboardButton("🎵 Audio Only (MP3)", callback_data=f"start_dl|audio|{yt_id}")]
    ]

    text = f"{header}🎬 📹 <b>{title}</b>\n\n👇 <b>Select Quality:</b>"
    keyboard = InlineKeyboardMarkup(buttons)
    await safe_edit_text(proc_msg, text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"^locked_quality$"))
async def locked_quality_alert(client, callback_query):
    alert_text = "🚫 OOPS! Sorry!\n\nThe requested quality is NOT available for this specific YouTube link. 😔\n\n👉 Please select an unlocked quality from the menu! 🎥"
    await callback_query.answer(alert_text, show_alert=True)

@Client.on_callback_query(filters.regex(r"^dl\|(.*)\|(.*)$"))
async def handle_quality_click(client, callback_query):
    _, quality, yt_id = callback_query.data.split("|")
    user_id = callback_query.from_user.id
    header = get_header(user_id)
    
    if quality == "144p":
        text = (
            f"{header}⚠️ <b>Confirmation Required!</b>\n\n"
            "👀 Note: 144p quality is very low and might be blurry 😵‍💫.\n"
            "This is only recommended for saving data 📉.\n\n"
            "🤔 Do you want to proceed?"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("☑️ Yes, Sure", callback_data=f"start_dl|144p|{yt_id}")],
            [InlineKeyboardButton("🔙 Back", callback_data=f"back_to_q|{yt_id}")]
        ])
        await safe_edit_text(callback_query.message, text, reply_markup=keyboard)
    else:
        await start_download_process(client, callback_query, quality, f"https://youtu.be/{yt_id}")

@Client.on_callback_query(filters.regex(r"^back_to_q\|(.*)$"))
async def back_to_qualities(client, callback_query):
    yt_id = callback_query.data.split("|")[1]
    user_id = callback_query.from_user.id
    header = get_header(user_id)
    await show_quality_buttons(client, callback_query.message, f"https://youtu.be/{yt_id}", yt_id, user_id, header, edit_msg=callback_query.message)

# ==========================================
# 🌟 MAIN DOWNLOAD & TELEGRAM UPLOAD PROCESS 🌟
# ==========================================
@Client.on_callback_query(filters.regex(r"^start_dl\|(.*)\|(.*)$"))
async def process_start_dl(client, callback_query):
    _, quality, yt_id = callback_query.data.split("|")
    await start_download_process(client, callback_query, quality, f"https://youtu.be/{yt_id}")

async def start_download_process(client, event, quality, url):
    user_id = event.from_user.id
    header = get_header(user_id)
    yt_id = extract_yt_id(url)
    user = users_db.find_one({"user_id": user_id}) or {}
    proxy = user.get("proxy")
    
    reply_to_id = event.message.reply_to_message_id if event.message.reply_to_message else event.message.id
    sent_msg = event.message

    try:
        title, yt_thumb_url = get_yt_metadata(yt_id)
        video_title = title if title != "YouTube Video" else f"Downloaded Video"

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
            except Exception:
                pass

        await safe_edit_text(sent_msg, f"{header}📥 <b>Processing & Downloading...</b>\n🎬 {video_title}")

        file_path = None
        download_success = False
        last_error = ""

        for attempt in range(5):
            cookie_file = get_working_cookie_file(attempt) 
            try:
                file_path, v_width, v_height, v_duration = await asyncio.to_thread(download_media_with_fallback, url, quality, yt_id, proxy)
                download_success = True
                break
            except Exception as e:
                last_error = str(e)
                print(f"Cookie/Package Loop Attempt {attempt+1} Failed: {e}")
                continue

        if not download_success:
            from plugins.admin import log_bot_problem
            from plugins.fallback import run_ultimate_fallback
            
            log_bot_problem(f"Download Failed (All methods exhausted). Final Error: {last_error}", "engine.py")
            await safe_edit_text(sent_msg, f"{header}⚠️ <b>All Internal Methods Failed!</b>\nTriggering Ultimate Fallback Protocol...")
            await run_ultimate_fallback(client, event.message, url, quality, yt_id, sent_msg)
            return

        start_time = time.time()
        extract_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Extract Audio MP3", callback_data=f"start_dl|audio|{yt_id}")]])

        if quality == "audio":
            await client.send_audio(
                chat_id=user_id, 
                audio=file_path, 
                caption=f"{header}🎬 <b>{video_title}</b>\n\n🙏 Thank you for using @VelvetaYTDownloaderBot", 
                duration=v_duration,
                thumb=final_thumb, 
                reply_to_message_id=reply_to_id,
                progress=progress_bar, 
                progress_args=(sent_msg, video_title, header, start_time)
            )
        else:
            await client.send_video(
                chat_id=user_id, 
                video=file_path, 
                caption=f"{header}🎬 <b>{video_title}</b>\n\n🙏 Thank you for using @VelvetaYTDownloaderBot", 
                width=v_width, height=v_height, duration=v_duration,
                thumb=final_thumb, 
                reply_to_message_id=reply_to_id,
                reply_markup=extract_kb, 
                progress=progress_bar, 
                progress_args=(sent_msg, video_title, header, start_time), 
                supports_streaming=True
            )
        
        await sent_msg.delete()
        if os.path.exists(file_path): os.remove(file_path)
        if final_thumb and final_thumb != custom_thumb and os.path.exists(final_thumb):
            os.remove(final_thumb)

    except Exception as e:
        from plugins.admin import log_bot_problem
        log_bot_problem(str(e), "engine.py - Upload Stage")
        await safe_edit_text(sent_msg, f"{header}❌ <b>Download Failed!</b>\n\n`{str(e)}`")

@Client.on_message(filters.text & filters.private & ~filters.command(["start", "help", "reveal", "setcookies", "setproxy", "schedule", "save", "delete", "wallpaper", "set_pref_quality", "users", "notify", "problems", "set_FreeBot", "set_freebot"]))
async def text_handler(client, message):
    yt_id = extract_yt_id(message.text)
    if yt_id:
        await show_quality_buttons(client, message, message.text, yt_id, message.from_user.id, get_header(message.from_user.id))
