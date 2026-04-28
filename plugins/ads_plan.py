import random
import urllib.parse
import requests
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pyrogram import Client, filters, enums, StopPropagation
from pyrogram.errors import MessageNotModified
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import users_db
import config

ADS_PLANS = {"1": 0.5, "3": 2, "5": 4, "7": 9, "10": 14, "25": 28, "30": 32}
IST = timezone(timedelta(hours=5, minutes=30))

# లాగ్స్ ని సెట్ చేస్తున్నాం, లోపల ఏం జరిగినా బయట పడుతుంది!
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_header(user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    if plan == "PREMIUM": 
        return "<blockquote><b>💎 Velveta Premium User                                                                                                                                                                                                        </b>                                                                                                                    </blockquote>\n"
    elif plan == "ADS": 
        return "<blockquote><b> 📺 Velveta Semi Premium User                                                                                                                                                                                                                                                                             </b>                                                                                                                                                   </blockquote>\n"
    else: 
        return ""

def fetch_shortlink(api_url):
    try:
        # బ్రౌజర్ లాగా యాక్ట్ చేయడానికి పవర్ఫుల్ హెడర్స్
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        res = requests.get(api_url, headers=headers, timeout=15)
        
        logger.info(f"API Response Code: {res.status_code}") # లాగ్ లో పడుతుంది
        
        # 1. JSON చెకింగ్
        try:
            data = res.json()
            logger.info(f"API JSON Response: {data}")
            if data and (str(data.get("status")).lower() in ["success", "1", "true"] or "shortenedUrl" in data or "short_url" in data):
                return data.get("shortenedUrl") or data.get("short_url") or data.get("url")
        except ValueError:
            pass # JSON ఫెయిల్ అయితే టెక్స్ట్ కి వెళ్తుంది
            
        # 2. Text చెకింగ్
        text_res = res.text.strip()
        logger.info(f"API Text Response: {text_res[:50]}...")
        if text_res.startswith("http"):
            return text_res
            
        return None
    except Exception as e:
        logger.error(f"Error fetching shortlink: {e}") # అసలు ఎర్రర్ లాగ్ లో పడుతుంది
        return None

async def generate_ad_link(user_id, ad_number):
    bot_username = getattr(config, "BOT_USERNAME", "VelvetaYTDownloaderBot")
    target_url = f"https://t.me/{bot_username}?start=ad_{user_id}_{ad_number}"
    encoded_url = urllib.parse.quote(target_url)
    
    shorteners = getattr(config, "SHORTENERS", {})
    if not shorteners: 
        logger.error("No SHORTENERS found in config!")
        return None 
        
    shortener_list = list(shorteners.items())
    
    for attempt in range(5):
        if not shortener_list: break
        domain, api_key = random.choice(shortener_list)
        api_url = f"https://{domain}/api?api={api_key}&url={encoded_url}"
        
        logger.info(f"Attempt {attempt+1}: Trying {domain}...")
        
        short_url = await asyncio.to_thread(fetch_shortlink, api_url)
        if short_url:
            return short_url
            
    return None 

@Client.on_callback_query(filters.regex("show_ads_plan"))
async def show_ads_plan_menu(client, callback_query):
    try: await callback_query.answer()
    except: pass
    header = get_header(callback_query.from_user.id)
    text = (
        f"{header}"
        "📦 <b>Please select a plan to continue</b>\n\n"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("1 Ad  (0.5 day)", callback_data="select_adplan_1")],
        [InlineKeyboardButton("3 Ads (2 days)", callback_data="select_adplan_3")],
        [InlineKeyboardButton("5 Ads (4 days)", callback_data="select_adplan_5")],
        [InlineKeyboardButton("7 Ads (9 days)", callback_data="select_adplan_7")],
        [InlineKeyboardButton("10 Ads (2 weeks)", callback_data="select_adplan_10")],
        [InlineKeyboardButton("25 Ads (4 weeks)", callback_data="select_adplan_25")],
        [InlineKeyboardButton("30 Ads (30+2 days)", callback_data="select_adplan_30")],
        [InlineKeyboardButton("✅ Completed", callback_data="check_ads_status")]
    ])
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex("check_ads_status"))
async def check_ads_status(client, callback_query):
    await callback_query.answer("Status: Please complete the given Ad tasks or check /my_plan", show_alert=True)

@Client.on_callback_query(filters.regex(r"^select_adplan_(\d+)$"))
async def start_ad_plan(client, callback_query):
    try: await callback_query.answer("Processing...", show_alert=False)
    except: pass
    user_id = callback_query.from_user.id
    target_ads = int(callback_query.data.split("_")[2])
    days = ADS_PLANS[str(target_ads)]
    
    users_db.update_one({"user_id": user_id}, {"$set": {"ad_progress": {"target": target_ads, "completed": 0, "days": days}}})
    await send_next_ad(callback_query.message, user_id, 1, target_ads)

async def send_next_ad(message, user_id, current_ad_num, target_ads, is_edit=True):
    short_url = await generate_ad_link(user_id, current_ad_num)
    if not short_url:
        text = f"📺 <b>Ad Task {current_ad_num} of {target_ads}</b>\n\n❌ <b>Servers are busy!</b> Could not generate ad link. Please click 'Change Link'."
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚠️ Ad not working (Change Link)", callback_data=f"skip_ad_{current_ad_num}")],
            [InlineKeyboardButton("❌ Cancel Plan", callback_data="cancel_ad_plan")]
        ])
    else:
        text = f"📺 <b>Ad Task {current_ad_num} of {target_ads}</b>\n\n👉 Click the button below, solve the shortlink, and return to the bot.\n<i>(Ref: {random.randint(100,999)})</i>"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Watch Ad Now", url=short_url)],
            [InlineKeyboardButton("⚠️ Ad not working (Change Link)", callback_data=f"skip_ad_{current_ad_num}")],
            [InlineKeyboardButton("❌ Cancel Plan", callback_data="cancel_ad_plan")]
        ])
        
    try: 
        if is_edit: await message.edit_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
        else: await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
    except MessageNotModified:
        pass
    except Exception as e:
        logger.error(f"Telegram Edit Error: {e}")

@Client.on_callback_query(filters.regex(r"^skip_ad_(\d+)$"))
async def change_ad_link(client, callback_query):
    try: await callback_query.answer("Changing Ad Link...", show_alert=False)
    except: pass
    user_id = callback_query.from_user.id
    target_ads = users_db.find_one({"user_id": user_id}).get("ad_progress", {}).get("target", 1)
    await send_next_ad(callback_query.message, user_id, int(callback_query.data.split("_")[2]), target_ads, is_edit=True)

@Client.on_callback_query(filters.regex("cancel_ad_plan"))
async def cancel_ad_plan_handler(client, callback_query):
    try: await callback_query.answer("Plan Cancelled", show_alert=True)
    except: pass
    users_db.update_one({"user_id": callback_query.from_user.id}, {"$unset": {"ad_progress": ""}})
    await callback_query.message.edit_text("❌ <b>Ads Plan Cancelled.</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade", callback_data="show_upgrade")]]), parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.regex(r"^/start ad_") & filters.private, group=-1)
async def ad_return_handler(client, message):
    try:
        user_id = message.from_user.id
        parts = message.text.split("_")
        if str(user_id) != parts[1]: raise StopPropagation
            
        user_data = users_db.find_one({"user_id": user_id})
        if not user_data or "ad_progress" not in user_data: raise StopPropagation
            
        ad_progress = user_data["ad_progress"]
        target = ad_progress["target"]
        completed = ad_progress["completed"] + 1
        days = ad_progress["days"]
        
        users_db.update_one({"user_id": user_id}, {"$set": {"ad_progress.completed": completed}})
        
        if completed >= target:
            expiry_date = datetime.now(IST) + timedelta(days=days)
            now_str = datetime.now(IST).strftime('%Y-%m-%d %H:%M')
            expiry_str = expiry_date.strftime('%Y-%m-%d %I:%M %p')
            
            users_db.update_one({"user_id": user_id}, {"$set": {"plan": "ADS", "expiry_date": expiry_date, "plan_started": datetime.now(IST), "amount_paid": f"{target} Ad(s)"}, "$unset": {"ad_progress": ""}})
            
            header = get_header(user_id)
            success_text = (
                f"{header}"
                "🎉 <b>Plan Activated Successfully!</b>\n\n"
                "💳 <b>Payment Mode:</b> Ads\n"
                f"🧾 <b>Payment:</b> {target} Ad(s)\n"
                f"🕒 <b>Activated On:</b> {now_str}\n"
                f"⏳ <b>Valid Until:</b> {expiry_str}\n\n"
                "🚀 <b>Features Unlocked:</b>\n"
                "✔️ Unlimited Downloads\n"
                "✔️ Fast Download Speed\n"
                "✔️ Basic Support (Group)\n"
                "✔️ Premium Banner Access\n"
                "✔️ Anti Crash Protection\n"
                "✔️ Quality Selection\n\n"
                "📊 <b>Status:</b> Active ✅\n\n"
                "👉 Send a YouTube link to start downloading\n"
                "👉 Use /my_plan to check remaining time anytime"
            )
            await message.reply_text(success_text, parse_mode=enums.ParseMode.HTML)
        else:
            text = f"✅ <b>Ad {completed} completed!</b>\n\n👉 Please continue to Ad {completed + 1}."
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"▶️ Please continue Ad {completed + 1}", callback_data=f"resend_ad_{completed + 1}")],
                [InlineKeyboardButton("⚠️ Ad not working (Change Link)", callback_data=f"skip_ad_{completed + 1}")],
                [InlineKeyboardButton("❌ Cancel Plan", callback_data="cancel_ad_plan")]
            ])
            await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
            
    except StopPropagation: raise
    except Exception as e: logger.error(f"Ad Return Error: {e}")
    raise StopPropagation

@Client.on_callback_query(filters.regex(r"^resend_ad_(\d+)$"))
async def resend_ad_action(client, callback_query):
    try: await callback_query.answer()
    except: pass
    user_id = callback_query.from_user.id
    target = users_db.find_one({"user_id": user_id}).get("ad_progress", {}).get("target", 1)
    await send_next_ad(callback_query.message, user_id, int(callback_query.data.split("_")[2]), target, is_edit=True)

async def ads_expiry_checker(client):
    while True:
        try:
            users = users_db.find({"plan": "ADS"})
            now = datetime.now(IST)
            for user in users:
                expiry = user.get("expiry_date")
                if expiry:
                    if expiry.tzinfo is None: expiry = expiry.replace(tzinfo=timezone.utc).astimezone(IST)
                    if now >= expiry:
                        users_db.update_one({"user_id": user["user_id"]}, {"$set": {"plan": "FREE"}})
                        try:
                            await client.send_message(
                                user["user_id"], 
                                "⚠️ <b>Alert: Your Ads Plan has Expired!</b>\n\nYour account has been downgraded to the FREE plan. Please upgrade to continue enjoying premium features.", 
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade", callback_data="show_upgrade")]]), 
                                parse_mode=enums.ParseMode.HTML
                            )
                        except: pass
        except: pass
        await asyncio.sleep(3600)
