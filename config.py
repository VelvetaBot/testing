import os

class Config:
    # Telegram Bot & Channel వివరాలు
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "8622929989:AAH3E1Fjxi5VrJLVM02OOsSwHiSJUpzynnE")
    API_ID = int(os.environ.get("API_ID", 11253846))
    API_HASH = os.environ.get("API_HASH", "8db4eb50f557faa9a5756e64fb74a51a")
    
    # Google Gemini
    GEMINI_API_KEY = "AIzaSyB3KfZfHcUlN9n4s6teCk0CqO5WkCFOIaU" 
    
    # YouTube API Key
    YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "AIzaSyBJhg5O3FOngBJC2TuUZUQg1U82S61bZFo")
    
    UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL", "Velvetabots")
    SUPPORT_ID = os.environ.get("SUPPORT_ID", "Velvetasupport")
    ADMIN_ID = os.environ.get("ADMIN_ID", "VelvetaBotmaker")

    # Azure Cosmos DB కనెక్షన్ లింక్
    MONGO_URL = os.environ.get("MONGO_URL", "mongodb://velveta-yt-downloader:0uabvoabpcANzKkbzoruevWGrNupjgxflU2WCheo6HqsGfGj90Hid5RuNEAGYGlT9QcI1aejC6fkACDbyyellw==@velveta-yt-downloader.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@velveta-yt-downloader@")

    # NOWPayments API Keys (For Automatic Crypto Payments)
    NOWPAYMENTS_API_KEY = os.environ.get("NOWPAYMENTS_API_KEY", "3VQ2PPP-6444DG8-Q0XHS91-72Z6PRR")
    NOWPAYMENTS_IPN_KEY = os.environ.get("NOWPAYMENTS_IPN_KEY", "KVeWs4gP39/MPhFOfqwdryhrogi4scpb")

    # Cashfree payment gateway system
    CASHFREE_APP_ID = os.environ.get("CASHFREE_APP_ID", "TEST10158680198c538bdf2027eb9add08685101")
    CASHFREE_SECRET_KEY = os.environ.get("CASHFREE_SECRET_KEY", "cfsk_ma_test_d47fdd9c1575cf4074e3f6f8c25995e3_f61130d1")

    # Payment & Ads వివరాలు
    CRYPTO_WALLET = os.environ.get("CRYPTO_WALLET", "TAwfCAk2GSGGn5m1WvnqD72bhQ4tr5Y7Wn")
    PAYTM_MID = os.environ.get("PAYTM_MID", "UaNEJZ50767121615064")
    PAYTM_KEY = os.environ.get("PAYTM_KEY", "%v8CJI0B@_Bw87L8")

    # Backup Downloader కోసం Pyrogram String Session
    STRING_SESSION = os.environ.get("STRING_SESSION", "BQCruFYApIp-d7jiQ8JS2Ku3askdbq-Wpxl42xvctL7sVUU_bz5qY5eblaELC9P_v5m3leQHoslqu3lI_8qnvGWJGXiwMzv0wFpZ2Zqo-aJU3rog0M7FdbU6uxmbw1IV0U-5DgOMkaIV8upuMBxgbo7G25zZ6ECBTSicb9VZ9roq5L7LwKlzWAe1AfkBXut7jaDHUfX7cxg8pAeRWCdNPgMiXiNG0OKmtXzEuoC5G2kO0ckiMEJ8rlhNDZW31bEBz_KRyODW82N7l7YGUPfPEUPPhcvQ_7tn_kvUHV6NRmYJiWle8iXwgAU4QtILPRWvplBRtwAo5DV5v78aHMBs7WLgx1yOeAAAAAH-HrhUAA")

    # యాడ్స్ కోసం 10 కంపెనీల API Keys
    SHORTENERS = {
        "gplinks.com": os.environ.get("GPLINKS_TOKEN", "6cfb65c98aac02096414e7df33c7d067bb850c5f"),
        "xui.io": os.environ.get("XUI_TOKEN", "c7f638092aef394f260ebbb9846a4dc2f98f65cc"),
        "shrinkme.io": os.environ.get("SHRINKME_TOKEN", "3c1a01f8050cd2d281b836aa1a2464bdf4b280e9"),
        "droplink.co": os.environ.get("DROPLINK_TOKEN", "ff72b15dc3b6f4cfbddd00dd63ca8f9669a39b91"),
        "cutwin.com": os.environ.get("CUTWIN_TOKEN", "7bbcbe4c505bc85564bf3d2bad62e3b4408de516"),
        "uii.io": os.environ.get("UII_TOKEN", "e96c580838fd512e84cb64fe2606ce7484829eca"),
        "shrinkearn.com": os.environ.get("SHRINKEARN_TOKEN", "ab54de394b711d8097c9b4968d2e2489a478b824"),
        "short.pe": os.environ.get("SHORTPE_TOKEN", "10cd83baa7438935fd74033b92c8eb1ad0d2e505"),
        "shrink.pe": os.environ.get("SHRINKPE_TOKEN", "285832fc86a8b6acead3e9cf7c2cc954f9726651"),
        "linkjust.com": os.environ.get("LINKJUST_TOKEN", "4d8b73c722e7826f6dc0f8d1f84b765422bf9e3e")
    }
