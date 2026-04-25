import re
from pyrogram import Client, filters, enums, StopPropagation
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
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
# 🌟 GLOBAL LIMIT CHECKER (Priority -7) 🌟
# ప్రైవేట్ చాట్ మరియు గ్రూప్ చాట్ రెండింటినీ ఇది కంట్రోల్ చేస్తుంది
# ==========================================
@Client.on_message((filters.private | filters.group) & filters.text, group=-7)
async def global_limit_manager(client, message):
    text = message.text
    yt_id = extract_yt_id(text)
    
    # యూట్యూబ్ లింక్ కాకపోతే వదిలేస్తుంది
    if not yt_id:
        return 

    user_id = message.from_user.id
    user = users_db.find_one({"user_id": user_id})
    
    # కొత్త యూజర్ అయితే డేటాబేస్ లో యాడ్ చేయడం
    if not user:
        users_db.insert_one({
            "user_id": user_id, 
            "plan": "FREE", 
            "bot_count": 0, 
            "group_count": 0
        })
        user = users_db.find_one({"user_id": user_id})
        
    plan = user.get("plan", "FREE")
    bot_count = user.get("bot_count", 0)
    group_count = user.get("group_count", 0)
    
    # 🌟 మీరు చెప్పిన టోటల్ 10 లిమిట్ లాజిక్ (గ్రూప్ + బాట్) 🌟
    total_used = bot_count + group_count
    header = get_header(user_id)
    
    if plan == "FREE":
        if total_used >= 10:
            # 10 లిమిట్స్ అయిపోతే...
            # మీ ఒరిజినల్ బాట్ యూజర్‌నేమ్ ఇక్కడ మార్చుకోండి (ఉదా: VelvetaYTDownloaderBot)
            bot_username = getattr(config.Config, "BOT_USERNAME", "VelvetaYTDownloaderBot") 
            
            limit_text = (
                f"{header}🚫 <b>Free Limit Exhausted!</b> 🚫\n\n"
                f"Oops! You have successfully used all your <b>10 Free Downloads</b> (Combined limits for Bot & Groups).\n\n"
                f"To continue downloading unlimited videos, please upgrade to our <b>Ads Premium</b> or <b>Premium</b> plan. 💎"
            )
            
            # గ్రూప్‌లో ఉంటే బాట్‌కి వెళ్లేలా, బాట్‌లో ఉంటే అప్‌గ్రేడ్ కమాండ్ చూపేలా రీ-డైరెక్ట్ బటన్
            if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("💎 Upgrade Plan (Go to Bot) 💎", url=f"https://t.me/{bot_username}?start=upgrade")]
                ])
            else:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("💎 Upgrade Plan 💎", callback_data="upgrade_plan_btn")] # ఈ కాల్‌బ్యాక్ మీ మనీ ప్లాన్‌లో ఉంటుంది
                ])
                
            await message.reply_text(limit_text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
            
            # లిమిట్ అయిపోయింది కాబట్టి కింది ఫైల్స్ (engine.py) కి వెళ్లకుండా ఆపేస్తుంది
            raise StopPropagation 
            
        else:
            # లిమిట్ ఇంకా ఉంటే... ఏ చోట వాడితే ఆ కౌంట్ పెంచుతుంది
            if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                users_db.update_one({"user_id": user_id}, {"$inc": {"group_count": 1}})
            else:
                users_db.update_one({"user_id": user_id}, {"$inc": {"bot_count": 1}})
                
            # కౌంట్ పెంచేసి సైలెంట్ గా వదిలేస్తుంది... ఆటోమేటిక్ గా తర్వాతి ఫైల్ (engine.py) రన్ అయిపోయి క్వాలిటీ బటన్స్ వచ్చేస్తాయి!

