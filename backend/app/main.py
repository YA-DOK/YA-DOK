
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, health, simulation, users
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # A shared, pooled HTTP client: no TCP/TLS handshake per chat turn.
    async with httpx.AsyncClient(
        limits=httpx.Limits(max_connections=40, max_keepalive_connections=20),
        timeout=httpx.Timeout(15.0, connect=2.0),
    ) as client:
        app.state.f04_http_client = client
        yield


app = FastAPI(
    lifespan=lifespan,
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
    admin_case_library,
    case_approval,
    case_lifecycle,
    cases,
    student_cases,
)

app.include_router(cases.router, prefix="/api/v1")
app.include_router(student_cases.router, prefix="/api/v1")
app.include_router(case_lifecycle.router, prefix="/api/v1")
app.include_router(admin_case_library.router, prefix="/api/v1")
app.include_router(case_approval.router, prefix="/api/v1")

# F02 + F03 published-case integration
from app.api.routes import published_simulation

app.include_router(published_simulation.router, prefix="/api/v1")

# F04: version-pinned, authorized, idempotent patient chat API.
from app.api.routes import patient_chat

app.include_router(patient_chat.router, prefix="/api/v1")

# F05 clinical catalog and private, session-owned imaging assets.
from app.feature05 import session_api as f05_session_api

app.include_router(f05_session_api.router, prefix="/api/v1")
