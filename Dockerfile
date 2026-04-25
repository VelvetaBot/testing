FROM python:3.11-slim-bookworm

WORKDIR /app

# ఇక్కడ ffmpeg, curl తో పాటు git ని యాడ్ చేశాను
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
