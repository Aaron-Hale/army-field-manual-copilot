FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AWS_REGION=us-east-1 \
    AFMC_TOP_K_MAX=5 \
    AFMC_MAX_OUTPUT_TOKENS=400 \
    AFMC_MAX_CONTEXT_TOKENS=1800 \
    AFMC_MIN_RETRIEVAL_SCORE=0.45 \
    AFMC_RATE_LIMIT_RPM=30

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
