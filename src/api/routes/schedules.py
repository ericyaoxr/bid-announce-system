from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from src.api.deps import AdminUser, DbSession
from src.db.models import ScheduledTask
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/schedules", tags=["定时调度"])


class ScheduleCreate(BaseModel):
    mode: str
    cron: str
    max_pages: int = 10
    days: int | None = None
    enabled: bool = True


class ScheduleResponse(BaseModel):
    id: str
    mode: str
    cron: str
    max_pages: int
    days: int | None = None
    enabled: bool = True


def _register_job_to_scheduler(task: ScheduledTask) -> None:
    from src.core.scheduler import get_scheduler

    scheduler = get_scheduler()
    job_id = task.id

    async def crawl_job() -> None:
        import sqlite3
        import threading
        from src.api.routes.crawler import _run_crawler_sync

        history_id = f"sh_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        conn = sqlite3.connect("data/announcements_deep.db")
        try:
            conn.execute(
                "INSERT INTO schedule_history (id, schedule_id, schedule_name, mode, status, started_at) VALUES (?, ?, ?, ?, ?, ?)",
                (history_id, job_id, task.name, task.mode, "running", datetime.now(UTC).isoformat()),
            )
            conn.commit()
        finally:
            conn.close()

        task_id = f"scheduled_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        thread = threading.Thread(
            target=_run_crawler_sync,
            args=(task.mode, task.max_pages, task.days, task_id),
            daemon=True,
        )
        thread.start()
        thread.join(timeout=3600)

        conn = sqlite3.connect("data/announcements_deep.db")
        try:
            task_result = conn.execute(
                "SELECT status, list_count, detail_count, total_records, with_winner, elapsed_seconds, error_message FROM crawl_tasks WHERE id=?",
                (task_id,),
            ).fetchone()
            if task_result:
                conn.execute(
                    "UPDATE schedule_history SET status=?, list_count=?, detail_count=?, total_records=?, with_winner=?, finished_at=?, elapsed_seconds=?, error_message=? WHERE id=?",
                    (task_result[0], task_result[1], task_result[2], task_result[3], task_result[4], datetime.now(UTC).isoformat(), task_result[5], task_result[6], history_id),
                )
                conn.commit()
        finally:
            conn.close()

    scheduler.add_job(
        id=job_id,
        name=task.name,
        func=crawl_job,
        cron=task.cron,
        enabled=task.enabled,
    )


@router.get("")
async def list_schedules(db: DbSession) -> list[dict]:
    from src.core.scheduler import get_scheduler

    scheduler = get_scheduler()
    aps_jobs = scheduler._scheduler.get_jobs() if scheduler._is_running else []
    aps_job_map = {j.id: j for j in aps_jobs}

    result = await db.execute(select(ScheduledTask).order_by(ScheduledTask.created_at.desc()))
    tasks = result.scalars().all()

    output = []
    for task in tasks:
        aps_job = aps_job_map.get(task.id)
        next_run = None
        if aps_job and aps_job.next_run_time:
            next_run = aps_job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
        output.append({
            "id": task.id,
            "name": task.name,
            "cron": task.cron,
            "next_run": next_run,
            "enabled": task.enabled,
        })
    return output


@router.post("")
async def create_schedule(req: ScheduleCreate, db: DbSession, admin: AdminUser) -> dict:
    from src.core.scheduler import get_scheduler

    job_id = f"crawl_{req.mode}_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    mode_label = {"incremental": "增量", "full": "全量", "by_date": "按时间", "detail_only": "仅详情"}.get(req.mode, req.mode)
    task_name = f"定时{mode_label}采集"

    task = ScheduledTask(
        id=job_id,
        name=task_name,
        mode=req.mode,
        cron=req.cron,
        max_pages=req.max_pages,
        days=req.days,
        enabled=req.enabled,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    _register_job_to_scheduler(task)

    return {"id": job_id, "name": task_name, "mode": req.mode, "cron": req.cron, "status": "created"}


@router.delete("/{job_id}")
async def delete_schedule(job_id: str, db: DbSession, _admin: AdminUser) -> dict:
    from src.core.scheduler import get_scheduler

    result = await db.execute(select(ScheduledTask).where(ScheduledTask.id == job_id))
    task = result.scalar()
    if task:
        await db.delete(task)
        await db.commit()

    scheduler = get_scheduler()
    scheduler.remove_job(job_id)
    return {"message": "定时任务已删除"}


@router.post("/{job_id}/pause")
async def pause_schedule(job_id: str, db: DbSession, _admin: AdminUser) -> dict:
    from src.core.scheduler import get_scheduler

    result = await db.execute(select(ScheduledTask).where(ScheduledTask.id == job_id))
    task = result.scalar()
    if task:
        task.enabled = False
        await db.commit()

    scheduler = get_scheduler()
    scheduler.pause_job(job_id)
    return {"message": "定时任务已暂停"}


@router.post("/{job_id}/resume")
async def resume_schedule(job_id: str, db: DbSession, _admin: AdminUser) -> dict:
    from src.core.scheduler import get_scheduler

    result = await db.execute(select(ScheduledTask).where(ScheduledTask.id == job_id))
    task = result.scalar()
    if task:
        task.enabled = True
        await db.commit()

    scheduler = get_scheduler()
    scheduler.resume_job(job_id)
    return {"message": "定时任务已恢复"}


@router.get("/history")
async def list_schedule_history(db: DbSession, limit: int = 50) -> list[dict]:
    from src.db.models import ScheduleHistory

    result = await db.execute(
        select(ScheduleHistory).order_by(ScheduleHistory.created_at.desc()).limit(limit)
    )
    records = result.scalars().all()
    return [
        {
            "id": r.id,
            "schedule_id": r.schedule_id,
            "schedule_name": r.schedule_name,
            "mode": r.mode,
            "status": r.status,
            "list_count": r.list_count,
            "detail_count": r.detail_count,
            "total_records": r.total_records,
            "with_winner": r.with_winner,
            "elapsed_seconds": r.elapsed_seconds,
            "started_at": r.started_at,
            "finished_at": r.finished_at,
            "error_message": r.error_message,
            "created_at": r.created_at,
        }
        for r in records
    ]
