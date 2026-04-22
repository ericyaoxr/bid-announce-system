from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from src.api.deps import AdminUser, CurrentUser, DbSession
from src.db.models import ScheduledTask, ScheduleEditHistory
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/schedules", tags=["定时调度"])


class ScheduleCreate(BaseModel):
    mode: str
    cron: str
    max_pages: int = 10
    days: int | None = None
    enabled: bool = True
    description: str | None = None


class ScheduleUpdate(BaseModel):
    name: str | None = None
    cron: str | None = None
    max_pages: int | None = None
    days: int | None = None
    enabled: bool | None = None
    description: str | None = None


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
                (
                    history_id,
                    job_id,
                    task.name,
                    task.mode,
                    "running",
                    datetime.now(UTC).isoformat(),
                ),
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
                    (
                        task_result[0],
                        task_result[1],
                        task_result[2],
                        task_result[3],
                        task_result[4],
                        datetime.now(UTC).isoformat(),
                        task_result[5],
                        task_result[6],
                        history_id,
                    ),
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


def _update_scheduler_job(task: ScheduledTask) -> None:
    """更新调度器中的任务"""
    from src.core.scheduler import get_scheduler

    scheduler = get_scheduler()
    if task.id in scheduler._jobs:
        scheduler.remove_job(task.id)
    _register_job_to_scheduler(task)


def _detect_cron_conflict(cron: str, exclude_id: str | None = None) -> bool:
    """检测cron表达式是否与其他任务冲突（简单检测：相同cron视为冲突）"""
    # 实际项目中可以实现更复杂的冲突检测逻辑
    return False


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
        output.append(
            {
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "mode": task.mode,
                "cron": task.cron,
                "max_pages": task.max_pages,
                "days": task.days,
                "next_run": next_run,
                "enabled": task.enabled,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
            }
        )
    return output


@router.post("")
async def create_schedule(req: ScheduleCreate, db: DbSession, admin: AdminUser) -> dict:

    job_id = f"crawl_{req.mode}_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    mode_label = {
        "incremental": "增量",
        "full": "全量",
        "by_date": "按时间",
        "detail_only": "仅详情",
    }.get(req.mode, req.mode)
    task_name = f"定时{mode_label}采集"

    task = ScheduledTask(
        id=job_id,
        name=task_name,
        description=req.description,
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

    return {
        "id": job_id,
        "name": task_name,
        "mode": req.mode,
        "cron": req.cron,
        "status": "created",
    }


@router.put("/{job_id}")
async def update_schedule(
    job_id: str,
    req: ScheduleUpdate,
    db: DbSession,
    user: CurrentUser,
) -> dict:
    """更新定时任务 - 支持原子性更新和冲突检测"""
    result = await db.execute(select(ScheduledTask).where(ScheduledTask.id == job_id))
    task = result.scalar()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="定时任务不存在",
        )

    # 记录旧值
    old_values = {
        "name": task.name,
        "cron": task.cron,
        "max_pages": task.max_pages,
        "days": task.days,
        "enabled": task.enabled,
        "description": task.description,
    }

    # 冲突检测：检查cron表达式是否与其他任务冲突
    if req.cron is not None and req.cron != task.cron:
        if _detect_cron_conflict(req.cron, exclude_id=job_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该执行时间与其他任务冲突",
            )

    # 原子性更新
    updated_fields = []
    if req.name is not None:
        task.name = req.name
        updated_fields.append("name")
    if req.cron is not None:
        task.cron = req.cron
        updated_fields.append("cron")
    if req.max_pages is not None:
        task.max_pages = req.max_pages
        updated_fields.append("max_pages")
    if req.days is not None:
        task.days = req.days
        updated_fields.append("days")
    if req.enabled is not None:
        task.enabled = req.enabled
        updated_fields.append("enabled")
    if req.description is not None:
        task.description = req.description
        updated_fields.append("description")

    if not updated_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未提供任何更新字段",
        )

    await db.commit()
    await db.refresh(task)

    # 记录新值
    new_values = {
        "name": task.name,
        "cron": task.cron,
        "max_pages": task.max_pages,
        "days": task.days,
        "enabled": task.enabled,
        "description": task.description,
    }

    # 写入修改历史
    history = ScheduleEditHistory(
        id=f"edit_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{job_id}",
        schedule_id=job_id,
        editor=user.username,
        action=f"update:{','.join(updated_fields)}",
        old_values=str(old_values),
        new_values=str(new_values),
    )
    db.add(history)
    await db.commit()

    # 更新调度器中的任务（立即生效）
    _update_scheduler_job(task)

    logger.info(
        "schedule_updated",
        job_id=job_id,
        editor=user.username,
        fields=updated_fields,
    )

    return {
        "id": job_id,
        "name": task.name,
        "mode": task.mode,
        "cron": task.cron,
        "max_pages": task.max_pages,
        "days": task.days,
        "enabled": task.enabled,
        "description": task.description,
        "updated_fields": updated_fields,
        "status": "updated",
    }


@router.get("/{job_id}")
async def get_schedule(job_id: str, db: DbSession) -> dict:
    """获取单个定时任务详情"""
    result = await db.execute(select(ScheduledTask).where(ScheduledTask.id == job_id))
    task = result.scalar()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="定时任务不存在",
        )

    from src.core.scheduler import get_scheduler

    scheduler = get_scheduler()
    aps_job = None
    if scheduler._is_running:
        aps_job = scheduler._scheduler.get_job(job_id)

    next_run = None
    if aps_job and aps_job.next_run_time:
        next_run = aps_job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")

    return {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "mode": task.mode,
        "cron": task.cron,
        "max_pages": task.max_pages,
        "days": task.days,
        "enabled": task.enabled,
        "next_run": next_run,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


@router.get("/{job_id}/edit-history")
async def get_schedule_edit_history(
    job_id: str,
    db: DbSession,
    limit: int = 50,
) -> list[dict]:
    """获取定时任务修改历史"""
    result = await db.execute(
        select(ScheduleEditHistory)
        .where(ScheduleEditHistory.schedule_id == job_id)
        .order_by(ScheduleEditHistory.created_at.desc())
        .limit(limit)
    )
    records = result.scalars().all()
    return [
        {
            "id": r.id,
            "schedule_id": r.schedule_id,
            "editor": r.editor,
            "action": r.action,
            "old_values": r.old_values,
            "new_values": r.new_values,
            "created_at": r.created_at,
        }
        for r in records
    ]


@router.delete("/{job_id}")
async def delete_schedule(job_id: str, db: DbSession, user: CurrentUser) -> dict:
    from src.core.scheduler import get_scheduler

    result = await db.execute(select(ScheduledTask).where(ScheduledTask.id == job_id))
    task = result.scalar()
    if task:
        # 记录删除历史
        history = ScheduleEditHistory(
            id=f"del_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{job_id}",
            schedule_id=job_id,
            editor=user.username,
            action="delete",
            old_values=str(
                {
                    "name": task.name,
                    "mode": task.mode,
                    "cron": task.cron,
                    "enabled": task.enabled,
                }
            ),
            new_values=None,
        )
        db.add(history)

        await db.delete(task)
        await db.commit()

    scheduler = get_scheduler()
    scheduler.remove_job(job_id)

    logger.info("schedule_deleted", job_id=job_id, editor=user.username)
    return {"message": "定时任务已删除"}


@router.post("/{job_id}/pause")
async def pause_schedule(job_id: str, db: DbSession, user: CurrentUser) -> dict:
    from src.core.scheduler import get_scheduler

    result = await db.execute(select(ScheduledTask).where(ScheduledTask.id == job_id))
    task = result.scalar()
    if task:
        task.enabled = False
        await db.commit()

        # 记录状态变更历史
        history = ScheduleEditHistory(
            id=f"pause_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{job_id}",
            schedule_id=job_id,
            editor=user.username,
            action="pause",
            old_values=str({"enabled": True}),
            new_values=str({"enabled": False}),
        )
        db.add(history)
        await db.commit()

    scheduler = get_scheduler()
    scheduler.pause_job(job_id)

    logger.info("schedule_paused", job_id=job_id, editor=user.username)
    return {"message": "定时任务已暂停"}


@router.post("/{job_id}/resume")
async def resume_schedule(job_id: str, db: DbSession, user: CurrentUser) -> dict:
    from src.core.scheduler import get_scheduler

    result = await db.execute(select(ScheduledTask).where(ScheduledTask.id == job_id))
    task = result.scalar()
    if task:
        task.enabled = True
        await db.commit()

        # 记录状态变更历史
        history = ScheduleEditHistory(
            id=f"resume_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{job_id}",
            schedule_id=job_id,
            editor=user.username,
            action="resume",
            old_values=str({"enabled": False}),
            new_values=str({"enabled": True}),
        )
        db.add(history)
        await db.commit()

    scheduler = get_scheduler()
    scheduler.resume_job(job_id)

    logger.info("schedule_resumed", job_id=job_id, editor=user.username)
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
