import os
import random
import string
from datetime import datetime
from pyrogram import Client, filters, enums, StopPropagation
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import users_db
import config

# టికెట్స్ సేవ్ చేయడానికి సపరేట్ డేటాబేస్ కలెక్షన్
tickets_db = users_db.database["tickets"]

# 🌟 ఫుల్ స్పేస్ & బోల్డ్ బ్రాండింగ్ 🌟
def get_header(user_id):
    user = users_db.find_one({"user_id": user_id}) or {}
    plan = user.get("plan", "FREE")
    if plan == "PREMIUM": return "<blockquote><b>💎 Velveta Premium User</b>\n</blockquote>\n\n"
    elif plan == "ADS_PREMIUM": return "<blockquote><b>💎 Velveta Semi Premium User</b>\n</blockquote>\n\n"
    else: return ""

def generate_ticket_id():
    """యూనిక్ టికెట్ నెంబర్ జనరేట్ చేయడానికి (ఉదా: TKT-A8X9)"""
    chars = string.ascii_uppercase + string.digits
    random_str = ''.join(random.choice(chars) for _ in range(6))
    return f"TKT-{random_str}"

def is_admin(user_id, username):
    admin_id = str(getattr(config.Config, "ADMIN_ID", ""))
    return str(user_id) == admin_id or str(username).lower() == admin_id.lower()

# ==========================================
# 1. RAISE TICKET COMMAND (User)
# ==========================================
@Client.on_message(filters.command("raise_ticket") & filters.private)
async def raise_ticket_cmd(client, message):
    users_db.update_one({"user_id": message.from_user.id}, {"$set": {"state": "raising_ticket"}})
    header = get_header(message.from_user.id)
    
    text = (
        f"{header}🎫 <b>Raise a Support Ticket</b>\n\n"
        f"Please describe your issue in detail. You can also send a <b>Photo or Video</b> along with your description (caption).\n\n"
        f"📝 <i>Type your issue below or send media...</i>"
    )
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]])
    await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

# ==========================================
# 2. TICKET STATE MANAGER (Intercepting User Message/Media) Group -5
# ==========================================
@Client.on_message((filters.text | filters.photo | filters.video | filters.document) & filters.private, group=-5)
async def ticket_state_manager(client, message):
    user_id = message.from_user.id
    user = users_db.find_one({"user_id": user_id}) or {}
    state = user.get("state")
    header = get_header(user_id)

    if state == "raising_ticket":
        ticket_id = generate_ticket_id()
        description = ""
        media_id = None
        media_type = None

        # యూజర్ పంపింది టెక్స్ట్ అయితే
        if message.text:
            description = message.text
        # యూజర్ పంపింది మీడియా అయితే (ఫోటో/వీడియో)
        elif message.media:
            description = message.caption if message.caption else "Media attached as proof."
            if message.photo:
                media_id = message.photo.file_id
                media_type = "photo"
            elif message.video:
                media_id = message.video.file_id
                media_type = "video"
            elif message.document:
                media_id = message.document.file_id
                media_type = "document"

        # డేటాబేస్ లో టికెట్ సేవ్ చేయడం
        ticket_data = {
            "ticket_id": ticket_id,
            "user_id": user_id,
            "username": message.from_user.username,
            "description": description,
            "media_id": media_id,
            "media_type": media_type,
            "status": "Pending",
            "resolution": "",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        tickets_db.insert_one(ticket_data)
        users_db.update_one({"user_id": user_id}, {"$set": {"state": None}})

        # యూజర్‌కి సక్సెస్ మెసేజ్ మరియు 24-hours SLA ప్రామిస్
        user_msg = (
            f"{header}✅ <b>Ticket Raised Successfully!</b>\n\n"
            f"🔖 <b>Ticket ID:</b> <code>{ticket_id}</code>\n"
            f"⏱️ <b>Resolution Time:</b> Within 24 Hours\n\n"
            f"Our team has received your request and will look into it immediately. You can check the status using /View_tickets."
        )
        await message.reply_text(user_msg, parse_mode=enums.ParseMode.HTML)

        # 🌟 అడ్మిన్ కి ఆటోమేటిక్ నోటిఫికేషన్ 🌟
        admin_id = getattr(config.Config, "ADMIN_ID", None)
        if admin_id:
            try:
                admin_msg = (
                    f"🚨 <b>NEW TICKET RAISED!</b> 🚨\n\n"
                    f"🔖 <b>Ticket ID:</b> <code>{ticket_id}</code>\n"
                    f"👤 <b>User ID:</b> <code>{user_id}</code> (@{message.from_user.username})\n"
                    f"📝 <b>Issue:</b> {description}\n\n"
                    f"<i>To resolve this, reply with:</i>\n"
                    f"<code>/Resolved {ticket_id} Your solution text here</code>"
                )
                if media_id:
                    await client.send_cached_media(chat_id=int(admin_id), file_id=media_id, caption=admin_msg)
                else:
                    await client.send_message(chat_id=int(admin_id), text=admin_msg, parse_mode=enums.ParseMode.HTML)
            except Exception as e:
                print(f"Failed to notify admin: {e}")
        
        raise StopPropagation # కింది ఫైల్స్ కి వెళ్లకుండా ఆపేస్తుంది

# ==========================================
# 3. VIEW TICKETS COMMAND (User History)
# ==========================================
@Client.on_message(filters.command(["View_tickets", "view_tickets"]) & filters.private)
async def view_tickets_cmd(client, message):
    user_id = message.from_user.id
    header = get_header(user_id)
    
    # యూజర్ కి సంబంధించిన అన్ని టికెట్లు డేటాబేస్ నుండి లాగడం
    user_tickets = list(tickets_db.find({"user_id": user_id}).sort("_id", -1)) # లేటెస్ట్ ముందు వచ్చేలా
    
    if not user_tickets:
        await message.reply_text(f"{header}📝 <b>No Tickets Found!</b>\nYou haven't raised any support tickets yet.", parse_mode=enums.ParseMode.HTML)
        return

    history_text = f"{header}🎫 <b>Your Ticket History</b>\n(Total Tickets: {len(user_tickets)})\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for tk in user_tickets:
        status_icon = "✅" if tk['status'] == "Resolved" else "⏳"
        history_text += f"🔖 <b>Ticket ID:</b> <code>{tk['ticket_id']}</code>\n"
        history_text += f"📅 <b>Date:</b> {tk['date']}\n"
        history_text += f"📝 <b>Description:</b> {tk['description']}\n"
        
        # మీరు అడిగినట్లుగా డిస్క్రిప్షన్ కింద గీత, దాని కింద రిజల్యూషన్
        history_text += "───────────────────\n"
        history_text += f"📌 <b>Status:</b> {status_icon} {tk['status']}\n"
        
        if tk['status'] == "Resolved" and tk.get('resolution'):
            history_text += f"🛠 <b>Resolution:</b> {tk['resolution']}\n"
            
        history_text += "━━━━━━━━━━━━━━━━━━━━━\n\n"

    # టెలిగ్రామ్ మెసేజ్ లిమిట్ దాటితే (చాలా టికెట్లు ఉంటే)
    if len(history_text) > 4000:
        history_text = history_text[:3900] + "...\n(Showing most recent tickets due to length limit)"

    await message.reply_text(history_text, parse_mode=enums.ParseMode.HTML)

# ==========================================
# 4. ADMIN RESOLVED COMMAND (/Resolved TKT-123 message)
# ==========================================
@Client.on_message(filters.command("Resolved") & filters.private)
async def admin_resolve_cmd(client, message):
    if not is_admin(message.from_user.id, message.from_user.username):
        return # అడ్మిన్ కాకపోతే వదిలేస్తుంది

    try:
        # కమాండ్ ఫార్మాట్ చెక్: /Resolved TKT-123456 Issue is fixed
        parts = message.text.split(maxsplit=2) if message.text else message.caption.split(maxsplit=2)
        
        if len(parts) < 2:
            await message.reply_text("⚠️ <b>Format Error:</b> Please use <code>/Resolved TICKET_ID Message</code>", parse_mode=enums.ParseMode.HTML)
            return

        ticket_id = parts[1]
        resolution_msg = parts[2] if len(parts) > 2 else "Issue has been successfully resolved by Admin."
        
        # డేటాబేస్ లో ఆ టికెట్ ఉందో లేదో వెతకడం
        ticket = tickets_db.find_one({"ticket_id": ticket_id})
        if not ticket:
            await message.reply_text(f"❌ <b>Ticket not found!</b> Double-check the ID: {ticket_id}", parse_mode=enums.ParseMode.HTML)
            return

        if ticket['status'] == "Resolved":
            await message.reply_text("⚠️ This ticket is already resolved.")
            return

        # డేటాబేస్ లో స్టేటస్ మరియు రిజల్యూషన్ అప్‌డేట్ చేయడం
        tickets_db.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"status": "Resolved", "resolution": resolution_msg, "resolved_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}}
        )

        user_id = ticket['user_id']
        header = get_header(user_id)

        # 🌟 యూజర్‌కి రిజల్యూషన్ మెసేజ్ పంపడం (మీడియా ఉంటే మీడియాతో సహా) 🌟
        user_notification = (
            f"{header}🔔 <b>Ticket Resolved!</b> 🔔\n\n"
            f"🔖 <b>Ticket ID:</b> <code>{ticket_id}</code>\n"
            f"🛠 <b>Resolution from Admin:</b>\n{resolution_msg}\n\n"
            f"🙏 Thank you for your patience. If you face any other issues, feel free to use /raise_ticket again."
        )

        try:
            if message.media:
                await message.copy(chat_id=user_id, caption=user_notification, parse_mode=enums.ParseMode.HTML)
            else:
                await client.send_message(chat_id=user_id, text=user_notification, parse_mode=enums.ParseMode.HTML)
            
            await message.reply_text(f"✅ Ticket <b>{ticket_id}</b> marked as Resolved and user notified!", parse_mode=enums.ParseMode.HTML)
        except Exception as e:
            await message.reply_text(f"⚠️ Ticket updated in DB, but failed to notify user. They might have blocked the bot.\nError: {e}")

    except Exception as e:
        await message.reply_text(f"❌ Error processing command: {e}")
