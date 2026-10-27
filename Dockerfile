FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

RUN useradd --system marcie && mkdir /data && chown marcie /data
USER marcie

# Guild prefixes are saved to /data/marcie.db, mount a volume there to keep them
ENV MARCIE_DATA_DIR=/data
VOLUME /data

# Configure with MARCIE_API, MARCIE_API_KEY and DISCORD_BOT_TOKEN
CMD ["python", "marcie.py"]
