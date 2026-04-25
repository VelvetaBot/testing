import os
import logging

# రైల్వే (Railway) కన్సోల్ లాగ్స్ లో మనకు మాత్రమే కనిపించడానికి
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# 🍪 మీ 5 కుకీస్ ఇక్కడ పేస్ట్ చేయండి 🍪
# (ఆ మూడు కొటేషన్స్ """ మధ్యలో 'paste_here' ని తీసేసి మీ కుకీస్ కోడ్ పేస్ట్ చేయండి)
# ==========================================

COOKIE_1 = """paste_here"""

COOKIE_2 = """paste_here"""

COOKIE_3 = """paste_here"""

COOKIE_4 = """paste_here"""

COOKIE_5 = """paste_here"""

# అన్ని కుకీస్‌ని ఒక లిస్ట్‌లో పెడుతున్నాం
AVAILABLE_COOKIES = [COOKIE_1, COOKIE_2, COOKIE_3, COOKIE_4, COOKIE_5]

def get_working_cookie_file(attempt_index):
    """
    ఇది రొటేషన్ లాజిక్. ఇంజిన్ అడిగినప్పుడు ఆ నెంబర్ బట్టి కుకీని ఒకే ఒక్క 'cookies.txt' లో రాసి ఇస్తుంది.
    యూజర్‌కి ఈ విషయం అస్సలు తెలియదు!
    """
    if attempt_index < len(AVAILABLE_COOKIES):
        cookie_data = AVAILABLE_COOKIES[attempt_index].strip()
        
        # కుకీ ఖాళీగా ఉంటే (లేదా paste_here అలానే ఉంటే) దాన్ని స్కిప్ చేయడానికి
        if not cookie_data or cookie_data == "paste_here":
            return None
            
        # ప్రతిసారీ ఒకే ఒక్క cookies.txt ఫైల్ క్రియేట్/ఓవర్‌రైట్ చేస్తుంది (గిట్‌హబ్ క్లీన్ గా ఉంటుంది)
        with open("cookies.txt", "w", encoding="utf-8") as f:
            f.write(cookie_data)
            
        # ఇది కేవలం మనకు రైల్వే లాగ్స్ లో మాత్రమే కనిపిస్తుంది
        logger.info(f"🔄 Switching to Cookie File Attempt: {attempt_index + 1}")
        return "cookies.txt"
        
    # 5 కుకీస్ కూడా ఫెయిల్ అయితే
    return None
