from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from catalogue.application.category_service import CategoryService
from catalogue.dependencies.context import admin_context
from catalogue.infrastructure.category_repository import CategoryRepository
from catalogue.schemas.category import Category, CategoryCreate, CategoryUpdate

router = APIRouter(prefix="/api/v1/categories")
def service(request: Request, _context=Depends(admin_context)) -> CategoryService:
    return CategoryService(CategoryRepository(request.state.tenant_settings))

@router.get("", response_model=list[Category])
def list_categories(_context=Depends(admin_context), categories: CategoryService = Depends(service)): return categories.list_categories()

@router.post("", response_model=Category, status_code=201)
def create_category(payload: CategoryCreate, _context=Depends(admin_context), categories: CategoryService = Depends(service)):
    try: return categories.create_category(payload)
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc

@router.patch("/{category_id}", response_model=Category)
def update_category(category_id: UUID, payload: CategoryUpdate, _context=Depends(admin_context), categories: CategoryService = Depends(service)):
    try: return categories.update_category(category_id, payload)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: UUID, _context=Depends(admin_context), categories: CategoryService = Depends(service)):
    try: categories.delete_category(category_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
