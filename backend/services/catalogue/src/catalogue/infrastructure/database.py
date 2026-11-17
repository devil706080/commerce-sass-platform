import psycopg
from fastapi import HTTPException
from catalogue.config.settings import Settings

def quote_identifier(value: str) -> str:
    if not value.replace("_", "").isalnum():
        raise ValueError("invalid SQL identifier")
    return f'"{value}"'

def connect(settings: Settings):
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="Catalogue database is not configured")
    return psycopg.connect(settings.database_url)
