import time
import requests
import asyncio
from datetime import datetime, timedelta, timezone
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import users_db
import config

IST = timezone(timedelta(hours=5, minutes=30))

def get_header(user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    if plan == "PREMIUM": return "<blockquote><b>💎 Velveta Premium User                                                                                                                                                                                                        </b>                                                                                                                    </blockquote>"
    elif plan == "ADS": return "<blockquote><b> 📺 Velveta Semi Premium User                                                                                                                                                                                                                                                                             </b>                                                                                                                                                   </blockquote>"
    else: return ""

@Client.on_callback_query(filters.regex("show_money_plan"))
async def money_plan_details(client, callback_query):
    header = get_header(callback_query.from_user.id)
    text = (
        f"{header}\n"
        "<b>🔸 Money Plan</b>\n"
        "━━━━━━━━━━━━━━\n"
        "🚀 <b>Features:</b>\n"
        "✔️ 15+2🆓 Tasks\n"
        "✔️ A to B forwarding System\n"
        "✔️ Auto forwarding enabled\n"
        "✔️ Header control\n"
        "✔️ Media forwarding\n"
        "✔️ Link preview\n"
        "✔️ Auto Delete Messages\n"
        "✔️ Remove Usernames\n"
        "✔️ Remove Links\n"
        "✔️ Mono Text ON/OFF\n"
        "✔️ Link Auto Replies\n"
        "✔️ Disable Hidden Links\n"
        "✔️ Add Blacklist Keywords\n"
        "✔️ Add Whitelist Keywords\n"
        "✔️ Add Header Text\n"
        "✔️ Add Footer Text\n"
        "✔️ Replace Usernames\n"
        "✔️ Replace words (Text)\n"
        "✔️ Trim single Words/Lines\n"
        "✔️ Transfer of Premium\n"
        "✔️ Replace Links\n"
        "✔️ Amazon Links Converter\n"
        "✔️ Delay Timer For Targets\n"
        "✔️ Forward Restricted Content\n"
        "✔️ Unlimited forwards/day\n"
        "✔️ Anti-Ban Speed Forwarding\n"
        "✔️ High Priority Support\n"
        "✔️ Fast delivery 💬\n\n"
        "<b>Select Your Payment Method 👇</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Pay with UPI 💳", callback_data="pay_upi")], 
        [InlineKeyboardButton("Pay with crypto 🪙", callback_data="pay_crypto")], 
        [InlineKeyboardButton("Pay with ⭐ Stars", callback_data="pay_stars")], 
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_upgrade_menu")]
    ])
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

# నోట్: ఇక్కడ పేమెంట్ వెరిఫికేషన్ లాజిక్ పాత కోడ్ లాగే ఉంటుంది.
# ప్లాన్ ఆక్టివేట్ అయినప్పుడు కింది మెసేజ్ వచ్చేలా మార్చాను:

async def activate_money_plan(client, user_id, amount, days):
    expiry_date = datetime.now(IST) + timedelta(days=days)
    now_str = datetime.now(IST).strftime('%Y-%m-%d %I:%M %p')
    users_db.update_one({"user_id": user_id}, {"$set": {"plan": "PREMIUM", "expiry_date": expiry_date, "plan_started": datetime.now(IST)}})
    
    header = get_header(user_id)
    success_text = (
        f"{header}\n\n"
        "🎉 <b>Plan Activated Successfully!</b>\n\n"
        "💳 <b>Payment Mode:</b> Money\n"
        f"🧾 <b>Amount Paid:</b> ₹{amount}\n"
        f"🕒 <b>Activated On:</b> {now_str}\n"
        f"⏳ <b>Valid Until:</b> {expiry_date.strftime('%Y-%m-%d %I:%M %p')}\n\n"
        "🚀 <b>Features Unlocked:</b>\n"
        "✔️ Unlimited Downloads\n"
        "✔️ Playlist Downloads\n"
        "✔️ Fast Download Speed\n"
        "✔️ High Priority Support\n"
        "✔️ Premium Banner Access\n"
        "✔️ Scheduled Downloads\n"
        "✔️ Save Videos\n"
        "✔️ Transfer Premium\n"
        "✔️ Multi-Platform Access (YT, TikTok, Instagram)\n"
        "✔️ Anti Crash Protection\n"
        "✔️ Auto Repair Link\n"
        "✔️ Wallpaper Setup\n"
        "✔️ Advanced Content Downloads\n"
        "✔️ Quality Selection\n"
        "✔️ Set Preferred Quality\n\n"
        "📊 <b>Status:</b> Active ✅\n\n"
        "👉 Send a YouTube link to start downloading\n"
        "👉 Use /my_plan to check details anytime"
    )
    await client.send_message(user_id, success_text, parse_mode=enums.ParseMode.HTML)
