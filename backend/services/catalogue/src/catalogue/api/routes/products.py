from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from catalogue.application.product_service import ProductService
from catalogue.dependencies.context import admin_context
from catalogue.infrastructure.product_repository import ProductRepository
from catalogue.schemas.category import Category
from catalogue.schemas.product import Product, ProductCreate, ProductUpdate

router = APIRouter(prefix="/api/v1/products")

def service(request: Request, _context=Depends(admin_context)) -> ProductService:
    return ProductService(ProductRepository(request.state.tenant_settings))

@router.get("", response_model=list[Product])
def list_products(search: str | None = None, published: bool | None = None, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), _context=Depends(admin_context), products: ProductService = Depends(service)):
    return products.list_products(search, published, limit, offset)

@router.get("/{product_id}", response_model=Product)
def get_product(product_id: UUID, _context=Depends(admin_context), products: ProductService = Depends(service)):
    try: return products.get_product(product_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.post("", response_model=Product, status_code=201)
def create_product(payload: ProductCreate, _context=Depends(admin_context), products: ProductService = Depends(service)):
    try: return products.create_product(payload)
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc

@router.patch("/{product_id}", response_model=Product)
def update_product(product_id: UUID, payload: ProductUpdate, _context=Depends(admin_context), products: ProductService = Depends(service)):
    try: return products.update_product(product_id, payload)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: UUID, _context=Depends(admin_context), products: ProductService = Depends(service)):
    try: products.delete_product(product_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.get("/{product_id}/categories", response_model=list[Category])
def product_categories(product_id: UUID, _context=Depends(admin_context), products: ProductService = Depends(service)):
    return [Category(id=row[0], name=row[1], slug=row[2], description=row[3]) for row in products.product_categories(product_id)]

@router.put("/{product_id}/categories/{category_id}", status_code=204)
def attach_category(product_id: UUID, category_id: UUID, _context=Depends(admin_context), products: ProductService = Depends(service)):
    try: products.attach_category(product_id, category_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.delete("/{product_id}/categories/{category_id}", status_code=204)
def detach_category(product_id: UUID, category_id: UUID, _context=Depends(admin_context), products: ProductService = Depends(service)):
    try: products.detach_category(product_id, category_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
