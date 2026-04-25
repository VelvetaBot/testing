import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import users_db
from datetime import datetime, timedelta

def get_header(user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    if plan == "PREMIUM": return "<blockquote><b>💎 Velveta Premium User                                                                                                                                                                                                        </b></blockquote>"
    elif plan == "ADS_PREMIUM": return "<blockquote><b> 📺 Velveta Semi Premium User                                                                                                                                                                                                                                                                             </b></blockquote>"
    else: return ""

# ==========================================
# 🌟 EXACT TIME EXPIRY CHECKER (గంటలు, నిమిషాలతో సహా) 🌟
# ==========================================
async def check_plan_expiry(client, user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    
    if plan != "FREE":
        expiry_date_str = user.get("plan_expiry")
        if expiry_date_str:
            # మనం సేవ్ చేసిన ఎక్సాక్ట్ టైమ్ ని మళ్ళీ తీసుకుంటున్నాం
            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d %H:%M:%S")
            if datetime.now() > expiry_date:
                # ప్లాన్ టైమ్ దాటిపోతే FREE కి మార్చేస్తుంది
                users_db.update_one({"user_id": user_id}, {"$set": {"plan": "FREE", "plan_started": None, "plan_expiry": None}})
                
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
# 🌟 MY PLAN COMMAND (కౌంట్ డౌన్ చూపించడానికి) 🌟
# ==========================================
@Client.on_message(filters.command(["my_plan", "myplan"]) & filters.private)
async def my_plan_cmd(client, message):
    user_id = message.from_user.id
    await check_plan_expiry(client, user_id) # ముందు ఎక్స్‌పైర్ అయ్యిందేమో చెక్ చేస్తాం
    
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    header = get_header(user_id)
    
    if plan == "FREE":
        await message.reply_text(f"{header}You are currently on the <b>FREE</b> plan.\n\n👉 Send /upgrade to get Premium features!", parse_mode=enums.ParseMode.HTML)
    else:
        expiry_str = user.get("plan_expiry")
        if expiry_str:
            expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            remaining = expiry_date - now
            
            # కౌంట్ డౌన్ లాజిక్ (మిగిలిన రోజులు, గంటలు, నిమిషాలు)
            days = remaining.days
            hours, remainder = divmod(remaining.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if days > 0:
                countdown_text = f"{days} Days, {hours} Hours, {minutes} Mins"
            else:
                countdown_text = f"{hours} Hours, {minutes} Mins"
            
            text = (
                f"{header}📊 <b>Your Current Plan Details:</b>\n━━━━━━━━━━━━━━\n\n"
                f"👑 <b>Plan:</b> {plan.replace('_', ' ')}\n"
                f"🕒 <b>Activated On:</b> {user.get('plan_started')}\n"
                f"⏳ <b>Time Remaining:</b> <code>{countdown_text}</code>\n\n"
                f"Enjoy your premium features! 🚀"
            )
            await message.reply_text(text, parse_mode=enums.ParseMode.HTML)

# ==========================================
# 🌟 ADS PLAN MENU 🌟
# ==========================================
@Client.on_callback_query(filters.regex(r"^pay\|ads$"))
async def pay_ads(client, callback_query):
    user_id = callback_query.from_user.id
    await check_plan_expiry(client, user_id)
    header = get_header(user_id)
    
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
    
    # ఇక్కడ callback_data లో "ప్లాన్_పేరు|గంటలు" అని పాస్ చేస్తున్నాం
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("1 Ad  (0.5 day)", callback_data="buy|ads|1 Ad|12"), InlineKeyboardButton("3 Ads (2 days)", callback_data="buy|ads|3 Ads|48")],
        [InlineKeyboardButton("5 Ads (4 days)", callback_data="buy|ads|5 Ads|96"), InlineKeyboardButton("7 Ads (9 days)", callback_data="buy|ads|7 Ads|216")],
        [InlineKeyboardButton("10 Ads (2 weeks)", callback_data="buy|ads|10 Ads|336"), InlineKeyboardButton("25 Ads (4 weeks)", callback_data="buy|ads|25 Ads|672")],
        [InlineKeyboardButton("30 Ads (30+2 days)", callback_data="buy|ads|30 Ads|768")],
        [InlineKeyboardButton("✅ Completed", callback_data="buy|ads|completed|0")]
    ])
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

# ==========================================
# 🌟 ADS ACTIVATION & DATABASE UPDATE 🌟
# ==========================================
@Client.on_callback_query(filters.regex(r"^buy\|ads\|(.*)\|(.*)$"))
async def process_buy_ads(client, callback_query):
    plan_name = callback_query.data.split("|")[2]
    hours_to_add = int(callback_query.data.split("|")[3])
    
    now = datetime.now()
    user_id = callback_query.from_user.id
    
    if plan_name == "completed":
        header = get_header(user_id)
        await callback_query.message.edit_text(f"{header}⚠️ <b>Plan not completed yet</b>\n\n📊 Selected: Ad Plan\n📈 Progress: 0 / X completed.\n❓ Facing any issue? Message us: @Velvetasupport\n\n👉 Please continue watching ads to proceed ▶️", parse_mode=enums.ParseMode.HTML)
    else:
        # గంటలను (Hours) బట్టి ఎక్సాక్ట్ ఎక్స్‌పైరీ టైమ్ క్యాలిక్యులేట్ చేస్తున్నాం
        expiry_date = now + timedelta(hours=hours_to_add)
        
        users_db.update_one(
            {"user_id": user_id}, 
            {"$set": {
                "plan": "ADS_PREMIUM", 
                "plan_started": now.strftime("%Y-%m-%d %H:%M:%S"),
                "plan_expiry": expiry_date.strftime("%Y-%m-%d %H:%M:%S")
            }}
        )
        
        header = get_header(user_id)
        text = (
            f"{header}🎉 <b>Plan Activated Successfully!</b>\n\n"
            f"💳 Payment Mode: Ads\n"
            f"🧾 Payment: {plan_name}\n"
            f"🕒 Activated On: {now.strftime('%Y-%m-%d %H:%M')}\n"
            f"⏳ <b>Valid Until: {expiry_date.strftime('%Y-%m-%d %H:%M')}</b>\n\n"
            f"🚀 <b>Features Unlocked:</b>\n"
            "✔️ Unlimited Downloads\n✔️ Anti Ban Speed\n✔️ Basic Support(Group)\n"
            "✔️ Free Primium Banner\n✔️ Anti Crash Proof\n✔️ User interference\n✔️ Quality Selection\n\n"
            "📊 Status: Active ✅\n\n"
            "👉 Send /start_forwarding to begin\n"
            "👉 Use <b>/my_plan</b> to check remaining time anytime!"
        )
        await callback_query.message.edit_text(text, parse_mode=enums.ParseMode.HTML)
