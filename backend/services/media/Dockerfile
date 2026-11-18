FROM ghcr.io/astral-sh/uv:0.13.8 AS uv
FROM python:3.14.8-slim
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv sync --no-dev --no-cache
RUN useradd --system --uid 10002 appuser && mkdir -p /var/lib/commerce-media && chown -R appuser:appuser /app /var/lib/commerce-media
USER appuser
EXPOSE 8020
CMD ["/app/.venv/bin/uvicorn", "media.main:app", "--host", "0.0.0.0", "--port", "8020"]
