import re
import requests
from pyrogram import Client, filters, enums
from pyrogram import StopPropagation
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import users_db
import config

try:
    from google import genai
except ImportError:
    genai = None

def get_header(user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    if plan == "PREMIUM": return "<blockquote><b>💎 Velveta Premium User                                                                                                                                                                                                        </b></blockquote>\n\n"
    elif plan == "ADS_PREMIUM": return "<blockquote><b> 📺 Velveta Semi Premium User                                                                                                                                                                                                                                                                             </b></blockquote>\n\n"
    else: return ""

def get_support_btn():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⚒️ Message Support", url="https://t.me/Velvetasupport")]])

def extract_yt_id(text):
    match = re.search(r"(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})", text)
    return match.group(2) if match else None

# ==========================================
# 1. REVEAL COMMAND ERROR HANDLING
# ==========================================
@Client.on_message(filters.command("reveal") & filters.private)
async def reveal_cmd(client, message):
    user_id = message.from_user.id
    user = users_db.find_one({"user_id": user_id}) or {}
    saved_url = user.get("saved_link")
    header = get_header(user_id)
    
    if not saved_url:
        text = (
            f"{header}📭 <b>Empty Storage!</b>\n\n"
            f"You haven't saved any links or videos yet. Please use the /save command to store your favorite content.\n\n"
            f"If you want further support, please message us! 👇"
        )
        await message.reply_text(text, reply_markup=get_support_btn(), parse_mode=enums.ParseMode.HTML)
        return
        
    if saved_url.startswith("vid:"):
        await client.send_video(user_id, saved_url.split("vid:")[1])
    else:
        yt_id = extract_yt_id(saved_url)
        if yt_id: 
            from plugins.engine import show_quality_buttons
            await show_quality_buttons(client, message, saved_url, yt_id, user_id, header)

# ==========================================
# 2. GLOBAL PROBLEM INTERCEPTOR (Group -6)
# ==========================================
@Client.on_message(filters.text & filters.private & ~filters.command(["start", "help", "reveal", "setcookies", "setproxy", "schedule", "save", "delete_save", "wallpaper", "set_pref_quality", "users", "notify", "problems", "set_FreeBot", "set_freebot", "raise_ticket", "view_tickets", "Resolved", "my_plan", "myplan", "upgrade", "cancel"]), group=-6)
async def problem_interceptor(client, message):
    text = message.text
    user_id = message.from_user.id
    
    # 🌟 CRITICAL FIX: యూజర్ స్టేట్ లో (ఉదాహరణకు Date/Time ఇస్తుంటే) ఉంటే ఇంటర్‌సెప్ట్ చేయకూడదు 🌟
    user = users_db.find_one({"user_id": user_id}) or {}
    if user.get("state"):
        return
        
    header = get_header(user_id)
    yt_id = extract_yt_id(text)
    
    # 🔴 1. LIVE STREAM ERROR 🔴
    if yt_id:
        api_key = getattr(config.Config, "YOUTUBE_API_KEY", None)
        if api_key:
            try:
                url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={yt_id}&key={api_key}"
                res = requests.get(url, timeout=5).json()
                if res.get("items"):
                    live_status = res["items"][0]["snippet"].get("liveBroadcastContent")
                    if live_status == "live":
                        err_text = (
                            f"{header}🔴 <b>Live Stream Detected!</b>\n\n"
                            f"Sorry, I cannot download videos that are currently broadcasting live. Please wait until the live stream ends and try again.\n\n"
                            f"If you want further support, please message us! 👇"
                        )
                        await message.reply_text(err_text, reply_markup=get_support_btn(), parse_mode=enums.ParseMode.HTML)
                        raise StopPropagation 
            except Exception:
                pass
    
    # ❌ 2. INVALID LINK / GEMINI AI CHAT ❌
    if not yt_id and "youtu" not in text:
        gemini_key = getattr(config.Config, "GEMINI_API_KEY", None)
        
        if gemini_key and genai:
            try:
                gemini_client = genai.Client(api_key=gemini_key)
                prompt = f"A user sent this message to my YouTube Downloader Telegram bot: '{text}'. Give a short, polite 1-2 sentence reply in English explaining that you are a bot and can only download YouTube links. Do not use bold formatting or markdown."
                
                response = gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                ai_reply = response.text.strip()
                err_text = f"{header}🤖 <b>AI Assistant:</b>\n\n{ai_reply}\n\n👇 If you need human support, click below!"
                
            except Exception as e:
                print(f"Gemini API Error: {e}")
                # 🌟 Gemini కీ లీక్ అయ్యి బ్లాక్ అయితే వచ్చే ఎర్రర్ 🌟
                if "PERMISSION_DENIED" in str(e) or "leaked" in str(e).lower():
                    err_text = f"{header}❌ <b>Invalid Input!</b>\n\nPlease send a valid YouTube link.\n\n<i>(Admin Note: Gemini API key is blocked/leaked. Please update config.py)</i>\n\n👇 If you want further support, please message us!"
                else:
                    err_text = f"{header}❌ <b>Invalid Input!</b>\n\nPlease send a valid YouTube link.\n\n👇 If you want further support, please message us!"
        else:
            err_text = (
                f"{header}❌ <b>Invalid Input!</b>\n\n"
                f"I couldn't understand that. Please send a valid YouTube link or use a command from the menu.\n\n"
                f"If you want further support, please message us! 👇"
            )
            
        await message.reply_text(err_text, reply_markup=get_support_btn(), parse_mode=enums.ParseMode.HTML)
        raise StopPropagation
