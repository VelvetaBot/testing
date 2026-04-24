import os
from pyrogram import Client, filters, enums

@Client.on_message(filters.command("setcookies") & filters.private)
async def set_cookies_command(client, message):
    text = (
        "🍪 <b>Cookies Updater</b>\n\n"
        "Please upload your fresh <code>cookies.txt</code> file here as a document.\n"
        "The bot will automatically replace the old cookies and start using the new ones instantly without restarting!"
    )
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.document & filters.private)
async def receive_cookies_file(client, message):
    file_name = message.document.file_name
    
    # యూజర్ పంపిన ఫైల్ పేరు cookies.txt అయితేనే తీసుకుంటుంది
    if file_name and file_name.lower() == "cookies.txt":
        msg = await message.reply_text("📥 <b>Downloading and applying new cookies...</b>", parse_mode=enums.ParseMode.HTML)
        try:
            # పాత ఫైల్ ఉంటే దాన్ని తొలగించి, కొత్త ఫైల్ ని మెయిన్ ఫోల్డర్ లో సేవ్ చేస్తుంది
            file_path = os.path.join(os.getcwd(), "cookies.txt")
            
            if os.path.exists(file_path):
                os.remove(file_path)
                
            await client.download_media(message, file_name=file_path)
            
            await msg.edit_text("✅ <b>Cookies Updated Successfully!</b> 🍪\n\nYour bot is ready to download age-restricted and high-quality videos again. Just send a YouTube link!", parse_mode=enums.ParseMode.HTML)
        except Exception as e:
            await msg.edit_text(f"❌ <b>Failed to update cookies:</b> {e}", parse_mode=enums.ParseMode.HTML)
