import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pyrogram import Client
import config

# లాగ్స్ సెటప్ (ఏదైనా ఎర్రర్ వస్తే టెర్మినల్ లో ఈజీగా చూసుకోవడానికి)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Railway/Render కిల్ చేయకుండా ఉండటానికి డమ్మీ వెబ్ సర్వర్ ---
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Velveta Bot is Alive and Running Perfectly!")

def keep_alive():
    try:
        port = int(os.environ.get("PORT", 8080))
        server = HTTPServer(("0.0.0.0", port), DummyServer)
        logger.info(f"🌐 Dummy Web Server started on port {port} to keep Railway happy.")
        server.serve_forever()
    except Exception as e:
        logger.error(f"⚠️ Dummy Server Error: {e}")

# బ్యాక్ గ్రౌండ్ లో ఆ డమ్మీ సర్వర్ ని స్టార్ట్ చేయడం
threading.Thread(target=keep_alive, daemon=True).start()
# ---------------------------------------------------------------

# Pyrogram క్లయింట్ సెటప్ 
app = Client(
    "VelvetaYTDownloaderBot",
    api_id=config.Config.API_ID,
    api_hash=config.Config.API_HASH,
    bot_token=config.Config.BOT_TOKEN,
    plugins=dict(root="plugins") 
)

if __name__ == "__main__":
    logger.info("🚀 Velveta YouTube Downloader Bot is starting...")
    try:
        app.run()
        logger.info("✅ Bot stopped gracefully.")
    except Exception as e:
        logger.error(f"❌ Bot stopped due to an error: {e}")
