
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, health, users
from app.core.config import settings
from .api.hints import router as hints_router

app = FastAPI(
    title="Yadok AI API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoints
app.include_router(
    health.router,
    prefix="/api",
)

# Authentication endpoints
app.include_router(
    auth.router,
    prefix="/api/v1",
)

# User profile endpoints
app.include_router(
    users.router,
    prefix="/api/v1",
)
# Feature 06 - Training Modes & Hints
app.include_router(
    hints_router,
    prefix="/api/v1",
)