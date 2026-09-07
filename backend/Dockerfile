FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for some python packages and OCR
RUN apt-get update \
    && apt-get install -y ca-certificates gcc libpq-dev tesseract-ocr libtesseract-dev tesseract-ocr-por tesseract-ocr-eng \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host pypi.python.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt

# Copiar app code será mapeado por volume no compose dev,
# mas para prod copiaríamos tudo aqui
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
