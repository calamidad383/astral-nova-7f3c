FROM python:3.12-slim

WORKDIR /app
COPY bot/requirements.txt bot/requirements.txt
COPY ia/ ia/
RUN pip install --no-cache-dir -r bot/requirements.txt

COPY bot/ bot/
CMD ["python", "-m", "bot.main"]
