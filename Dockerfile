FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[anthropic,azure]"

COPY data ./data
COPY eval ./eval

RUN useradd --create-home appuser && mkdir -p /app/var && chown appuser /app/var
USER appuser
VOLUME ["/app/var"]

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
CMD ["uvicorn", "ai_act_assistant.api:app", "--host", "0.0.0.0", "--port", "8000"]
