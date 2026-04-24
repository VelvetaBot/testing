FROM python:3.11-slim-bookworm

# సిస్టమ్ డిపెండెన్సీలను ఇన్‌స్టాల్ చేయడం
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ఫైల్స్‌ని కాపీ చేయడం
COPY . .

# పైథాన్ లైబ్రరీలను ఇన్‌స్టాల్ చేయడం
RUN pip install --no-cache-dir -r requirements.txt

# బాట్‌ను స్టార్ట్ చేయడం
CMD ["python3", "main.py"]
