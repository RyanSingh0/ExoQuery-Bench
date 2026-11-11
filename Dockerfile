FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src EQB_DATA_DIR=/app/state
WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir --require-hashes -r requirements.lock \
    && useradd --uid 10001 --create-home researcher \
    && mkdir -p /app/state && chown researcher:researcher /app/state
COPY src ./src
USER researcher
EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/health',timeout=3)"
CMD ["python", "-m", "uvicorn", "eqb.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8765"]
