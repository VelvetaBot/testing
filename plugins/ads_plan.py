import random
import urllib.parse
import requests
import asyncio
from datetime import datetime, timedelta, timezone
from pyrogram import Client, filters, enums, StopPropagation
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import users_db
import config

ADS_PLANS = {"1": 0.5, "3": 2, "5": 4, "7": 9, "10": 14, "25": 28, "30": 32}
IST = timezone(timedelta(hours=5, minutes=30))

def get_header(user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    if plan == "PREMIUM": return "<blockquote><b>💎 Velveta Premium User                                                                                                                                                                                                        </b>                                                                                                                    </blockquote>"
    elif plan == "ADS": return "<blockquote><b> 📺 Velveta Semi Premium User                                                                                                                                                                                                                                                                             </b>                                                                                                                                                   </blockquote>"
    else: return ""

async def generate_ad_link(user_id, ad_number):
    bot_username = getattr(config, "BOT_USERNAME", "VelvetaForwarderBot")
    target_url = f"https://t.me/{bot_username}?start=ad_{user_id}_{ad_number}"
    encoded_url = urllib.parse.quote(target_url)
    shorteners = getattr(config, "SHORTENERS", {})
    if not shorteners: return None
    domain, api_key = random.choice(list(shorteners.items()))
    api_url = f"https://{domain}/api?api={api_key}&url={encoded_url}"
    try:
        res = requests.get(api_url, timeout=5).json()
        return res.get("shortenedUrl")
    except: return None

@Client.on_callback_query(filters.regex("show_ads_plan"))
async def show_ads_plan_menu(client, callback_query):
    header = get_header(callback_query.from_user.id)
    text = (
        f"{header}\n"
        "🔹 <b>Ads Plan</b>\n"
        "━━━━━━━━━━━━━━\n"
        "🚀 <b>Features:</b>\n"
        "✔️ 3+1 Forwarding tasks\n"
        "✔️ Auto-forwarding\n"
        "✔️ Media forwarding\n"
        "✔️ Link Auto reply\n"
        "✔️ Amazon link converter\n"
        "✔️ Add Head Text\n"
        "✔️ Hide links ON/OFF\n"
        "✔️ Unlimited forwards/day\n"
        "✔️ Basic support (TG Group)\n"
        "✔️ Anti-ban speed\n"
        "✔️ Delay it by about 2 minutes\n"
        "━━━━━━━━━━━━━━\n"
        "👇 <b>Choose your ads plan</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("1 Ad (0.5 day)", callback_data="select_adplan_1"), InlineKeyboardButton("3 Ads (2 days)", callback_data="select_adplan_3")],
        [InlineKeyboardButton("5 Ads (4 days)", callback_data="select_adplan_5"), InlineKeyboardButton("7 Ads (9 days)", callback_data="select_adplan_7")],
        [InlineKeyboardButton("10 Ads (2 weeks)", callback_data="select_adplan_10"), InlineKeyboardButton("25 Ads (4 weeks)", callback_data="select_adplan_25")],
        [InlineKeyboardButton("30 Ads (32 days)", callback_data="select_adplan_30")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_upgrade_menu")]
    ])
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^select_adplan_(\d+)$"))
async def start_ad_plan(client, callback_query):
    user_id = callback_query.from_user.id
    target_ads = int(callback_query.data.split("_")[2])
    days = ADS_PLANS[str(target_ads)]
    users_db.update_one({"user_id": user_id}, {"$set": {"ad_progress": {"target": target_ads, "completed": 0, "days": days}}})
    await send_next_ad(callback_query.message, user_id, 1, target_ads)

async def send_next_ad(message, user_id, current_ad_num, target_ads):
    short_url = await generate_ad_link(user_id, current_ad_num)
    if not short_url:
        await message.reply_text("❌ సర్వర్ బిజీగా ఉంది. దయచేసి కాసేపటి తర్వాత ప్రయత్నించండి.")
        return
    text = f"📺 <b>Ad Task {current_ad_num} of {target_ads}</b>\n\n👉 కింద ఉన్న బటన్ నొక్కి యాడ్ చూడండి. పూర్తయ్యాక తిరిగి బాట్ కి రండి."
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Watch Ad Now", url=short_url)], [InlineKeyboardButton("❌ Cancel Plan", callback_data="cancel_ad_plan")]])
    await message.edit_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.regex(r"^/start ad_") & filters.private, group=-1)
async def ad_return_handler(client, message):
    user_id = message.from_user.id
    user_data = users_db.find_one({"user_id": user_id})
    if not user_data or "ad_progress" not in user_data: return
    
    ad_progress = user_data["ad_progress"]
    completed = ad_progress["completed"] + 1
    target = ad_progress["target"]
    days = ad_progress["days"]
    
    if completed >= target:
        expiry_date = datetime.now(IST) + timedelta(days=days)
        now_str = datetime.now(IST).strftime('%Y-%m-%d %H:%M')
        users_db.update_one({"user_id": user_id}, {"$set": {"plan": "ADS", "expiry_date": expiry_date, "plan_started": datetime.now(IST)}, "$unset": {"ad_progress": ""}})
        
        success_text = (
            "🎉 <b>Plan Activated Successfully!</b>\n\n"
            "💳 <b>Payment Mode:</b> Ads\n"
            f"🧾 <b>Payment:</b> {target} Ad(s)\n"
            f"🕒 <b>Activated On:</b> {now_str}\n"
            f"⏳ <b>Valid Until:</b> {expiry_date.strftime('%Y-%m-%d %H:%M')}\n\n"
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
        users_db.update_one({"user_id": user_id}, {"$set": {"ad_progress.completed": completed}})
        await send_next_ad(message, user_id, completed + 1, target)
    raise StopPropagation
