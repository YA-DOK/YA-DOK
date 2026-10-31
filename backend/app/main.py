
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, health, users, simulation
from app.core.config import settings

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

# Medical simulation endpoints
app.include_router(
    simulation.router,
    prefix="/api/v1",
)

# YA-DOK F02 CASE MANAGEMENT ROUTERS
from app.api.routes import (
    cases,
    student_cases,
    case_lifecycle,
    admin_case_library,
    case_approval,
)

app.include_router(cases.router, prefix="/api/v1")
app.include_router(student_cases.router, prefix="/api/v1")
app.include_router(case_lifecycle.router, prefix="/api/v1")
app.include_router(admin_case_library.router, prefix="/api/v1")
app.include_router(case_approval.router, prefix="/api/v1")

# F02 + F03 published-case integration
from app.api.routes import published_simulation
app.include_router(published_simulation.router, prefix="/api/v1")
