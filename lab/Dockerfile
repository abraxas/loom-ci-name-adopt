FROM python:3.13-slim

WORKDIR /app

COPY src-v1.10.3/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src-v1.10.3/backend/app/ ./app/
COPY src-v1.10.3/backend/etc/ ./etc/

COPY lab_patch.py sitecustomize.py /usr/local/lib/python3.13/site-packages/
COPY poc.py /lab/poc.py

RUN mkdir -p /lab/capture

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AWS_EC2_METADATA_DISABLED=true \
    AWS_DEFAULT_REGION=us-east-1 \
    AWS_REGION=us-east-1 \
    AWS_ACCESS_KEY_ID=lab \
    AWS_SECRET_ACCESS_KEY=lab \
    LOOM_LITELLM_PRICING_URL=

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
