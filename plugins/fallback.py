import os
import asyncio
import time
import requests
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import MessageNotModified
import config
from database import users_db
from plugins.engine import get_yt_metadata, get_header, progress_bar, safe_edit_text

# ==========================================
# 🌟 USERBOT INITIALIZATION (The Secret Weapon) 🌟
# టెలిగ్రామ్ బాట్స్ వేరే బాట్స్ తో మాట్లాడలేవు కాబట్టి, ఈ Userbot ఒక మనిషిలాగా వెళ్లి ఆ 5 బాట్స్ నుండి వీడియో లాగుతుంది.
# ==========================================
userbot = Client(
    "VelvetaUserbot",
    api_id=config.Config.API_ID,
    api_hash=config.Config.API_HASH,
    session_string=config.Config.STRING_SESSION
)

# బాట్ స్టార్ట్ అయినప్పుడు యూజర్‌బాట్ కూడా బ్యాక్‌గ్రౌండ్ లో స్టార్ట్ అవ్వాలి
async def start_userbot():
    if not userbot.is_connected:
        await userbot.start()

# ప్రయారిటీ ప్రకారం బాట్స్ లిస్ట్
PRIORITY_1_BOTS = ["Gozillabot_Downloaderbot_Bot", "Bot_Gozillabot", "ttrubot"] # ఇవి క్వాలిటీ బటన్స్ ఇస్తాయి
PRIORITY_2_BOTS = ["YTfinderbot", "FullDowerBot"] # ఇవి డైరెక్ట్ గా లేదా Video/Audio బటన్స్ తో ఇస్తాయి

async def wait_for_bot_response(bot_username, start_time, timeout=45):
    """బాట్ కి మెసేజ్ పంపిన తర్వాత అది రిప్లై ఇచ్చే వరకు వెయిట్ చేసే లాజిక్"""
    for _ in range(int(timeout / 2)):
        await asyncio.sleep(2)
        async for msg in userbot.get_chat_history(bot_username, limit=1):
            if msg.date > start_time and msg.from_user and msg.from_user.username == bot_username:
                return msg
    return None

async def interact_with_fallback_bot(bot_username, url, quality, attempt_msg, header):
    """ఒక్కో బాట్ తో మనిషిలాగా ఇంటరాక్ట్ అయ్యే డీప్ లాజిక్"""
    try:
        await safe_edit_text(attempt_msg, f"{header}🔄 <b>Fallback Triggered:</b> Requesting <code>@{bot_username}</code>...")
        
        # 1. బాట్ కి లింక్ పంపడం
        start_time = datetime.now()
        await userbot.send_message(bot_username, url)
        
        # 2. బాట్ రిప్లై కోసం వెయిటింగ్
        response = await wait_for_bot_response(bot_username, start_time)
        if not response:
            return None # బాట్ పడుకుంది లేదా పని చేయట్లేదు

        # 3. క్వాలిటీ బటన్స్ (Inline Keyboard) ఉంటే దాన్ని నొక్కడం
        if response.reply_markup and response.reply_markup.inline_keyboard:
            target_btn = None
            # యూజర్ అడిగిన క్వాలిటీ కోసం వెతుకుతుంది
            for row in response.reply_markup.inline_keyboard:
                for btn in row:
                    if quality.lower() in btn.text.lower() or (quality == "audio" and "audio" in btn.text.lower()):
                        target_btn = btn
                        break
                if target_btn: break
            
            # ఒకవేళ కచ్చితమైన క్వాలిటీ లేకపోతే, 'Video' లేదా ఫస్ట్ ఉన్న బటన్ నొక్కుతుంది
            if not target_btn:
                for row in response.reply_markup.inline_keyboard:
                    for btn in row:
                        if "video" in btn.text.lower() or "mp4" in btn.text.lower():
                            target_btn = btn
                            break
                    if target_btn: break

            if target_btn:
                await safe_edit_text(attempt_msg, f"{header}🔄 <b>Selecting Quality...</b> on <code>@{bot_username}</code>")
                # Userbot బటన్ నొక్కుతుంది
                await userbot.request_callback_answer(chat_id=response.chat.id, message_id=response.id, callback_data=target_btn.callback_data)
                
                # బటన్ నొక్కాక అసలైన వీడియో ఫైల్ కోసం మళ్లీ వెయిటింగ్
                start_time_media = datetime.now()
                video_response = await wait_for_bot_response(bot_username, start_time_media, timeout=60)
                if video_response and (video_response.video or video_response.audio or video_response.document):
                    return video_response
            
        # డైరెక్ట్ గా వీడియో పంపించేస్తే (ఉదా: FullDowerBot)
        elif response.video or response.audio or response.document:
            return response
            
        return None
    except Exception as e:
        print(f"Error interacting with {bot_username}: {e}")
        return None

async def download_and_clean_media(media_message, yt_id, user_id, status_msg, header, quality):
    """ఎక్స్టర్నల్ బాట్ పంపిన వీడియోని మన సర్వర్ లోకి డౌన్‌లోడ్ చేసి క్లీన్ చేసే లాజిక్"""
    await safe_edit_text(status_msg, f"{header}📥 <b>Receiving File from External Server...</b>\nPlease wait.")
    
    if not os.path.exists("downloads"): os.makedirs("downloads")
    ext = ".mp3" if quality == "audio" else ".mp4"
    file_path = os.path.join("downloads", f"fallback_{yt_id}_{user_id}{ext}")
    
    # Userbot ద్వారా వీడియో డౌన్‌లోడ్
    downloaded_file = await userbot.download_media(message=media_message, file_name=file_path)
    return downloaded_file

async def run_ultimate_fallback(client, message, url, quality, yt_id, existing_msg):
    """మెయిన్ బాట్ లోని engine.py పిలవాల్సిన అసలైన ఫంక్షన్"""
    user_id = message.from_user.id
    header = get_header(user_id)
    user = users_db.find_one({"user_id": user_id}) or {}
    
    await start_userbot() # Userbot రన్ అవుతోందో లేదో చెక్ చేస్తుంది
    
    if user.get("plan", "FREE") != "PREMIUM":
        await safe_edit_text(existing_msg, f"{header}🚫 <b>Download Failed</b>\n\nYouTube servers are strictly blocking normal requests right now. <b>Premium Users</b> get access to our Ultimate Multi-Bot Fallback system. Please upgrade to continue downloading!")
        return

    await safe_edit_text(existing_msg, f"{header}⚠️ <b>Standard Download Failed!</b>\n🚀 Initializing Ultimate Fallback Protocol...")
    
    # ముందు Priority 1, తర్వాత Priority 2 బాట్స్ కి వెళ్తుంది
    all_fallback_bots = PRIORITY_1_BOTS + PRIORITY_2_BOTS
    final_media_message = None
    successful_bot = ""

    for ext_bot in all_fallback_bots:
        final_media_message = await interact_with_fallback_bot(ext_bot, url, quality, existing_msg, header)
        if final_media_message:
            successful_bot = ext_bot
            break # సక్సెస్ అవ్వగానే లూప్ ఆపేస్తుంది

    if not final_media_message:
        await safe_edit_text(existing_msg, f"{header}❌ <b>Ultimate Fallback Failed!</b>\n\nAll our 5 backup servers are currently overloaded or blocked by YouTube. Please try again after some time.")
        return

    try:
        # 1. ఆ బాట్ దగ్గరి నుండి వీడియోని మన సర్వర్ కి లాగడం
        file_path = await download_and_clean_media(final_media_message, yt_id, user_id, existing_msg, header, quality)
        
        if not file_path or not os.path.exists(file_path):
            raise Exception("Failed to save media locally")

        # 2. థంబ్‌నైల్ మరియు యూట్యూబ్ డేటా ప్రిపరేషన్ (కింద ఉన్న చెత్తను తీసేసి మనవి యాడ్ చేయడం)
        api_title, yt_thumb_url = get_yt_metadata(yt_id)
        video_title = api_title if api_title != "YouTube Video" else "Downloaded via Fallback"
        
        custom_thumb = user.get("wallpaper_path")
        final_thumb = custom_thumb if custom_thumb and os.path.exists(custom_thumb) else None

        # వాల్‌పేపర్ లేకపోతే, కనీసం యూట్యూబ్ అఫీషియల్ థంబ్‌నైల్ అయినా ఇస్తాం (వాళ్ల బాట్ చెత్త రాకుండా)
        if not final_thumb and yt_thumb_url:
            yt_thumb_path = f"downloads/{yt_id}_thumb.jpg"
            try:
                img_data = requests.get(yt_thumb_url).content
                with open(yt_thumb_path, 'wb') as handler:
                    handler.write(img_data)
                final_thumb = yt_thumb_path
            except Exception: pass

        await safe_edit_text(existing_msg, f"{header}📤 <b>Uploading Cleaned Video to Telegram...</b>")
        
        share_url = f"https://t.me/share/url?url={url}"
        share_markup = InlineKeyboardMarkup([[InlineKeyboardButton("📤 Share Video With Friends 📤", url=share_url)]])
        reply_to_id = message.reply_to_message_id if message.reply_to_message else message.id

        # 3. యూజర్‌కి ఫైనల్ గా మన బాట్ నుండి, మన స్టైల్ లో వీడియో పంపడం!
        if quality == "audio":
            await client.send_audio(
                chat_id=user_id, 
                audio=file_path, 
                caption=f"{header}🎬 <b>{video_title}</b>", 
                thumb=final_thumb, 
                reply_to_message_id=reply_to_id,
                reply_markup=share_markup,
                progress=progress_bar, 
                progress_args=(existing_msg, video_title, header)
            )
        else:
            await client.send_video(
                chat_id=user_id, 
                video=file_path, 
                caption=f"{header}🎬 <b>{video_title}</b>", 
                thumb=final_thumb, 
                reply_to_message_id=reply_to_id,
                reply_markup=share_markup,
                progress=progress_bar, 
                progress_args=(existing_msg, video_title, header), 
                supports_streaming=True
            )

        await existing_msg.delete()
        
        # 4. సర్వర్ ఫ్రీ అవ్వడానికి ఫైల్స్ డిలీట్
        if os.path.exists(file_path): os.remove(file_path)
        if final_thumb and final_thumb != custom_thumb and os.path.exists(final_thumb): os.remove(final_thumb)

    except Exception as e:
        await safe_edit_text(existing_msg, f"{header}❌ <b>Processing Failed!</b>\n\nError during cleanup: `{str(e)}`")
