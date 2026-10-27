FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

RUN useradd --system marcie
USER marcie

# Configure with MARCIE_DB, MARCIE_API, MARCIE_API_KEY and DISCORD_BOT_TOKEN
CMD ["python", "marcie.py"]
