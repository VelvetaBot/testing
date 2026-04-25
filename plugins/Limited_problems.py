import re
import requests
import asyncio
import google.generativeai as genai
from pyrogram import Client, filters, enums, StopPropagation
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import users_db
import config

# ==========================================
# 🌟 GOOGLE GEMINI AI CONFIGURATION 🌟
# ==========================================
GEMINI_API_KEY = "AIzaSyB3KfZfHcUlN9n4s6teCk0CqO5WkCFOIaU"
genai.configure(api_key=GEMINI_API_KEY)

async def get_gemini_smart_reply(user_text):
    """యూజర్ పంపిన టెక్స్ట్ ని బట్టి జెమినీ ద్వారా స్మార్ట్ రిప్లై తెచ్చే ఫంక్షన్"""
    def fetch_ai_response():
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = (
            f"You are a polite and helpful customer support AI for the 'Velveta YouTube Downloader Telegram Bot'. "
            f"A user sent this message: '{user_text}'. "
            f"Reply in 1 or 2 short sentences in the SAME language the user used. "
            f"Politely explain that you can only process YouTube links and ask them to send a valid YouTube link."
        )
        response = model.generate_content(prompt)
        return response.text

    try:
        # టెలిగ్రామ్ బాట్ ఆగిపోకుండా బ్యాక్‌గ్రౌండ్ లో AI తో మాట్లాడే లాజిక్
        return await asyncio.to_thread(fetch_ai_response)
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "I couldn't understand that. Please send a valid YouTube link or use a command from the menu."

# 🌟 ఫుల్ స్పేస్ & బోల్డ్ బ్రాండింగ్ 🌟
def get_header(user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    if plan == "PREMIUM": return "<blockquote><b>💎 VELVETA PREMIUM USER 💎\n━━━━━━━━━━━━━━━━━━━━━</b></blockquote>\n\n"
    elif plan == "ADS_PREMIUM": return "<blockquote><b>📺 VELVETA SEMI PREMIUM 📺\n━━━━━━━━━━━━━━━━━━━━━</b></blockquote>\n\n"
    else: return ""

# 🌟 యూనివర్సల్ సపోర్ట్ బటన్ 🌟
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
            # పాత ఫైల్ నుండి క్వాలిటీ బటన్స్ పిలుస్తున్నాం
            from plugins.engine import show_quality_buttons
            await show_quality_buttons(client, message, saved_url, yt_id, user_id, header)

# ==========================================
# 2. GLOBAL PROBLEM INTERCEPTOR (Group -6)
# ==========================================
@Client.on_message(filters.text & filters.private & ~filters.command(["start", "help", "reveal", "setcookies", "setproxy", "schedule", "save", "delete", "wallpaper", "set_pref_quality", "users", "notify", "problems", "set_FreeBot", "set_freebot"]), group=-6)
async def problem_interceptor(client, message):
    text = message.text
    user_id = message.from_user.id
    header = get_header(user_id)
    
    yt_id = extract_yt_id(text)
    
    # 🔴 1. LIVE STREAM ERROR (YouTube API వాడి చెక్ చేయడం) 🔴
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
    
    # 🤖 2. COMPLETELY INVALID LINK / UNKNOWN TEXT (GEMINI AI ACTIVATION) 🤖
    if not yt_id and "youtu" not in text:
        proc_msg = await message.reply_text("🤖 <i>Processing...</i>", parse_mode=enums.ParseMode.HTML)
        
        # యూజర్ పెట్టిన టెక్స్ట్ ని జెమినీకి పంపి రిప్లై తెచ్చుకోవడం
        ai_reply = await get_gemini_smart_reply(text)
        
        err_text = (
            f"{header}✨ <b>Velveta AI Assistant:</b>\n\n"
            f"{ai_reply}\n\n"
            f"If you want further support, please message us! 👇"
        )
        await proc_msg.edit_text(err_text, reply_markup=get_support_btn(), parse_mode=enums.ParseMode.HTML)
        raise StopPropagation

# ==========================================
# 3. 18+ (NSFW) CONTENT ERROR HANDLER
# ==========================================
async def handle_18_plus_error(client, message, user_id):
    header = get_header(user_id)
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    
    if plan != "PREMIUM":
        text = (
            f"{header}🔞 <b>Age-Restricted Content (18+)</b>\n\n"
            f"This video contains age-restricted content. Downloading 18+ content is strictly reserved for our <b>Premium Users</b>.\n\n"
            f"Please upgrade your plan using the /upgrade command to download this video.\n\n"
            f"If you want further support, please message us! 👇"
        )
    else:
        text = (
            f"{header}🔞 <b>18+ Content Blocked by YouTube</b>\n\n"
            f"Even with your Premium plan, YouTube's strict servers have blocked this specific age-restricted video from being downloaded securely.\n\n"
            f"If you want further support, please message us! 👇"
        )
        
    await client.send_message(chat_id=user_id, text=text, reply_markup=get_support_btn(), parse_mode=enums.ParseMode.HTML)
