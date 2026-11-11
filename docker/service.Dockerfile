FROM python:3.12-slim

ARG SERVICE
RUN test -n "$SERVICE" || (echo "Укажите --build-arg SERVICE=<users|chats|messages|presence|gif|gateway>" && exit 1)

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY shared ./shared

WORKDIR /app/${SERVICE}
COPY ${SERVICE}/requirements.txt ./
RUN pip install -r requirements.txt

COPY ${SERVICE}/app ./app

RUN groupadd --system kokogram \
    && useradd --system --gid kokogram --no-create-home --shell /usr/sbin/nologin kokogram
USER kokogram

EXPOSE 8000

HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=10 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
