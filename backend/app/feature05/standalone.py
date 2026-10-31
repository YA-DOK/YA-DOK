
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import router
from .imaging import router as imaging_router


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend 5"

app = FastAPI(
    title="YA-DOK - Feature 05",
    description="Clinical Examination & Investigations",
    version="1.0.0",
)

# Backend APIs
app.include_router(router)
app.include_router(imaging_router)

# Frontend static files
app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static",
)


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "feature05",
    }

