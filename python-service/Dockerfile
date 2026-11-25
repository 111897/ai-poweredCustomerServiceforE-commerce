FROM python:3.13-slim

WORKDIR /app

RUN groupadd -r app && useradd -r -g app app

COPY requirements.txt requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

COPY --chown=app:app app ./app
COPY --chown=app:app scripts ./scripts

RUN mkdir -p /app/logs /app/data && chown -R app:app /app/logs /app/data

ENV PYTHONPATH=/app
USER app
EXPOSE 8000

# 知识库数据通过卷挂载到 /app/data（见 docker-compose.yml）
HEALTHCHECK --interval=15s --timeout=5s --retries=10 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
