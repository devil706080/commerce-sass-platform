FROM ghcr.io/astral-sh/uv:0.13.8 AS uv
FROM python:3.14.8-slim
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --no-install-project
COPY src ./src
COPY migrations ./migrations
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev \
    && useradd --system --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser
EXPOSE 8040
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD /app/.venv/bin/python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8040/health', timeout=3)" || exit 1
CMD ["/app/.venv/bin/uvicorn", "inventory.main:app", "--host", "0.0.0.0", "--port", "8040"]
