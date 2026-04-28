import random
import urllib.parse
import requests
import asyncio
from datetime import datetime, timedelta, timezone
from pyrogram import Client, filters, enums, StopPropagation
from pyrogram.errors import MessageNotModified
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import users_db
import config

ADS_PLANS = {"1": 0.5, "3": 2, "5": 4, "7": 9, "10": 14, "25": 28, "30": 32}
IST = timezone(timedelta(hours=5, minutes=30))

def get_header(user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    if plan == "PREMIUM": 
        return "<blockquote><b>💎 Velveta Premium User                                                                                                                                                                                                        </b>                                                                                                                    </blockquote>"
    elif plan == "ADS": 
        return "<blockquote><b> 📺 Velveta Semi Premium User                                                                                                                                                                                                                                                                             </b>                                                                                                                                                   </blockquote>"
    else: 
        return ""

async def generate_ad_link(user_id, ad_number):
    bot_username = getattr(config, "BOT_USERNAME", "VelvetaYTDownloaderBot")
    target_url = f"https://t.me/{bot_username}?start=ad_{user_id}_{ad_number}"
    encoded_url = urllib.parse.quote(target_url)
    shorteners = getattr(config, "SHORTENERS", {})
    if not shorteners: return None
    for _ in range(3):
        domain, api_key = random.choice(list(shorteners.items()))
        api_url = f"https://{domain}/api?api={api_key}&url={encoded_url}"
        try:
            res = requests.get(api_url, timeout=5).json()
            if res and (res.get("status") == "success" or res.get("status") == 1):
                return res.get("shortenedUrl")
        except: pass
    return None

@Client.on_callback_query(filters.regex("show_ads_plan"))
async def show_ads_plan_menu(client, callback_query):
    try: await callback_query.answer()
    except: pass
    header = get_header(callback_query.from_user.id)
    text = (
        f"{header}\n"
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

async def send_next_ad(message, user_id, current_ad_num, target_ads):
    short_url = await generate_ad_link(user_id, current_ad_num)
    if not short_url:
        text = f"📺 <b>Ad Task {current_ad_num} of {target_ads}</b>\n\n❌ <b>Servers are busy!</b> Could not generate ad link. Please click 'Change Link'."
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⚠️ Ad not working (Change Link)", callback_data=f"skip_ad_{current_ad_num}")], [InlineKeyboardButton("❌ Cancel Plan", callback_data="cancel_ad_plan")]])
    else:
        text = f"📺 <b>Ad Task {current_ad_num} of {target_ads}</b>\n\n👉 Click the button below, solve the shortlink, and return to the bot."
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Watch Ad Now", url=short_url)], [InlineKeyboardButton("⚠️ Ad not working (Change Link)", callback_data=f"skip_ad_{current_ad_num}")], [InlineKeyboardButton("❌ Cancel Plan", callback_data="cancel_ad_plan")]])
    try: await message.edit_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
    except MessageNotModified: pass

@Client.on_callback_query(filters.regex(r"^skip_ad_(\d+)$"))
async def change_ad_link(client, callback_query):
    try: await callback_query.answer("Changing Ad Link...", show_alert=False)
    except: pass
    user_id = callback_query.from_user.id
    target_ads = users_db.find_one({"user_id": user_id}).get("ad_progress", {}).get("target", 1)
    await send_next_ad(callback_query.message, user_id, int(callback_query.data.split("_")[2]), target_ads)

@Client.on_callback_query(filters.regex("cancel_ad_plan"))
async def cancel_ad_plan_handler(client, callback_query):
    try: await callback_query.answer("Plan Cancelled", show_alert=True)
    except: pass
    users_db.update_one({"user_id": callback_query.from_user.id}, {"$unset": {"ad_progress": ""}})
    await callback_query.message.edit_text("❌ <b>Ads Plan Cancelled.</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade", callback_data="show_upgrade")]]), parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.regex(r"^/start ad_") & filters.private, group=-1)
async def ad_return_handler(client, message):
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
        users_db.update_one({"user_id": user_id}, {"$set": {"plan": "ADS", "expiry_date": expiry_date, "plan_started": datetime.now(IST), "amount_paid": f"{target} Ads"}, "$unset": {"ad_progress": ""}})
        header = get_header(user_id)
        success_text = (
            f"{header}\n"
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
        text = f"✅ <b>Ad {completed} completed!</b>\n\n👉 Please continue to Ad {completed + 1}."
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(f"▶️ Please continue Ad {completed + 1}", callback_data=f"resend_ad_{completed + 1}")], [InlineKeyboardButton("⚠️ Ad not working (Change Link)", callback_data=f"skip_ad_{completed + 1}")], [InlineKeyboardButton("❌ Cancel Plan", callback_data="cancel_ad_plan")]])
        await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
    raise StopPropagation

@Client.on_callback_query(filters.regex(r"^resend_ad_(\d+)$"))
async def resend_ad_action(client, callback_query):
    try: await callback_query.answer()
    except: pass
    user_id = callback_query.from_user.id
    target = users_db.find_one({"user_id": user_id}).get("ad_progress", {}).get("target", 1)
    await send_next_ad(callback_query.message, user_id, int(callback_query.data.split("_")[2]), target)

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
                            await client.send_message(user["user_id"], "⚠️ <b>Alert: Your Ads Plan has Expired!</b>\n\nYour account has been downgraded to the FREE plan. Please upgrade to continue enjoying premium features.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade", callback_data="show_upgrade")]]), parse_mode=enums.ParseMode.HTML)
                        except: pass
        except: pass
        await asyncio.sleep(3600)

