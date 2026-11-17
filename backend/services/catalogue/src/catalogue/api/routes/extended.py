from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from catalogue.application.extended_service import ExtendedService
from catalogue.config.settings import load_settings
from catalogue.dependencies.context import admin_context
from catalogue.infrastructure.extended_repository import ExtendedRepository
from catalogue.schemas.extended import Image, ImageCreate, Variant, VariantCreate, PriceRule, PriceRuleCreate

router=APIRouter(prefix="/api/v1/products")
def service() -> ExtendedService: return ExtendedService(ExtendedRepository(load_settings()))

@router.get("/{product_id}/images", response_model=list[Image])
def images(product_id: UUID, _context=Depends(admin_context), catalogue: ExtendedService=Depends(service)): return catalogue.list_images(product_id)

@router.post("/{product_id}/images", response_model=Image, status_code=201)
def add_image(product_id: UUID, payload: ImageCreate, _context=Depends(admin_context), catalogue: ExtendedService=Depends(service)):
    try: return catalogue.add_image(product_id, payload)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.get("/{product_id}/variants", response_model=list[Variant])
def variants(product_id: UUID, _context=Depends(admin_context), catalogue: ExtendedService=Depends(service)): return catalogue.list_variants(product_id)

@router.post("/{product_id}/variants", response_model=Variant, status_code=201)
def add_variant(product_id: UUID, payload: VariantCreate, _context=Depends(admin_context), catalogue: ExtendedService=Depends(service)):
    try: return catalogue.add_variant(product_id, payload)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc

@router.get("/{product_id}/prices", response_model=list[PriceRule])
def prices(product_id: UUID, _context=Depends(admin_context), catalogue: ExtendedService=Depends(service)): return catalogue.list_prices(product_id)

@router.post("/{product_id}/prices", response_model=PriceRule, status_code=201)
def add_price(product_id: UUID, payload: PriceRuleCreate, _context=Depends(admin_context), catalogue: ExtendedService=Depends(service)):
    try: return catalogue.add_price(product_id, payload)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from None
