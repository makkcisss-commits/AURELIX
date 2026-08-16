FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AURELIX_HOST=0.0.0.0 \
    AURELIX_PORT=8000

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml ./
COPY src ./src
COPY web ./web

RUN python -m pip install --no-cache-dir . \
    && addgroup --system --gid 10001 aurelix \
    && adduser --system --uid 10001 --ingroup aurelix --home /nonexistent --no-create-home aurelix \
    && mkdir -p /app/data \
    && chown -R aurelix:aurelix /app

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["aurelix-server"]
