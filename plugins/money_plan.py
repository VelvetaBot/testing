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
    if plan == "PREMIUM": 
        return "<blockquote><b>💎 Velveta Premium User                                                                                                                                                                                                        </b>                                                                                                                    </blockquote>\n"
    elif plan == "ADS": 
        return "<blockquote><b> 📺 Velveta Semi Premium User                                                                                                                                                                                                                                                                             </b>                                                                                                                                                   </blockquote>\n"
    else: 
        return ""

def create_nowpayments_invoice(data, headers):
    try: return requests.post("https://api.nowpayments.io/v1/invoice", json=data, headers=headers, timeout=10).json()
    except Exception as e: return {"error": str(e)}

def check_nowpayments_invoice(invoice_id, headers):
    try: return requests.get(f"https://api.nowpayments.io/v1/invoice/{invoice_id}", headers=headers, timeout=10).json()
    except Exception as e: return {"error": str(e)}

def create_cashfree_link(amount, user_id):
    url = "https://sandbox.cashfree.com/pg/links"
    headers = {"accept": "application/json", "content-type": "application/json", "x-api-version": "2023-08-01", "x-client-id": getattr(config, "CASHFREE_APP_ID", ""), "x-client-secret": getattr(config, "CASHFREE_SECRET_KEY", "")}
    payload = {"link_id": f"order_{user_id}_{int(time.time())}", "link_amount": float(amount), "link_currency": "INR", "link_purpose": "Velveta Subscription", "customer_details": {"customer_phone": "9999999999", "customer_name": f"User_{user_id}"}, "link_notify": {"send_sms": False, "send_email": False}}
    try: return requests.post(url, json=payload, headers=headers, timeout=10).json()
    except Exception as e: return {"error": str(e)}

def check_cashfree_status(link_id):
    url = f"https://sandbox.cashfree.com/pg/links/{link_id}"
    headers = {"accept": "application/json", "x-api-version": "2023-08-01", "x-client-id": getattr(config, "CASHFREE_APP_ID", ""), "x-client-secret": getattr(config, "CASHFREE_SECRET_KEY", "")}
    try: return requests.get(url, headers=headers, timeout=10).json()
    except Exception as e: return {"error": str(e)}

# ==========================================
# RESET & TRANSFER COMMANDS
# ==========================================
@Client.on_message(filters.command("reset_me") & filters.private)
async def reset_me_cmd(client, message):
    users_db.update_one(
        {"user_id": message.from_user.id},
        {"$set": {"plan": "FREE", "trial_claimed": False}, "$unset": {"expiry_date": "", "plan_started": "", "amount_paid": "", "ad_progress": "", "transfer_count": "", "warning_sent": ""}}
    )
    await message.reply_text("✅ <b>Account Reset Successfully!</b>\n\nYou are now on the FREE plan.", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("transfer_premium") & filters.private)
async def transfer_premium_cmd(client, message):
    user_id = message.from_user.id
    user_data = users_db.find_one({"user_id": user_id})
    if not user_data or user_data.get("plan") != "PREMIUM":
        await message.reply_text("⚠️ <b>Access Denied!</b>\nYou must be a Premium user to transfer your plan.", parse_mode=enums.ParseMode.HTML)
        return

    transfer_count = user_data.get("transfer_count", 0)
    if transfer_count >= 3:
        await message.reply_text("❌ <b>Transfer Limit Reached!</b>\nYou can only transfer your premium plan a maximum of 3 times.", parse_mode=enums.ParseMode.HTML)
        return

    args = message.text.split()
    if len(args) != 3:
        await message.reply_text("<b>⚠️ Usage:</b>\n<code>/transfer_premium {Your_User_Id} {Target_User_Id}</code>", parse_mode=enums.ParseMode.HTML)
        return

    try:
        sender_id = int(args[1])
        target_id = int(args[2])
        if sender_id != user_id:
            await message.reply_text("❌ Please provide YOUR correct User ID as the first argument.", parse_mode=enums.ParseMode.HTML)
            return

        expiry = user_data.get("expiry_date")
        started = user_data.get("plan_started")
        amount = user_data.get("amount_paid", "Transferred")

        users_db.update_one({"user_id": target_id}, {"$set": {"plan": "PREMIUM", "expiry_date": expiry, "plan_started": started, "amount_paid": f"{amount} (Transferred)"}}, upsert=True)
        users_db.update_one({"user_id": user_id}, {"$set": {"plan": "FREE", "transfer_count": transfer_count + 1}, "$unset": {"expiry_date": "", "plan_started": "", "amount_paid": ""}})

        await message.reply_text(f"✅ <b>Transfer Successful!</b>\nYour Premium plan has been transferred to <code>{target_id}</code>\nTransfers left: {2 - transfer_count}", parse_mode=enums.ParseMode.HTML)
        await client.send_message(target_id, "🎉 <b>Congratulations!</b>\nA Premium plan has been transferred to your account.", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text("❌ Error: Invalid IDs provided.", parse_mode=enums.ParseMode.HTML)

# ==========================================
# UPGRADE & MENUS
# ==========================================
@Client.on_message(filters.command("upgrade") & filters.private)
async def upgrade_cmd(client, message):
    user_data = users_db.find_one({"user_id": message.from_user.id})
    prefix_text = ""
    if user_data and user_data.get("plan", "FREE") != "FREE":
        expiry = user_data.get("expiry_date")
        if expiry and expiry.replace(tzinfo=timezone.utc).astimezone(IST) > datetime.now(IST):
            prefix_text = "⚠️ <b>You already have an active plan!</b>\n\n<i>Note: Upgrading now will overwrite your current plan.</i>\n\n"
                
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Ads 📺", callback_data="show_ads_plan")], [InlineKeyboardButton("Money 💰", callback_data="show_money_plan")]])
    await message.reply_text(f"{prefix_text}<b>💳 Choose a payment method:</b>", reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex("^show_upgrade$") | filters.regex("^back_to_upgrade_menu$"))
async def upgrade_callback(client, callback_query):
    try: await callback_query.answer() 
    except: pass
    user_data = users_db.find_one({"user_id": callback_query.from_user.id})
    prefix_text = ""
    if user_data and user_data.get("plan", "FREE") != "FREE":
        expiry = user_data.get("expiry_date")
        if expiry and expiry.replace(tzinfo=timezone.utc).astimezone(IST) > datetime.now(IST):
            prefix_text = "⚠️ <b>You already have an active plan!</b>\n\n<i>Note: Upgrading now will overwrite your current plan.</i>\n\n"
                
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Ads 📺", callback_data="show_ads_plan")], [InlineKeyboardButton("Money 💰", callback_data="show_money_plan")]])
    await callback_query.message.edit_text(f"{prefix_text}<b>💳 Choose a payment method:</b>", reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

# ... (Payment Button Callbacks - No Changes from your Exact Requested Prices) ...
@Client.on_callback_query(filters.regex("show_money_plan"))
async def money_plan_details(client, callback_query):
    try: await callback_query.answer()
    except: pass
    header = get_header(callback_query.from_user.id)
    text = (f"{header}<b>🔸 Money Plan</b>\n━━━━━━━━━━━━━━\n🚀 <b>Features:</b>\n✔️ Unlimited Downloads\n✔️ Playlist Downloads\n✔️ Fast Download Speed\n✔️ High Priority Support\n✔️ Premium Banner Access\n✔️ Scheduled Downloads\n✔️ Save Videos\n✔️ Transfer Premium\n✔️ Multi-Platform Access\n✔️ Anti Crash Protection\n✔️ Auto Repair Link\n✔️ Wallpaper Setup\n✔️ Advanced Content Downloads\n✔️ Quality Selection\n✔️ Set Preferred Quality\n\n<b>Select Your Payment Method 👇</b>")
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Pay with UPI 💳", callback_data="pay_upi")], [InlineKeyboardButton("Pay with crypto 🪙", callback_data="pay_crypto")], [InlineKeyboardButton("Pay with ⭐Telegram Stars", callback_data="pay_stars")], [InlineKeyboardButton("🔙 Back", callback_data="back_to_upgrade_menu")]])
    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex("pay_upi"))
async def upi_plans(client, callback_query):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("₹29 (1 week)", callback_data="gencf_29_7")], [InlineKeyboardButton("₹89 (3 weeks)", callback_data="gencf_89_21")], [InlineKeyboardButton("₹125 (1 month)", callback_data="gencf_125_30")], [InlineKeyboardButton("₹379 (3 months)", callback_data="gencf_379_90")], [InlineKeyboardButton("₹755 (6 months)", callback_data="gencf_755_180")], [InlineKeyboardButton("₹1519 (365+2 days)", callback_data="gencf_1519_367")], [InlineKeyboardButton("✅ Completed", callback_data="check_man_pay")], [InlineKeyboardButton("🔙 Back", callback_data="show_money_plan")]])
    await callback_query.message.edit_text("<b>📦 Please select a plan to continue</b>", reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex("pay_crypto"))
async def crypto_plans(client, callback_query):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("💲0.5 USDT (1 week)", callback_data="cryptoinv_0.5_7")], [InlineKeyboardButton("💲1.00 USDT (2 weeks)", callback_data="cryptoinv_1.0_14")], [InlineKeyboardButton("💲1.50 USDT (1 month)", callback_data="cryptoinv_1.5_30")], [InlineKeyboardButton("💲4.50 USDT (3 months)", callback_data="cryptoinv_4.5_90")], [InlineKeyboardButton("💲9.00 USDT (6 months)", callback_data="cryptoinv_9.0_180")], [InlineKeyboardButton("💲18.00 USDT (365+2 days)", callback_data="cryptoinv_18.0_367")], [InlineKeyboardButton("✅ Completed", callback_data="check_man_pay")], [InlineKeyboardButton("🔙 Back", callback_data="show_money_plan")]])
    await callback_query.message.edit_text("<b>📦 Please select a plan to continue</b>", reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex("pay_stars"))
async def stars_plans(client, callback_query):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⭐ 35 Stars (1 week)", callback_data="starinv_35_7")], [InlineKeyboardButton("⭐ 110 Stars (3 weeks)", callback_data="starinv_110_21")], [InlineKeyboardButton("⭐ 150 Stars (1 month)", callback_data="starinv_150_30")], [InlineKeyboardButton("⭐ 460 Stars (3 months)", callback_data="starinv_460_90")], [InlineKeyboardButton("⭐ 910 Stars (6 months)", callback_data="starinv_910_180")], [InlineKeyboardButton("⭐ 1830 Stars (365+2 days)", callback_data="starinv_1830_367")], [InlineKeyboardButton("✅ Completed", callback_data="check_man_pay")], [InlineKeyboardButton("🔙 Back", callback_data="show_money_plan")]])
    await callback_query.message.edit_text("<b>📦 Please select a plan to continue</b>", reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex("check_man_pay"))
async def check_man_pay(client, callback_query):
    await callback_query.answer("Status: Processing automatically. Contact Support if failed.", show_alert=True)

# 🌟 PAYMENT GENERATORS WITH STRICT "NO CHANGE" WARNINGS 🌟
@Client.on_callback_query(filters.regex(r"^gencf_(\d+)_(\d+)$"))
async def generate_cashfree_invoice(client, callback_query):
    try:
        await callback_query.answer("Generating Secure Payment Link...", show_alert=False)
        amount = int(callback_query.data.split("_")[1])
        days = int(callback_query.data.split("_")[2])
        user_id = callback_query.from_user.id
        res = await asyncio.to_thread(create_cashfree_link, amount, user_id)
        if "link_url" in res:
            text = f"🧾 <b>UPI Payment Link Generated</b>\n\n📦 <b>Plan:</b> {days} Days\n💰 <b>Amount:</b> ₹{amount}\n\n⚠️ <b>NOTE: Once payment is done, no plan changes or refunds are allowed!</b>\n\n👉 Click 'Pay Now' to complete your payment securely.\n⚠️ <i>Link expires in 10 minutes.</i>"
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("💳 Pay Now", url=res["link_url"])], [InlineKeyboardButton("🔙 Cancel", callback_data="pay_upi")]])
            sent_msg = await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
            asyncio.create_task(auto_verify_upi_payment(client, callback_query.message.chat.id, sent_msg.id, res["link_id"], days, f"₹{amount}", user_id))
        else: await callback_query.message.edit_text(f"❌ Failed: {res.get('message', 'API Error')}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="pay_upi")]]))
    except Exception as e: await callback_query.message.edit_text(f"❌ Error: {e}")

@Client.on_callback_query(filters.regex(r"^cryptoinv_([\d.]+)_(\d+)$"))
async def generate_nowpayments_invoice(client, callback_query):
    try: 
        await callback_query.answer("Generating Invoice...", show_alert=False)
        amount_usd = float(callback_query.data.split("_")[1])
        days = int(callback_query.data.split("_")[2])
        user_id = callback_query.from_user.id
        headers = {"x-api-key": getattr(config, "NOWPAYMENTS_API_KEY", ""), "Content-Type": "application/json"}
        data = {"price_amount": amount_usd, "price_currency": "usd", "order_description": f"Premium {days} Days"}
        res = await asyncio.to_thread(create_nowpayments_invoice, data, headers)
        if res.get("invoice_url"):
            text = f"🧾 <b>Crypto Invoice Generated</b>\n\n📦 <b>Plan:</b> {days} Days\n💰 <b>Amount:</b> ${amount_usd} USD\n\n⚠️ <b>NOTE: Once payment is done, no plan changes or refunds are allowed!</b>\n\n👉 Click 'Pay Now'. Use TRX, LTC or DOGE for low fees.\n⚠️ <i>Link expires in 10 minutes.</i>"
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("💳 Pay Now", url=res["invoice_url"])], [InlineKeyboardButton("🔙 Cancel", callback_data="pay_crypto")]])
            sent_msg = await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
            asyncio.create_task(auto_verify_crypto_payment(client, callback_query.message.chat.id, sent_msg.id, res["id"], days, f"${amount_usd}", user_id))
        else: await callback_query.message.edit_text(f"❌ Failed: {res.get('message', 'API Error')}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="pay_crypto")]]))
    except Exception as e: await callback_query.message.edit_text(f"❌ Error: {e}")

@Client.on_callback_query(filters.regex(r"^starinv_(\d+)_(\d+)$"))
async def send_star_invoice(client, callback_query):
    try:
        amount = int(callback_query.data.split("_")[1])
        days = int(callback_query.data.split("_")[2])
        url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendInvoice"
        payload = {"chat_id": callback_query.from_user.id, "title": "Velveta Premium 💎", "description": f"Upgrade ({amount} Stars for {days} Days)\n⚠️ Note: No changes allowed after payment.", "payload": f"premium_stars_{amount}_{days}", "provider_token": "", "currency": "XTR", "prices": [{"label": "Premium", "amount": amount}]}
        res = requests.post(url, json=payload).json()
        await callback_query.answer("Invoice sent!", show_alert=False)
        if res.get("ok"):
            asyncio.create_task(auto_delete_stars_invoice(client, callback_query.message.chat.id, res["result"]["message_id"]))
    except: pass

@Client.on_message(filters.create(lambda _, __, message: bool(getattr(message, "successful_payment", None))))
async def payment_success(client, message):
    try:
        user_id = message.from_user.id
        payload = message.successful_payment.invoice_payload
        if payload.startswith("premium_stars_"):
            parts = payload.split("_")
            await activate_money_plan(client, user_id, f"⭐ {parts[2]} Stars", int(parts[3]))
    except: pass

# 🌟 VERIFIERS 🌟
async def auto_verify_crypto_payment(client, chat_id, message_id, invoice_id, days, amount_text, user_id):
    headers = {"x-api-key": getattr(config, "NOWPAYMENTS_API_KEY", "")}
    for _ in range(200):
        await asyncio.sleep(3)
        res = await asyncio.to_thread(check_nowpayments_invoice, invoice_id, headers)
        if res.get("payment_status") in ["finished", "completed", "confirming", "sending"]:
            await activate_money_plan(client, user_id, amount_text, days)
            try: await client.delete_messages(chat_id, message_id)
            except: pass
            return
    try: await client.edit_message_text(chat_id, message_id, "⏳ <b>Invoice Expired</b>\n\nPayment link expired.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade", callback_data="show_upgrade")]]), parse_mode=enums.ParseMode.HTML)
    except: pass

async def auto_verify_upi_payment(client, chat_id, message_id, link_id, days, amount_text, user_id):
    for _ in range(200):
        await asyncio.sleep(3)
        res = await asyncio.to_thread(check_cashfree_status, link_id)
        if res.get("link_status") == "PAID":
            await activate_money_plan(client, user_id, amount_text, days)
            try: await client.delete_messages(chat_id, message_id)
            except: pass
            return
    try: await client.edit_message_text(chat_id, message_id, "⏳ <b>Invoice Expired</b>\n\nPayment link expired.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade", callback_data="show_upgrade")]]), parse_mode=enums.ParseMode.HTML)
    except: pass

async def auto_delete_stars_invoice(client, chat_id, message_id):
    await asyncio.sleep(600)
    try:
        await client.delete_messages(chat_id, message_id)
        await client.send_message(chat_id, "⏳ <b>Invoice Expired</b>\n\nStars payment link expired.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade", callback_data="show_upgrade")]]), parse_mode=enums.ParseMode.HTML)
    except: pass

async def activate_money_plan(client, user_id, amount, days):
    expiry_date = datetime.now(IST) + timedelta(days=days)
    now_str = datetime.now(IST).strftime('%Y-%m-%d %I:%M %p')
    expiry_str = expiry_date.strftime('%Y-%m-%d %I:%M %p')
    
    users_db.update_one({"user_id": user_id}, {"$set": {"plan": "PREMIUM", "expiry_date": expiry_date, "plan_started": datetime.now(IST), "amount_paid": amount, "warning_sent": False}})
    
    header = get_header(user_id)
    success_text = (
        f"{header}"
        "🎉 <b>Plan Activated Successfully!</b>\n\n"
        "💳 <b>Payment Mode:</b> Money\n"
        f"🧾 <b>Amount Paid:</b> {amount}\n"
        f"🕒 <b>Activated On:</b> {now_str}\n"
        f"⏳ <b>Valid Until:</b> {expiry_str}\n\n"
        "🚀 <b>Features Unlocked:</b>\n"
        "✔️ Unlimited Downloads\n"
        "✔️ Playlist Downloads\n"
        "✔️ Fast Download Speed\n"
        "✔️ High Priority Support\n"
        "✔️ Premium Banner Access\n"
        "✔️ Scheduled Downloads\n"
        "✔️ Save Videos\n"
        "✔️ Transfer Premium\n"
        "✔️ Multi-Platform Access\n"
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

# 🌟 MONEY PLAN EXPIRY WARNING & REMOVAL (1-Day Reminder Included) 🌟
async def money_expiry_checker(client):
    while True:
        try:
            users = users_db.find({"plan": "PREMIUM"})
            now = datetime.now(IST)
            for user in users:
                expiry = user.get("expiry_date")
                user_id = user["user_id"]
                if expiry:
                    if expiry.tzinfo is None: expiry = expiry.replace(tzinfo=timezone.utc).astimezone(IST)
                    
                    # 1 Day Expiry Warning
                    time_left = expiry - now
                    if timedelta(hours=23) <= time_left <= timedelta(hours=25) and not user.get("warning_sent"):
                        try:
                            warn_msg = f"⚠️ <b>Reminder!</b>\n\nYour Premium Plan is expiring in exactly <b>1 Day</b> (on {expiry.strftime('%Y-%m-%d %I:%M %p')}).\n\nPlease renew your plan to continue enjoying uninterrupted premium features."
                            await client.send_message(user_id, warn_msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Renew Plan", callback_data="show_upgrade")]]), parse_mode=enums.ParseMode.HTML)
                            users_db.update_one({"user_id": user_id}, {"$set": {"warning_sent": True}})
                        except: pass
                    
                    if now >= expiry:
                        users_db.update_one({"user_id": user_id}, {"$set": {"plan": "FREE"}, "$unset": {"warning_sent": ""}})
                        try:
                            await client.send_message(user_id, "⚠️ <b>Alert: Your Premium Plan has Expired!</b>\n\nYour account has been downgraded to the FREE plan. Please upgrade to regain your features.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade", callback_data="show_upgrade")]]), parse_mode=enums.ParseMode.HTML)
                        except: pass
        except: pass
        await asyncio.sleep(3600)
