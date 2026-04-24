import os
import asyncio
from pyrogram import Client, filters, enums
import config

# స్ట్రింగ్ సెషన్ తో యూజర్ అకౌంట్ క్లయింట్ (Userbot)
user_bot = Client(
    "velveta_userbot",
    api_id=config.Config.API_ID,
    api_hash=config.Config.API_HASH,
    session_string=config.Config.STRING_SESSION
)

# ఇక్కడ మీరు ఇచ్చే 5 బాట్స్ పేర్లు వస్తాయి (ఉదాహరణకి: ["@bot1", "@bot2", ...])
EXTERNAL_BOTS = [
    # దయచేసి ఆ 5 బాట్స్ పేర్లు ఇవ్వండి
]

# మన బాట్ యొక్క లోగో/వాల్‌పేపర్ (Thumb) పాత్
DEFAULT_LOGO_PATH = "logo.jpg" 

async def fetch_video_via_fallback(main_client, chat_id, message_id, youtube_link, title):
    """
    అసలు ఇంజిన్ ఫెయిల్ అయితే, స్ట్రింగ్ సెషన్ ద్వారా 5 ఎక్స్‌టర్నల్ బాట్స్‌లో 
    ఒకదాని తర్వాత ఒకటి ట్రై చేసి వీడియో తెప్పించి మన లోగోతో పంపే ఫంక్షన్.
    """
    try:
        await main_client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"🔄 <b>Connecting to Backup Servers...</b>\n\n🎬 {title}\n⏳ Please wait, processing securely.",
            parse_mode=enums.ParseMode.HTML
        )

        await user_bot.start()
        
        video_message = None
        
        # మీరు ఇచ్చిన 5 బాట్స్ ని ఒకదాని తర్వాత ఒకటి ట్రై చేసే బ్రహ్మాస్త్రం లాజిక్
        for bot_username in EXTERNAL_BOTS:
            try:
                await user_bot.send_message(bot_username, youtube_link)
                
                # ఆ బాట్ నుండి రిప్లై కోసం 30 సెకన్లు వెయిట్ చేయడం (15 * 2 సెకన్లు)
                for _ in range(15):
                    await asyncio.sleep(2)
                    async for msg in user_bot.get_chat_history(bot_username, limit=3):
                        if msg.video or msg.document:
                            video_message = msg
                            break
                    if video_message:
                        break
                
                # ఒకవేళ ఈ బాట్ నుండి వీడియో దొరికేస్తే, మిగతా బాట్స్ కి వెళ్లకుండా ఆపేస్తాం
                if video_message:
                    break 
                    
            except Exception as e:
                # ఈ బాట్ పని చేయకపోతే, సైలెంట్ గా తర్వాతి బాట్ కి వెళ్తుంది
                continue 

        # 5 బాట్స్ కూడా పని చేయకపోతే (ఇలా జరగడం చాలా రేర్)
        if not video_message:
            await main_client.edit_message_text(chat_id, message_id, "❌ All Backup Servers are busy. Please try again later.")
            await user_bot.stop()
            return

        # వీడియో దొరికితే డౌన్‌లోడ్ చేయడం
        await main_client.edit_message_text(chat_id, message_id, "📥 <b>Downloading from Backup Server...</b>\n⏳ Almost done!")
        downloaded_file = await user_bot.download_media(video_message)
        
        await user_bot.stop()

        # మన లోగో మరియు క్యాప్షన్ తో యూజర్ కి పంపడం
        await main_client.edit_message_text(chat_id, message_id, "📤 <b>Uploading to you...</b>")
        
        caption_text = (
            f"🎬 <b>{title}</b>\n\n"
            f"🙏 Thank you for using @{getattr(config, 'BOT_USERNAME', 'VelvetaYTDownloaderBot')}"
        )
        
        thumb_path = DEFAULT_LOGO_PATH if os.path.exists(DEFAULT_LOGO_PATH) else None

        await main_client.send_video(
            chat_id=chat_id,
            video=downloaded_file,
            caption=caption_text,
            thumb=thumb_path,
            parse_mode=enums.ParseMode.HTML
        )
        
        # పంపిన తర్వాత సర్వర్ లోని ఫైల్ డిలీట్ చేయడం (స్టోరేజ్ సేవ్ చేయడానికి)
        os.remove(downloaded_file)
        
        await main_client.delete_messages(chat_id, message_id)

    except Exception as e:
        await main_client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"❌ Error in Backup Server: {str(e)}"
        )
        if user_bot.is_connected:
            await user_bot.stop()
