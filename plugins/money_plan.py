from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import users_db
from datetime import datetime

def get_header(user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    if plan == "PREMIUM": return "<blockquote>💎 Velveta Premium User</blockquote>\n"
    elif plan == "ADS_PREMIUM": return "<blockquote>📺 Velveta Semi Premium User</blockquote>\n"
    else: return ""

@Client.on_message(filters.command("upgrade") & filters.private)
@Client.on_callback_query(filters.regex("^upgrade_menu$"))
async def upgrade_cmd(client, event):
    user_id = event.from_user.id
    header = get_header(user_id)
    text = f"{header}💳 Choose a payment method: Money or Ads"
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
        [InlineKeyboardButton("₹29(1 week)", callback_data="buy|upi|29"), InlineKeyboardButton("₹89(3 weeks)", callback_data="buy|upi|89")],
        [InlineKeyboardButton("₹125(1 month)", callback_data="buy|upi|125"), InlineKeyboardButton("₹379(3 months)", callback_data="buy|upi|379")],
        [InlineKeyboardButton("₹755(6 months)", callback_data="buy|upi|755"), InlineKeyboardButton("₹1519(365+2days)", callback_data="buy|upi|1519")],
        [InlineKeyboardButton("✅ Completed", callback_data="buy|upi|completed")]
    ])
    await callback_query.message.edit_text(f"{header}📦 Please select a plan to continue", reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^pmt\|stars$"))
async def method_stars(client, callback_query):
    header = get_header(callback_query.from_user.id)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ 35 Stars (1 week)", callback_data="buy|stars|35"), InlineKeyboardButton("⭐ 110 Stars (3 weeks)", callback_data="buy|stars|110")],
        [InlineKeyboardButton("⭐ 150 Stars (1 month)", callback_data="buy|stars|150"), InlineKeyboardButton("⭐ 460 Stars (3 months)", callback_data="buy|stars|460")],
        [InlineKeyboardButton("⭐ 910 Stars (6 months)", callback_data="buy|stars|910"), InlineKeyboardButton("⭐ 1830 Stars (365+2 days)", callback_data="buy|stars|1830")],
        [InlineKeyboardButton("✅ Completed", callback_data="buy|stars|completed")]
    ])
    await callback_query.message.edit_text(f"{header}📦 Please select a plan to continue", reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^pmt\|crypto$"))
async def method_crypto(client, callback_query):
    header = get_header(callback_query.from_user.id)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💲0.5 USDT (1 week)", callback_data="buy|crypto|0.5"), InlineKeyboardButton("💲1.00 USDT (2 weeks)", callback_data="buy|crypto|1")],
        [InlineKeyboardButton("💲1.50 USDT (1 month)", callback_data="buy|crypto|1.5"), InlineKeyboardButton("💲4.50 USDT (3 months)", callback_data="buy|crypto|4.5")],
        [InlineKeyboardButton("💲9.00 USDT (6 months)", callback_data="buy|crypto|9"), InlineKeyboardButton("💲18.00 USDT (365+2 days)", callback_data="buy|crypto|18")],
        [InlineKeyboardButton("✅ Completed", callback_data="buy|crypto|completed")]
    ])
    await callback_query.message.edit_text(f"{header}📦 Please select a plan to continue", reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^buy\|(upi|stars|crypto)\|(.*)$"))
async def process_buy_money(client, callback_query):
    method = callback_query.data.split("|")[1]
    plan_id = callback_query.data.split("|")[2]
    now = datetime.now()
    user_id = callback_query.from_user.id
    
    if plan_id == "completed":
        users_db.update_one({"user_id": user_id}, {"$set": {"plan": "PREMIUM", "plan_started": str(now.date())}})
        header = get_header(user_id)
        text = f"{header}🎉 <b>Plan Activated Successfully!</b>\n\n💳 Payment Mode: {method.upper()}\n🧾 Amount Paid: Verified\n🕒 Activated On: {now.strftime('%Y-%m-%d %H:%M')}\n\n🚀 <b>Features Unlock 🔓:-</b>\n✔️ Unlimited Downloads\n✔️ Playlist Downloads\n✔️ Anti Ban Speed\n✔️ High priority Support\n✔️ Free Primium Banner\n✔️ Scheduled uploading\n✔️ Save Videos\n✔️ Transfer Primium\n✔️ 1 Free Bot\n✔️ Anti Crash Proof\n✔️ User interference\n✔️ Set wallpaper\n✔️ 🔞+ Content downloads\n✔️ Quality Selection\n✔️ Set Preferred Quality\n\n📊 Status: Active ✅\n\n👉 Use /my_plan for details\n📩 Send payment screenshot to @VelvetaBotmaker"
        await callback_query.message.edit_text(text, parse_mode=enums.ParseMode.HTML)
    else:
        header = get_header(user_id)
        await callback_query.message.edit_text(f"{header}Please pay the amount for {plan_id} and click ✅ Completed to verify.", parse_mode=enums.ParseMode.HTML)
