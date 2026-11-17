from uuid import UUID
from pydantic import BaseModel, Field

class ImageCreate(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    alt_text: str | None = Field(default=None, max_length=255)
    sort_order: int = Field(default=0, ge=0)

class Image(ImageCreate):
    id: UUID

class VariantCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    price_cents: int = Field(ge=0)
    attributes: dict[str, str] = Field(default_factory=dict)

class Variant(VariantCreate):
    id: UUID
    product_id: UUID

class PriceRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    price_cents: int = Field(ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    active: bool = True

class PriceRule(PriceRuleCreate):
    id: UUID
