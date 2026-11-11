FROM python:3.12-slim

WORKDIR /app
COPY api/requirements.txt api/requirements.txt
COPY ia/ ia/
COPY bot/__init__.py bot/__init__.py
COPY bot/constructor.py bot/constructor.py
COPY bot/db.py bot/db.py
RUN pip install --no-cache-dir -r api/requirements.txt

COPY api/ api/
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
