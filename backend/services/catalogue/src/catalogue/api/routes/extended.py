from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from catalogue.application.extended_service import ExtendedService
from catalogue.config.settings import load_settings
from catalogue.dependencies.context import admin_context
from catalogue.infrastructure.extended_repository import ExtendedRepository
from catalogue.schemas.extended import Image, ImageCreate, ImageUpdate, Variant, VariantCreate, VariantUpdate, PriceRule, PriceRuleCreate, PriceRuleUpdate

router=APIRouter(prefix="/api/v1/products")
def service() -> ExtendedService: return ExtendedService(ExtendedRepository(load_settings()))

@router.get("/{product_id}/images", response_model=list[Image])
def images(product_id: UUID, _context=Depends(admin_context), catalogue: ExtendedService=Depends(service)):
    try: return catalogue.list_images(product_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.post("/{product_id}/images", response_model=Image, status_code=201)
def add_image(product_id: UUID, payload: ImageCreate, _context=Depends(admin_context), catalogue: ExtendedService=Depends(service)):
    try: return catalogue.add_image(product_id, payload)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.patch("/{product_id}/images/{image_id}", response_model=Image)
def update_image(product_id: UUID, image_id: UUID, payload: ImageUpdate, _context=Depends(admin_context), catalogue: ExtendedService=Depends(service)):
    try: return catalogue.update_image(product_id, image_id, payload)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.delete("/{product_id}/images/{image_id}", status_code=204)
def delete_image(product_id: UUID, image_id: UUID, _context=Depends(admin_context), catalogue: ExtendedService=Depends(service)):
    try: catalogue.delete_image(product_id, image_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.get("/{product_id}/variants", response_model=list[Variant])
def variants(product_id: UUID, _context=Depends(admin_context), catalogue: ExtendedService=Depends(service)):
    try: return catalogue.list_variants(product_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.post("/{product_id}/variants", response_model=Variant, status_code=201)
def add_variant(product_id: UUID, payload: VariantCreate, _context=Depends(admin_context), catalogue: ExtendedService=Depends(service)):
    try: return catalogue.add_variant(product_id, payload)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc

@router.patch("/{product_id}/variants/{variant_id}", response_model=Variant)
def update_variant(product_id: UUID, variant_id: UUID, payload: VariantUpdate, _context=Depends(admin_context), catalogue: ExtendedService=Depends(service)):
    try: return catalogue.update_variant(product_id, variant_id, payload)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc

@router.delete("/{product_id}/variants/{variant_id}", status_code=204)
def delete_variant(product_id: UUID, variant_id: UUID, _context=Depends(admin_context), catalogue: ExtendedService=Depends(service)):
    try: catalogue.delete_variant(product_id, variant_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.get("/{product_id}/prices", response_model=list[PriceRule])
def prices(product_id: UUID, _context=Depends(admin_context), catalogue: ExtendedService=Depends(service)):
    try: return catalogue.list_prices(product_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.post("/{product_id}/prices", response_model=PriceRule, status_code=201)
def add_price(product_id: UUID, payload: PriceRuleCreate, _context=Depends(admin_context), catalogue: ExtendedService=Depends(service)):
    try: return catalogue.add_price(product_id, payload)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from None

@router.patch("/{product_id}/prices/{price_id}", response_model=PriceRule)
def update_price(product_id: UUID, price_id: UUID, payload: PriceRuleUpdate, _context=Depends(admin_context), catalogue: ExtendedService=Depends(service)):
    try: return catalogue.update_price(product_id, price_id, payload)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.delete("/{product_id}/prices/{price_id}", status_code=204)
def delete_price(product_id: UUID, price_id: UUID, _context=Depends(admin_context), catalogue: ExtendedService=Depends(service)):
    try: catalogue.delete_price(product_id, price_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
