"""FastAPI main application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .routers import memory, system
from .auth import AuthMiddleware

app = FastAPI(
    title="Jakebot Labs Dashboard",
    version="0.1.0-alpha",
    description="Memory & HealthKit Management Dashboard"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:7842",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:7842",
        "http://192.168.1.167:7842"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Auth middleware (disabled by default)
app.add_middleware(AuthMiddleware)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# API routers
app.include_router(memory.router, prefix="/api")
app.include_router(system.router, prefix="/api")

# Serve static frontend (if built)
static_dir = Path(__file__).parent / "static"
if static_dir.exists() and list(static_dir.glob("*")):
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
