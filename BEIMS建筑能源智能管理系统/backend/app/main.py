from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
from sqlalchemy import func, text

from .config.settings import settings
from .models.database import init_db, SessionLocal, EnergyData
from .routers import data_router, query_router, intelligence_router, auth_router
from .routers.chat_router import router as chat_router
from .utils.mcp_server import mcp_server

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def _mask_database_url(url: str) -> str:
    if "@" not in url or "://" not in url:
        return url
    scheme, rest = url.split("://", 1)
    credentials, host = rest.split("@", 1)
    if ":" in credentials:
        username = credentials.split(":", 1)[0]
        return f"{scheme}://{username}:***@{host}"
    return url


def _probe_database_state() -> None:
    db = SessionLocal()
    try:
        dialect = db.bind.dialect.name if db.bind else "unknown"
        db_name = "unknown"

        if dialect == "postgresql":
            db_name = db.execute(text("SELECT current_database()")) .scalar() or "unknown"
        elif dialect == "sqlite":
            db_name = settings.DATABASE_URL

        total_records = db.query(EnergyData).count()
        total_buildings = db.query(func.count(func.distinct(EnergyData.building_id))).scalar() or 0

        logger.info(
            "Database probe success: dialect=%s db=%s energy_data=%s buildings=%s",
            dialect,
            db_name,
            total_records,
            total_buildings,
        )
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting BEIMS application...")
    
    try:
        logger.info("Configured DATABASE_URL=%s", _mask_database_url(settings.DATABASE_URL))

        if settings.FORCE_POSTGRESQL and not settings.DATABASE_URL.startswith("postgresql://"):
            raise RuntimeError("FORCE_POSTGRESQL=true but DATABASE_URL is not PostgreSQL")

        init_db()
        logger.info("Database initialized successfully")
        _probe_database_state()
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.EXPORT_DIR, exist_ok=True)
    os.makedirs(settings.KNOWLEDGE_BASE_DIR, exist_ok=True)
    
    logger.info("Application startup completed")
    
    yield
    
    logger.info("Shutting down BEIMS application...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="建筑能源智能管理系统 - 集查询统计与智慧运维于一体",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data_router, prefix="/api")
app.include_router(query_router, prefix="/api")
app.include_router(intelligence_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix="")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }


@app.get("/api/mcp/tools")
async def list_mcp_tools():
    return {"tools": mcp_server.list_tools()}


@app.post("/api/mcp/call-tool")
async def call_mcp_tool(request: Request):
    body = await request.json()
    tool_name = body.get("name")
    arguments = body.get("arguments", {})
    
    result = await mcp_server.call_tool(tool_name, arguments)
    return result


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "message": "Internal server error"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
