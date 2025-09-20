import logging
import asyncio
from fastapi import FastAPI
from app.routers import upload, health, pdf_analysis
from app.services.background_worker import background_pdf_worker
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.utils.db import init_db_pool, close_db_pool
from typing import AsyncGenerator

# Configure logger if needed
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_app: FastAPI)-> AsyncGenerator[None, None]:

    # --- Startup ---
    await init_db_pool()
    logger.info("✅ Database pool initialized")

    # Schedule background worker
    loop = asyncio.get_event_loop()
    loop.create_task(background_pdf_worker())
    logger.info("Background worker scheduled on startup")

    yield # keep app running

    # --- Shutdown ---
    await close_db_pool()
    logger.info("🛑 Database pool closed")

def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    # Mount static files
    # html=True so that directory requests serve index.html if it exists
    app.mount("/static", StaticFiles(directory="app/static", html=True), name="static")

    # Optionally if you want root ("/") to redirect or serve index.html via route

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # or specify ["http://localhost:3000"]
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


    @app.get("/", include_in_schema=False)
    async def root():
        # either return index.html file
        from fastapi.responses import FileResponse
        return FileResponse("app/static/index.html")

    # include routers
    app.include_router(upload.router)
    app.include_router(pdf_analysis.router)
    app.include_router(health.router)

    return app

app = create_app()


