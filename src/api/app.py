from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import (
    announcements_router,
    auth_router,
    crawler_router,
    dashboard_router,
    export_router,
    marketing_router,
    notifications_router,
    schedules_router,
)
from src.config.settings import get_settings
from src.core.scheduler import get_scheduler
from src.db.database import close_db, init_db
from src.utils.logger import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(log_level=settings.log_level, log_format=settings.log_format)
    logger.info("application_starting")

    await init_db()
    logger.info("database_initialized")

    _ensure_default_admin()

    if settings.scheduler_enabled:
        scheduler = get_scheduler()
        await _load_scheduled_tasks(scheduler)
        await scheduler.start()
        logger.info("scheduler_started")

    yield

    if settings.scheduler_enabled:
        scheduler = get_scheduler()
        await scheduler.stop()
        logger.info("scheduler_stopped")

    await close_db()
    logger.info("application_stopped")


async def _load_scheduled_tasks(scheduler) -> None:
    from sqlalchemy import select

    from src.db.database import get_session
    from src.db.models import ScheduledTask

    async for session in get_session():
        result = await session.execute(select(ScheduledTask).where(ScheduledTask.enabled))
        tasks = result.scalars().all()

        for task in tasks:
            from src.api.routes.schedules import _register_job_to_scheduler

            _register_job_to_scheduler(task)
            logger.info("loaded_scheduled_task", id=task.id, name=task.name)

        logger.info("loaded_scheduled_tasks", count=len(tasks))
        break


def _ensure_default_admin() -> None:
    import sqlite3

    from src.core.security import get_password_hash

    db_path = get_settings().db_path
    if not Path(db_path).exists():
        return

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone() is None:
            return
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        if count == 0:
            conn.execute(
                "INSERT INTO users (username, hashed_password, is_active, is_admin) VALUES (?, ?, 1, 1)",
                ("admin", get_password_hash("admin")),
            )
            conn.commit()
            logger.info("default_admin_created", username="admin")
    finally:
        conn.close()


app = FastAPI(
    title="中标结果公示系统 API",
    description="提供公告查询、统计、采集数据管理、认证等接口",
    version="3.0.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(announcements_router)
app.include_router(crawler_router)
app.include_router(export_router)
app.include_router(marketing_router)
app.include_router(notifications_router)
app.include_router(schedules_router)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "version": "3.0.0"}


web_dir = Path(__file__).parent.parent.parent / "web"
if web_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(web_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if (
            full_path.startswith("api/")
            or full_path.startswith("docs")
            or full_path.startswith("openapi.json")
            or full_path.startswith("redoc")
        ):
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Not Found")
        index_path = web_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        from fastapi import HTTPException

        raise HTTPException(status_code=404)
