import re

def repair_youtube_link(text: str):
    """
    యూజర్ పంపిన టెక్స్ట్‌లో స్పేస్‌లు ఉన్నా, ముందు/వెనుక వేరే అక్షరాలు ఉన్నా 
    వాటిని తొలగించి కేవలం YouTube లింక్ ని మాత్రమే బయటకు తీస్తుంది.
    """
    if not text:
        return None

    # అన్ని రకాల స్పేస్ లను తొలగించడం
    cleaned_text = text.replace(" ", "").replace("\n", "")

    # కచ్చితమైన యూట్యూబ్ లింక్ ప్యాటర్న్ ని వెతికి పట్టుకోవడం
    yt_pattern = re.compile(
        r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})"
    )
    
    match = yt_pattern.search(cleaned_text)
    
    if match:
        # దొరికిన అసలైన లింక్ ని రిటర్న్ చేస్తుంది
        return match.group(0)
    
    return None
