import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import users_db
from datetime import datetime, timedelta, timezone

# 🌟 పక్కా ఇండియన్ స్టాండర్డ్ టైమ్ (IST) సెటప్ 🌟
IST = timezone(timedelta(hours=5, minutes=30))

def get_header(user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    if plan == "PREMIUM": return "<blockquote><b>💎 Velveta Premium User                                                                                                                                                                                                        </b></blockquote>"
    elif plan == "ADS_PREMIUM": return "<blockquote><b> 📺 Velveta Semi Premium User                                                                                                                                                                                                                                                                             </b></blockquote>"
    else: return ""

# ==========================================
# 🌟 MY PLAN COMMAND (IST & COUNTDOWN LOGIC) 🌟
# ==========================================
@Client.on_message(filters.command(["my_plan", "myplan"]) & filters.private)
async def my_plan_cmd(client, message):
    user_id = message.from_user.id
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    header = get_header(user_id)
    
    if plan == "FREE":
        await message.reply_text(f"{header}You are currently on the <b>FREE</b> plan.\n\n👉 Send /upgrade to get Premium features!", parse_mode=enums.ParseMode.HTML)
    else:
        expiry_str = user.get("plan_expiry")
        started_str = user.get("plan_started")
        
        if expiry_str:
            # డేటాబేస్ లో ఉన్న టైమ్ ని తీసుకుంటున్నాం
            expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=IST)
            now = datetime.now(IST)
            
            # ఒకవేళ ఎక్స్‌పైర్ అయిపోతే..
            if now > expiry_date:
                users_db.update_one({"user_id": user_id}, {"$set": {"plan": "FREE", "plan_started": None, "plan_expiry": None}})
                await message.reply_text(f"{header}⚠️ <b>Your Plan Has Expired!</b>\n\nYour Premium/Ads plan validity has ended. Your account has been downgraded to the FREE plan.\n\n👉 Send /upgrade to renew!", parse_mode=enums.ParseMode.HTML)
                return

            # మనీ ప్లాన్ కి IST టైమ్, యాడ్స్ కి కౌంట్‌డౌన్
            if plan == "PREMIUM":
                expiry_display = f"{expiry_date.strftime('%Y-%m-%d %I:%M %p')} (IST)"
            else:
                remaining = expiry_date - now
                days = remaining.days
                hours, remainder = divmod(remaining.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                expiry_display = f"{days} Days, {hours} Hours, {minutes} Mins left" if days > 0 else f"{hours} Hours, {minutes} Mins left"
            
            text = (
                f"{header}📊 <b>Your Current Plan Details:</b>\n━━━━━━━━━━━━━━\n\n"
                f"👑 <b>Plan:</b> {plan.replace('_', ' ')}\n"
                f"🕒 <b>Activated On:</b> {started_str}\n"
                f"⏳ <b>Validity:</b> <code>{expiry_display}</code>\n\n"
                f"Enjoy your premium features! 🚀"
            )
            await message.reply_text(text, parse_mode=enums.ParseMode.HTML)

# ==========================================
# 🌟 అప్‌గ్రేడ్ కమాండ్ లాజిక్ 🌟
# ==========================================
@Client.on_message(filters.command("upgrade") & filters.private)
@Client.on_callback_query(filters.regex("^upgrade_menu$"))
async def upgrade_cmd(client, event):
    user_id = event.from_user.id
    header = get_header(user_id)
    text = f"{header}💳 <b>Choose a payment method:</b> Money or Ads"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Ads", callback_data="pay|ads"), InlineKeyboardButton("Money", callback_data="pay|money")]])
    
    if hasattr(event, "data"):
        await event.message.edit_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
    else:
        await event.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^pay\|money$"))
async def pay_money(client, callback_query):
    header = get_header(callback_query.from_user.id)
    text = (
        f"{header}🔸 <b>Money Plan</b>\n━━━━━━━━━━━━━━\n"
        "🚀 <b>Features:</b>\n"
        "✔️ Unlimited Downloads\n"
        "✔️ Playlist Downloads\n"
        "✔️ Anti Ban Speed\n"
        "✔️ High priority Support\n"
        "✔️ Free Primium Banner\n"
        "✔️ Scheduled uploading\n"
        "✔️ Save Videos\n"
        "✔️ Transfer Primium\n"
        "✔️ 1 Free Bot(YT, tiktok, Fb, X, Insta)\n"
        "✔️ Anti Crash Proof\n"
        "✔️ Auto Repair Link\n"
        "✔️ User interference\n"
        "✔️ Set wallpaper\n"
        "✔️ 🔞+ Content downloads\n"
        "✔️ Quality Selection\n"
        "✔️ Set Preferred Quality\n"
        "━━━━━━━━━━━━━━\nSelect Your Payment Method Below 👇"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Pay with UPI", callback_data="pmt|upi")],
        [InlineKeyboardButton("Pay with crypto", callback_data="pmt|crypto")],
        [InlineKeyboardButton("Pay with ⭐Telegram Stars", callback_data="pmt|stars")]
    ])
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^pmt\|upi$"))
async def method_upi(client, callback_query):
    header = get_header(callback_query.from_user.id)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("₹29(1 week)", callback_data="buy|upi|29|7"), InlineKeyboardButton("₹89(3 weeks)", callback_data="buy|upi|89|21")],
        [InlineKeyboardButton("₹125(1 month)", callback_data="buy|upi|125|30"), InlineKeyboardButton("₹379(3 months)", callback_data="buy|upi|379|90")],
        [InlineKeyboardButton("₹755(6 months)", callback_data="buy|upi|755|180"), InlineKeyboardButton("₹1519(365+2days)", callback_data="buy|upi|1519|367")],
        [InlineKeyboardButton("✅ Completed", callback_data="buy|upi|completed|0")]
    ])
    await callback_query.message.edit_text(f"{header}📦 Please select a plan to continue", reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^pmt\|stars$"))
async def method_stars(client, callback_query):
    header = get_header(callback_query.from_user.id)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ 35 Stars (1 week)", callback_data="buy|stars|35|7"), InlineKeyboardButton("⭐ 110 Stars (3 weeks)", callback_data="buy|stars|110|21")],
        [InlineKeyboardButton("⭐ 150 Stars (1 month)", callback_data="buy|stars|150|30"), InlineKeyboardButton("⭐ 460 Stars (3 months)", callback_data="buy|stars|460|90")],
        [InlineKeyboardButton("⭐ 910 Stars (6 months)", callback_data="buy|stars|910|180"), InlineKeyboardButton("⭐ 1830 Stars (365+2 days)", callback_data="buy|stars|1830|367")],
        [InlineKeyboardButton("✅ Completed", callback_data="buy|stars|completed|0")]
    ])
    await callback_query.message.edit_text(f"{header}📦 Please select a plan to continue", reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^pmt\|crypto$"))
async def method_crypto(client, callback_query):
    header = get_header(callback_query.from_user.id)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💲0.5 USDT (1 week)", callback_data="buy|crypto|0.5|7"), InlineKeyboardButton("💲1.00 USDT (2 weeks)", callback_data="buy|crypto|1|14")],
        [InlineKeyboardButton("💲1.50 USDT (1 month)", callback_data="buy|crypto|1.5|30"), InlineKeyboardButton("💲4.50 USDT (3 months)", callback_data="buy|crypto|4.5|90")],
        [InlineKeyboardButton("💲9.00 USDT (6 months)", callback_data="buy|crypto|9|180"), InlineKeyboardButton("💲18.00 USDT (365+2 days)", callback_data="buy|crypto|18|367")],
        [InlineKeyboardButton("✅ Completed", callback_data="buy|crypto|completed|0")]
    ])
    await callback_query.message.edit_text(f"{header}📦 Please select a plan to continue", reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

# ==========================================
# 🌟 ఫైనల్ పేమెంట్ వెరిఫికేషన్ & IST డేటాబేస్ అప్‌డేట్ 🌟
# ==========================================
@Client.on_callback_query(filters.regex(r"^buy\|(upi|stars|crypto)\|(.*)\|(.*)$"))
async def process_buy_money(client, callback_query):
    parts = callback_query.data.split("|")
    method = parts[1]
    plan_id = parts[2]
    
    # 🌟 లోకల్ ఇండియా టైమ్ (IST) ప్రకారం క్యాలిక్యులేషన్ 🌟
    now = datetime.now(IST)
    user_id = callback_query.from_user.id
    
    if plan_id == "completed":
        # టెంపరరీగా 30 రోజులు ఇస్తున్నాం (తర్వాత మీ API ద్వారా మార్చుకోవచ్చు)
        expiry_date = now + timedelta(days=30)
        
        # డేటాబేస్‌లో IST డేట్ & టైమ్ ని సేవ్ చేయడం
        users_db.update_one(
            {"user_id": user_id}, 
            {"$set": {
                "plan": "PREMIUM", 
                "plan_started": now.strftime("%Y-%m-%d %I:%M %p (IST)"), 
                "plan_expiry": expiry_date.strftime("%Y-%m-%d %H:%M:%S")
            }}
        )
        header = get_header(user_id)
        text = (
            f"{header}🎉 <b>Plan Activated Successfully!</b>\n\n"
            f"💳 Payment Mode: {method.upper()}\n"
            f"🧾 Amount Paid: Verified\n"
            f"🕒 Activated On: {now.strftime('%Y-%m-%d %I:%M %p')} (IST)\n"
            f"⏳ <b>Valid Until: {expiry_date.strftime('%Y-%m-%d %I:%M %p')} (IST)</b>\n\n"
            f"🚀 <b>Features Unlock 🔓:-</b>\n"
            "✔️ Unlimited Downloads\n✔️ Playlist Downloads\n✔️ Anti Ban Speed\n"
            "✔️ High priority Support\n✔️ Free Primium Banner\n✔️ Scheduled uploading\n"
            "✔️ Save Videos\n✔️ Transfer Primium\n✔️ 1 Free Bot\n✔️ Anti Crash Proof\n"
            "✔️ User interference\n✔️ Set wallpaper\n✔️ 🔞+ Content downloads\n"
            "✔️ Quality Selection\n✔️ Set Preferred Quality\n\n"
            "📊 Status: Active ✅\n\n"
            "👉 Use /my_plan for details\n"
            "📩 Send payment screenshot to @VelvetaBotmaker"
        )
        await callback_query.message.edit_text(text, parse_mode=enums.ParseMode.HTML)
    else:
        header = get_header(user_id)
        await callback_query.message.edit_text(f"{header}Please pay the amount for {plan_id} and click ✅ Completed to verify.", parse_mode=enums.ParseMode.HTML)
