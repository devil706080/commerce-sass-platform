FROM ghcr.io/astral-sh/uv:0.13.8 AS uv
FROM python:3.14.8-slim
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv sync --locked --no-dev --no-cache 2>/dev/null || uv sync --no-dev --no-cache
RUN useradd --system --uid 10001 appuser
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8010
CMD ["/app/.venv/bin/uvicorn", "catalogue.main:app", "--host", "0.0.0.0", "--port", "8010"]
