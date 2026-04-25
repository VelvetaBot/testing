from pymongo import MongoClient
import config
import logging

# లాగ్స్ కోసం సెటప్
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # MongoDB కి కనెక్ట్ చేయడం (మీ Azure Cosmos DB లింక్ ద్వారా)
    client = MongoClient(config.Config.MONGO_URL)

    # డేటాబేస్ పేరు (VelvetaYTDownloader)
    db = client["VelvetaYTDownloader"]

    # యూజర్లు డేటా సేవ్ చేసే కలెక్షన్
    users_db = db["users"]
    
    # 🌟 ఇక్కడే మార్పు చేశాను (లైన్ ముందుకు జరగకుండా, మరియు "db" పేరుతో) 🌟
    logs_collection = db["logs_collection"]

    logger.info("✅ Database connected successfully!")
except Exception as e:
    logger.error(f"❌ Database connection failed: {e}")
