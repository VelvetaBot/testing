import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import users_db
from datetime import datetime, timedelta

# ==========================================
# 🌟 ఫుల్ స్పేస్ & బోల్డ్ బ్రాండింగ్ 🌟
# ==========================================
def get_header(user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    # మొబైల్ స్క్రీన్ కి సరిపోయేలా స్పేస్‌లు సగానికి తగ్గించాను
    if plan == "PREMIUM": return "<blockquote><b>💎 Velveta Premium User </b>ㅤㅤㅤㅤㅤㅤㅤㅤ</blockquote>\n\n"
    elif plan == "ADS_PREMIUM": return "<blockquote><b>📺 Velveta Semi Premium </b>ㅤㅤㅤㅤㅤㅤ</blockquote>\n\n"
    else: return ""

# ==========================================
# 🌟 ఎక్స్‌పైరీ చెకింగ్ (ప్రతిసారి యూజర్ కమాండ్ వాడినప్పుడు) 🌟
# ==========================================
async def check_plan_expiry(client, user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    
    if plan != "FREE":
        expiry_date_str = user.get("plan_expiry")
        if expiry_date_str:
            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
            if datetime.now().date() > expiry_date:
                # 🔴 ప్లాన్ ఎక్స్‌పైర్ అయితే ఆటోమేటిక్ గా FREE కి మార్చడం
                users_db.update_one({"user_id": user_id}, {"$set": {"plan": "FREE", "plan_started": None, "plan_expiry": None}})
                
                # 🔴 మీరు అడిగిన వార్నింగ్ మెసేజ్
                text = (
                    "⚠️ <b>Your Plan Has Expired!</b>\n\n"
                    "Your Premium/Ads plan validity has ended. Your account has been downgraded to the FREE plan.\n\n"
                    "👉 Send /upgrade to renew your plan and unlock all features!"
                )
                try:
                    await client.send_message(chat_id=user_id, text=text, parse_mode=enums.ParseMode.HTML)
                except:
                    pass

# ==========================================
# 🌟 అప్‌గ్రేడ్ కమాండ్ లాజిక్ 🌟
# ==========================================
@Client.on_message(filters.command("upgrade") & filters.private)
@Client.on_callback_query(filters.regex("^upgrade_menu$"))
async def upgrade_cmd(client, event):
    user_id = event.from_user.id
    
    # ముందు ప్లాన్ ఎక్స్‌పైర్ అయ్యిందేమో చెక్ చేయి
    await check_plan_expiry(client, user_id)
    
    header = get_header(user_id)
    text = f"{header}💳 <b>Choose a payment method:</b> Money or Ads"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Ads", callback_data="pay|ads"), InlineKeyboardButton("Money", callback_data="pay|money")]])
    
    if hasattr(event, "data"):
        await event.message.edit_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
    else:
        await event.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^pay\|money$"))
async def pay_money(client, callback_query):
    user_id = callback_query.from_user.id
    await check_plan_expiry(client, user_id)
    header = get_header(user_id)
    
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
# 🌟 ఫైనల్ పేమెంట్ వెరిఫికేషన్ & డేటాబేస్ అప్‌డేట్ 🌟
# ==========================================
@Client.on_callback_query(filters.regex(r"^buy\|(upi|stars|crypto)\|(.*)\|(.*)$"))
async def process_buy_money(client, callback_query):
    parts = callback_query.data.split("|")
    method = parts[1]
    plan_id = parts[2]
    days_to_add = int(parts[3])
    
    now = datetime.now()
    user_id = callback_query.from_user.id
    
    if plan_id == "completed":
        # నోట్: టెంపరరీగా టెస్టింగ్ కోసం "Completed" నొక్కితే 30 రోజులు ఇస్తున్నాం.
        # ఒరిజినల్ ప్రొడక్షన్ లో మీరు పేమెంట్ వెరిఫై చేసాకే దీన్ని అప్రూవ్ చేయాలి.
        expiry_date = (now + timedelta(days=30)).date() 
        
        users_db.update_one(
            {"user_id": user_id}, 
            {"$set": {"plan": "PREMIUM", "plan_started": str(now.date()), "plan_expiry": str(expiry_date)}}
        )
        header = get_header(user_id)
        text = (
            f"{header}🎉 <b>Plan Activated Successfully!</b>\n\n"
            f"💳 Payment Mode: {method.upper()}\n"
            f"🧾 Amount Paid: Verified\n"
            f"🕒 Activated On: {now.strftime('%Y-%m-%d %H:%M')}\n"
            f"⏳ <b>Valid Until: {expiry_date}</b>\n\n"
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
        # యూజర్ ప్లాన్ బటన్ నొక్కినప్పుడు, ఆ ప్లాన్ కి సంబంధించిన డేటా సేవ్ చేసి వెరిఫికేషన్ అడగడం
        users_db.update_one({"user_id": user_id}, {"$set": {"pending_plan_days": days_to_add}})
        header = get_header(user_id)
        await callback_query.message.edit_text(f"{header}Please pay the amount for {plan_id} and click ✅ Completed to verify.", parse_mode=enums.ParseMode.HTML)
