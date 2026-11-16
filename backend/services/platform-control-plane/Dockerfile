FROM python:3.14.8-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --locked --no-dev --no-cache && useradd --system --uid 10001 appuser
COPY alembic.ini ./
COPY migrations ./migrations
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1
CMD ["uvicorn", "platform_control_plane.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
