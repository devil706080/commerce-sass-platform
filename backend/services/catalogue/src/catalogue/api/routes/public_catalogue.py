from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from catalogue.config.settings import load_settings
from catalogue.infrastructure.product_repository import ProductRepository
from catalogue.schemas.product import Product

router = APIRouter(prefix="/api/v1/store")

@router.get("/products", response_model=list[Product])
def public_products(search: str | None = None, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    return ProductRepository(load_settings()).list(search, True, limit, offset)

@router.get("/products/{product_id}", response_model=Product)
def public_product(product_id: UUID):
    try:
        product = ProductRepository(load_settings()).get(product_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Product not found") from exc
    if not product.published:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
