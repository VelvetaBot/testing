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

@Client.on_callback_query(filters.regex(r"^pay\|ads$"))
async def pay_ads(client, callback_query):
    header = get_header(callback_query.from_user.id)
    text = (
        f"{header}🔹 <b>Ads Plan</b>\n━━━━━━━━━━━━━━\n"
        "🚀 <b>Features:</b>\n"
        "✔️ Unlimited Downloads\n"
        "✔️ Anti Ban Speed\n"
        "✔️ Basic Support(Group)\n"
        "✔️ Free Primium Banner\n"
        "✔️ Anti Crash Proof\n"
        "✔️ User interference\n"
        "✔️ Quality Selection\n"
        "━━━━━━━━━━━━━━\n👇 Choose your ads plan"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("1 Ad  (0.5 day)", callback_data="buy|ads|1"), InlineKeyboardButton("3 Ads (2 days)", callback_data="buy|ads|3")],
        [InlineKeyboardButton("5 Ads (4 days)", callback_data="buy|ads|5"), InlineKeyboardButton("7 Ads (9 days)", callback_data="buy|ads|7")],
        [InlineKeyboardButton("10 Ads (2 weeks)", callback_data="buy|ads|10"), InlineKeyboardButton("25 Ads (4 weeks)", callback_data="buy|ads|25")],
        [InlineKeyboardButton("30 Ads (30+2 days)", callback_data="buy|ads|30")],
        [InlineKeyboardButton("✅ Completed", callback_data="buy|ads|completed")]
    ])
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^buy\|ads\|(.*)$"))
async def process_buy_ads(client, callback_query):
    plan_id = callback_query.data.split("|")[2]
    now = datetime.now()
    user_id = callback_query.from_user.id
    
    if plan_id == "completed":
        header = get_header(user_id)
        await callback_query.message.edit_text(f"{header}⚠️ <b>Plan not completed yet</b>\n\n📊 Selected: Ad Plan\n📈 Progress: 0 / X completed.\n❓ Facing any issue? Message us: @Velvetasupport\n\n👉 Please continue watching ads to proceed ▶️", parse_mode=enums.ParseMode.HTML)
    else:
        users_db.update_one({"user_id": user_id}, {"$set": {"plan": "ADS_PREMIUM", "plan_started": str(now.date())}})
        header = get_header(user_id)
        text = f"{header}🎉 <b>Plan Activated Successfully!</b>\n\n💳 Payment Mode: Ads\n🧾 Payment:- {plan_id} Ads\n🕒 Activated On: {now.strftime('%Y-%m-%d %H:%M')}\n\n🚀 <b>Features Unlocked:</b>\n✔️ Unlimited Downloads\n✔️ Anti Ban Speed\n✔️ Basic Support(Group)\n✔️ Free Primium Banner\n✔️ Anti Crash Proof\n✔️ User interference\n✔️ Quality Selection\n\n📊 Status: Active ✅\n\n👉 Send /start_forwarding to begin\n👉 Use /my_plan to check details anytime"
        await callback_query.message.edit_text(text, parse_mode=enums.ParseMode.HTML)
