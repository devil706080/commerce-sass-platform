from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from catalogue.api.routes import categories, extended, health, products, public_catalogue

@asynccontextmanager
async def lifespan(_: FastAPI):
    yield

app = FastAPI(title="Catalogue Service", version="0.1.0", lifespan=lifespan)
app.state.settings = __import__("catalogue.config.settings", fromlist=["load_settings"]).load_settings()
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3001"], allow_credentials=False, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type"])
app.include_router(health.router)
app.include_router(products.router)
app.include_router(categories.router)
app.include_router(extended.router)
app.include_router(public_catalogue.router)
