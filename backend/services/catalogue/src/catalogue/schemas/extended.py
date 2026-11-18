from uuid import UUID
from pydantic import BaseModel, Field
from pydantic import field_validator
from urllib.parse import urlsplit

class ImageCreate(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    alt_text: str | None = Field(default=None, max_length=255)
    sort_order: int = Field(default=0, ge=0)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("Image URL must be an absolute http or https URL")
        return value

    @field_validator("alt_text")
    @classmethod
    def normalize_alt_text(cls, value: str | None) -> str | None:
        return value.strip() if value else None

class Image(ImageCreate):
    id: UUID

class ImageUpdate(BaseModel):
    url: str | None = Field(default=None, min_length=1, max_length=2048)
    alt_text: str | None = Field(default=None, max_length=255)
    sort_order: int | None = Field(default=None, ge=0)

    _validate_url = field_validator("url")(ImageCreate.validate_url)
    _normalize_alt_text = field_validator("alt_text")(ImageCreate.normalize_alt_text)

class VariantCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    price_cents: int = Field(ge=0)
    attributes: dict[str, str] = Field(default_factory=dict)

class Variant(VariantCreate):
    id: UUID
    product_id: UUID

class VariantUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=100)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    price_cents: int | None = Field(default=None, ge=0)
    attributes: dict[str, str] | None = None

class PriceRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    price_cents: int = Field(ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    active: bool = True

class PriceRule(PriceRuleCreate):
    id: UUID

class PriceRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    price_cents: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    active: bool | None = None
