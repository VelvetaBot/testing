import re
import os
import asyncio
import requests
import yt_dlp
from pyrogram import Client, filters, enums, StopPropagation
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import users_db
import config

# పాత ఇంజిన్ ఫైల్ నుండి అవసరమైన ఫంక్షన్స్ తీసుకుంటున్నాం (కోడ్ డూప్లికేట్ అవ్వకుండా)
from plugins.engine import get_header, download_media_with_fallback, progress_bar, safe_edit_text, get_yt_metadata

def extract_clean_id(text):
    # 🌟 ఆటో-రిపేర్ లాజిక్: స్పేస్‌లు మరియు చెత్త అక్షరాలను క్లీన్ చేసి ID ని లాగుతుంది 🌟
    cleaned_text = text.replace(" ", "") # ముందుగా స్పేస్‌లు అన్నీ తీసేస్తుంది
    match = re.search(r"(?:v=|youtu\.be/|shorts/|v/|embed/|post/|community/)([a-zA-Z0-9_-]{11})", cleaned_text)
    if not match:
        # URL మొత్తం దెబ్బతిన్నా, పక్కన ఎక్కడైనా 11 అక్షరాల ID ఉందేమో వెతుకుతుంది
        match = re.search(r"([a-zA-Z0-9_-]{11})", cleaned_text)
    return match.group(1) if match else None

def get_playlist_videos(playlist_id):
    api_key = getattr(config.Config, "YOUTUBE_API_KEY", None)
    if not api_key: return []
    
    videos = []
    url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId={playlist_id}&key={api_key}"
    
    try:
        while url and len(videos) < 50: # సర్వర్ క్రాష్ అవ్వకుండా లిమిట్ 50 పెట్టాను
            res = requests.get(url, timeout=5).json()
            for item in res.get("items", []):
                videos.append(item["snippet"]["resourceId"]["videoId"])
            next_token = res.get("nextPageToken")
            if next_token:
                url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId={playlist_id}&pageToken={next_token}&key={api_key}"
            else:
                break
    except Exception:
        pass
    return videos

def extract_post_images(url, proxy=None):
    opts = {
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt',
        'extract_flat': True,
        'skip_download': True
    }
    if proxy and proxy.lower() != "none": opts['proxy'] = proxy
    
    images = []
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'thumbnails' in info:
                # హై క్వాలిటీ ఫోటో లింక్ లాగడం
                images.append(info['thumbnails'][-1]['url'])
    except Exception:
        pass
    return images

# ==========================================
# MASTER HANDLER: PLAYLIST, POSTS & AUTO-REPAIR (Group -4)
# ==========================================
@Client.on_message(filters.text & filters.private, group=-4)
async def premium_master_handler(client, message):
    user_id = message.from_user.id
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    header = get_header(user_id)
    text = message.text

    # 1. 🌟 PLAYLIST HANDLER 🌟
    if "list=" in text:
        if plan != "PREMIUM":
            await message.reply_text(f"{header}🚫 <b>Premium Feature Only</b> 🚫\n\nPlaylist downloading is exclusively for Premium users. Please upgrade your plan to download full playlists!", parse_mode=enums.ParseMode.HTML)
            raise StopPropagation
        
        plist_match = re.search(r"list=([a-zA-Z0-9_-]+)", text)
        if not plist_match: return
        playlist_id = plist_match.group(1)
        
        proc_msg = await message.reply_text(f"{header}🔍 <b>Fetching Playlist...</b>\nPlease wait while I gather the videos.", parse_mode=enums.ParseMode.HTML)
        
        videos = await asyncio.to_thread(get_playlist_videos, playlist_id)
        if not videos:
            await safe_edit_text(proc_msg, f"{header}❌ <b>Failed to fetch playlist!</b> Make sure the playlist is public.")
            raise StopPropagation
            
        pref_quality = user.get("preferred_quality")
        
        if pref_quality:
            # డిఫాల్ట్ క్వాలిటీ ఉంటే డైరెక్ట్ గా లూప్ స్టార్ట్ అవుతుంది
            await safe_edit_text(proc_msg, f"{header}✅ <b>Playlist Found! ({len(videos)} videos)</b>\nStarting download with your default quality: <b>{pref_quality}</b>")
            asyncio.create_task(process_playlist_download(client, message, videos, pref_quality, proc_msg, user_id, header, user.get("proxy")))
        else:
            # క్వాలిటీ బటన్స్ చూపిస్తుంది
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🖥 1080p", callback_data=f"plist|1080p|{playlist_id}"), InlineKeyboardButton("💻 720p", callback_data=f"plist|720p|{playlist_id}")],
                [InlineKeyboardButton("📺 480p", callback_data=f"plist|480p|{playlist_id}"), InlineKeyboardButton("📱 360p", callback_data=f"plist|360p|{playlist_id}")],
                [InlineKeyboardButton("🎵 Audio", callback_data=f"plist|audio|{playlist_id}")]
            ])
            await safe_edit_text(proc_msg, f"{header}📁 <b>Playlist Found ({len(videos)} videos)</b>\n\n👇 <b>Select Quality to Download Entire Playlist:</b>", reply_markup=keyboard)
        raise StopPropagation

    # 2. 🌟 COMMUNITY POST / PHOTOS HANDLER 🌟
    elif "/post/" in text or "/community" in text or "channel/" in text:
        if plan != "PREMIUM":
            await message.reply_text(f"{header}🚫 <b>Premium Feature Only</b> 🚫\n\nExtracting photos from Community Posts is a Premium feature. Upgrade your plan to use it!", parse_mode=enums.ParseMode.HTML)
            raise StopPropagation
            
        proc_msg = await message.reply_text(f"{header}🔍 <b>Extracting Photos...</b>", parse_mode=enums.ParseMode.HTML)
        images = await asyncio.to_thread(extract_post_images, text, user.get("proxy"))
        
        if images:
            await proc_msg.delete()
            for img in images:
                await client.send_photo(chat_id=user_id, photo=img, caption=f"{header}📸 <b>Community Post Photo</b>")
        else:
            await safe_edit_text(proc_msg, f"{header}❌ <b>No photos found in this post.</b>")
        raise StopPropagation

    # 3. 🌟 AUTO-REPAIR LINK HANDLER 🌟
    elif "youtu" in text.lower():
        clean_id = extract_clean_id(text)
        
        # పాత ఇంజిన్ ఫైల్‌కి అర్థంకాని ఫార్మాట్ లో ఉంటే దీన్ని రిపేర్ చేస్తుంది
        standard_match = re.search(r"(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})", text)
        
        if clean_id and not standard_match:
            if plan != "PREMIUM":
                await message.reply_text(f"{header}🚫 <b>Invalid Link Format</b> 🚫\n\nYour link is broken. Auto-Repairing broken links is a Premium feature. Please send a correct link or upgrade your plan!", parse_mode=enums.ParseMode.HTML)
                raise StopPropagation
                
            clean_url = f"https://youtu.be/{clean_id}"
            repair_msg = await message.reply_text(f"{header}🔧 <b>Auto-Repair Activated!</b>\nFixed your broken link. Processing now...", parse_mode=enums.ParseMode.HTML)
            
            # రిపేర్ చేసిన లింక్‌ను పాత క్వాలిటీ బటన్స్ ఫంక్షన్‌కి పంపుతుంది
            from plugins.engine import show_quality_buttons
            await asyncio.sleep(1.5)
            await repair_msg.delete()
            await show_quality_buttons(client, message, clean_url, clean_id, user_id, header)
            raise StopPropagation

# ==========================================
# PLAYLIST CALLBACK & DOWNLOAD LOOP
# ==========================================
@Client.on_callback_query(filters.regex(r"^plist\|(.*)\|(.*)$"))
async def playlist_quality_selection(client, callback_query):
    _, quality, playlist_id = callback_query.data.split("|")
    user_id = callback_query.from_user.id
    header = get_header(user_id)
    user = users_db.find_one({"user_id": user_id}) or {}
    
    await safe_edit_text(callback_query.message, f"{header}🔍 <b>Fetching Playlist...</b>\nPlease wait.")
    videos = await asyncio.to_thread(get_playlist_videos, playlist_id)
    
    if not videos:
        await safe_edit_text(callback_query.message, f"{header}❌ <b>Failed to fetch playlist!</b>")
        return
        
    await safe_edit_text(callback_query.message, f"{header}✅ <b>Starting Playlist Download!</b> ({len(videos)} videos)")
    asyncio.create_task(process_playlist_download(client, callback_query.message, videos, quality, callback_query.message, user_id, header, user.get("proxy")))

async def process_playlist_download(client, message, videos, quality, status_msg, user_id, header, proxy):
    total = len(videos)
    custom_thumb = (users_db.find_one({"user_id": user_id}) or {}).get("wallpaper_path")
    
    for index, yt_id in enumerate(videos, 1):
        url = f"https://youtu.be/{yt_id}"
        await safe_edit_text(status_msg, f"{header}⏳ <b>Playlist Progress:</b> {index}/{total}\n📥 Processing Video ID: <code>{yt_id}</code>")
        
        try:
            api_title, yt_thumb_url = get_yt_metadata(yt_id)
            video_title = api_title if api_title != "YouTube Video" else f"Playlist Video {index}"

            final_thumb = custom_thumb if custom_thumb and os.path.exists(custom_thumb) else None
            if not final_thumb and yt_thumb_url:
                yt_thumb_path = f"downloads/{yt_id}_thumb.jpg"
                try:
                    img_data = requests.get(yt_thumb_url).content
                    with open(yt_thumb_path, 'wb') as handler:
                        handler.write(img_data)
                    final_thumb = yt_thumb_path
                except Exception: pass

            file_path, v_width, v_height, v_duration = await asyncio.to_thread(download_media_with_fallback, url, quality, yt_id, proxy)

            if quality == "audio":
                await client.send_audio(chat_id=user_id, audio=file_path, caption=f"{header}🎬 <b>{video_title}</b>", thumb=final_thumb, duration=v_duration)
            else:
                await client.send_video(chat_id=user_id, video=file_path, caption=f"{header}🎬 <b>{video_title}</b>", thumb=final_thumb, width=v_width, height=v_height, duration=v_duration, supports_streaming=True)
            
            if os.path.exists(file_path): os.remove(file_path)
            if final_thumb and final_thumb != custom_thumb and os.path.exists(final_thumb): os.remove(final_thumb)
            
            await asyncio.sleep(2) # టెలిగ్రామ్ స్పామ్ లిమిట్ తగలకుండా చిన్న గ్యాప్
            
        except Exception as e:
            await client.send_message(chat_id=user_id, text=f"{header}❌ <b>Skipped video {index}/{total}</b> due to error:\n`{str(e)}`")
            continue
            
    await safe_edit_text(status_msg, f"{header}🎉 <b>Playlist Download Complete!</b>\nSuccessfully processed {total} videos.")
