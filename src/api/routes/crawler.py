import asyncio
import sqlite3
import time
from datetime import UTC, datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy import select

from src.api.deps import AdminUser, DbSession
from src.db.models import CrawlTask, Site
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/crawler", tags=["采集管理"])

DB_PATH = "data/announcements_deep.db"


class CrawlerStartRequest(BaseModel):
    mode: str = "incremental"
    max_pages: int = 100
    days: int | None = None


class CrawlerStatusResponse(BaseModel):
    is_running: bool
    mode: str = ""
    task_id: str = ""
    elapsed: str = ""
    progress: dict = {}
    result: dict = {}
    recent_logs: list[dict] = []
    log_count: int = 0


class CrawlTaskManager:
    def __init__(self) -> None:
        self.is_running = False
        self.mode = ""
        self.task_id = ""
        self.start_time: float | None = None
        self.logs: list[dict] = []
        self.progress: dict = {}
        self.result: dict = {}
        self._stop_flag = False
        self._thread = None
        self._ws_clients: list[WebSocket] = []

    def add_log(self, msg: str, level: str = "info") -> None:
        cst = timezone(timedelta(hours=8))
        entry = {
            "time": datetime.now(cst).strftime("%H:%M:%S"),
            "level": level,
            "msg": msg,
        }
        self.logs.insert(0, entry)
        if len(self.logs) > 200:
            self.logs = self.logs[:200]
        for ws in self._ws_clients:
            try:
                asyncio.get_event_loop().create_task(ws.send_json(entry))
            except Exception:
                pass

    async def add_ws_client(self, ws: WebSocket) -> None:
        await ws.accept()
        self._ws_clients.append(ws)

    def remove_ws_client(self, ws: WebSocket) -> None:
        if ws in self._ws_clients:
            self._ws_clients.remove(ws)

    def to_dict(self) -> dict:
        elapsed = ""
        if self.start_time:
            if self.is_running:
                elapsed = f"{time.time() - self.start_time:.1f}s"
            else:
                elapsed = f"{self.result.get('elapsed', 0):.1f}s"
        return {
            "is_running": self.is_running,
            "mode": self.mode,
            "task_id": self.task_id,
            "elapsed": elapsed,
            "progress": self.progress,
            "result": self.result,
            "recent_logs": self.logs[:50],
            "log_count": len(self.logs),
        }


crawler_manager = CrawlTaskManager()


def _run_crawler_sync(mode: str, max_pages: int, days: int | None, task_id: str) -> None:
    crawler_manager.is_running = True
    crawler_manager.mode = mode
    crawler_manager.start_time = time.time()
    crawler_manager.progress = {"phase": "starting", "detail": "初始化..."}
    crawler_manager.result = {}
    crawler_manager._stop_flag = False

    mode_label = {
        "incremental": "增量",
        "full": "全量",
        "by_date": "按时间",
        "detail_only": "仅详情",
    }.get(mode, mode)
    extra = f", 最近{days}天" if mode == "by_date" and days else ""
    crawler_manager.add_log(f"启动{mode_label}采集, max_pages={max_pages}{extra}")

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_async_crawler_main(mode, max_pages, days))
        loop.close()
    except Exception as e:
        crawler_manager.add_log(f"采集异常: {str(e)}", "error")
        crawler_manager.result = {"status": "error", "error": str(e)}
    finally:
        elapsed = time.time() - crawler_manager.start_time
        crawler_manager.is_running = False
        crawler_manager.result["elapsed"] = elapsed
        crawler_manager.progress["phase"] = "done"
        crawler_manager.add_log(f"采集完成, 耗时 {elapsed:.1f}s")

        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute(
                "UPDATE crawl_tasks SET status=?, finished_at=?, elapsed_seconds=?, "
                "list_count=?, detail_count=?, removed_no_winner=?, total_records=?, "
                "with_winner=?, error_message=? WHERE id=?",
                (
                    "error" if crawler_manager.result.get("status") == "error" else "completed",
                    datetime.now(UTC).isoformat(),
                    elapsed,
                    crawler_manager.result.get("list_count", 0),
                    crawler_manager.result.get("detail_count", 0),
                    crawler_manager.result.get("removed_no_winner", 0),
                    crawler_manager.result.get("total_records", 0),
                    crawler_manager.result.get("with_winner", 0),
                    crawler_manager.result.get("error"),
                    task_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()


async def _async_crawler_main(mode: str, max_pages: int, days: int | None) -> None:
    from src.crawlers.deep_crawler import DeepCrawler

    crawler = DeepCrawler(db_path=DB_PATH, rate_limit_rpm=120)

    try:
        if mode == "incremental":
            crawler_manager.add_log("增量采集: 抓取结果公示新数据...")
            crawler_manager.progress = {"phase": "list", "detail": "抓取结果公示新数据..."}
            list_count = await crawler.crawl_list(4, max_pages=max_pages, incremental=True)
            crawler_manager.add_log(f"列表抓取完成: 新增 {list_count} 条")
            crawler_manager.progress = {
                "phase": "detail",
                "detail": f"列表完成(新增{list_count}条), 开始抓详情...",
                "list_count": list_count,
            }
            detail_count = await crawler.crawl_details(announcement_type=4)
            crawler_manager.add_log(f"详情抓取完成: {detail_count} 条")
            removed = crawler.remove_no_winner()
            crawler_manager.add_log(f"清理无中标记录: 删除 {removed} 条")

        elif mode == "full":
            crawler_manager.add_log("全量采集: 抓取结果公示全部数据...")
            crawler_manager.progress = {"phase": "list", "detail": "抓取结果公示列表..."}
            list_count = await crawler.crawl_list(4, max_pages=max_pages)
            crawler_manager.add_log(f"结果公示: 新增 {list_count} 条")
            if not crawler_manager._stop_flag:
                crawler_manager.progress = {
                    "phase": "detail",
                    "detail": f"列表完成({list_count}条), 开始抓详情...",
                    "list_count": list_count,
                }
                detail_count = await crawler.crawl_details(announcement_type=4)
                crawler_manager.add_log(f"详情抓取完成: {detail_count} 条")
                removed = crawler.remove_no_winner()
                crawler_manager.add_log(f"清理无中标记录: 删除 {removed} 条")

        elif mode == "by_date":
            actual_days = days or 30
            crawler_manager.add_log(f"按时间采集: 结果公示最近 {actual_days} 天...")
            crawler_manager.progress = {
                "phase": "list",
                "detail": f"按时间采集(最近{actual_days}天)...",
            }
            est_pages = max(1, (actual_days * 5 + 19) // 20)
            list_count = await crawler.crawl_list(4, max_pages=est_pages, incremental=True)
            crawler_manager.add_log(f"结果公示: 新增 {list_count} 条")
            if not crawler_manager._stop_flag:
                detail_count = await crawler.crawl_details(announcement_type=4)
                crawler_manager.add_log(f"详情抓取完成: {detail_count} 条")
                removed = crawler.remove_no_winner()
                crawler_manager.add_log(f"清理无中标记录: 删除 {removed} 条")

        elif mode == "detail_only":
            crawler_manager.add_log("仅抓取结果公示详情页...")
            crawler_manager.progress = {"phase": "detail", "detail": "抓取详情页..."}
            detail_count = await crawler.crawl_details(announcement_type=4)
            crawler_manager.add_log(f"详情抓取完成: {detail_count} 条")
            removed = crawler.remove_no_winner()
            crawler_manager.add_log(f"清理无中标记录: 删除 {removed} 条")

        conn = sqlite3.connect(DB_PATH)
        total = conn.execute("SELECT COUNT(*) FROM announcements").fetchone()[0]
        with_winner = conn.execute(
            "SELECT COUNT(*) FROM announcements WHERE winning_bidders IS NOT NULL AND winning_bidders != '[]'"
        ).fetchone()[0]
        conn.close()

        crawler_manager.result.update(
            {
                "status": "success",
                "total_records": total,
                "with_winner": with_winner,
            }
        )
        crawler_manager.add_log(f"采集完成! 总记录={total}, 有中标={with_winner}")

        await _send_crawl_notification(mode, total, with_winner)

    finally:
        await crawler.close()


async def _send_crawl_notification(mode: str, total: int, with_winner: int) -> None:
    try:
        import json

        from sqlalchemy import select

        from src.core.notifier import NotificationService
        from src.db.database import get_session
        from src.db.models import NotificationConfig

        async for session in get_session():
            result = await session.execute(
                select(NotificationConfig).where(NotificationConfig.enabled)
            )
            configs = result.scalars().all()
            if not configs:
                break

            notifier_configs = [
                {
                    "type": c.ntype,
                    "enabled": c.enabled,
                    **json.loads(c.config),
                }
                for c in configs
            ]

            service = NotificationService({"notifiers": notifier_configs})
            mode_label = {
                "incremental": "增量",
                "full": "全量",
                "by_date": "按时间",
                "detail_only": "仅详情",
            }.get(mode, mode)
            await service.send(
                f"采集完成 - {mode_label}模式",
                f"总记录数: {total}\n有中标记录: {with_winner}",
            )
            break
    except Exception as e:
        logger.error("发送采集通知失败: %s", e)


@router.get("/sites/registry")
async def list_crawler_sites() -> dict:
    from src.crawlers.registry import list_crawlers

    return {"sites": list_crawlers()}


@router.post("/start")
async def start_crawler(req: CrawlerStartRequest, db: DbSession, _admin: AdminUser) -> dict:
    if crawler_manager.is_running:
        raise HTTPException(status_code=409, detail="采集任务正在运行中")

    task_id = f"task_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    task = CrawlTask(
        id=task_id,
        mode=req.mode,
        status="running",
        max_pages=req.max_pages,
        days=req.days,
        started_at=datetime.now(UTC).isoformat(),
    )
    db.add(task)
    await db.flush()

    crawler_manager.task_id = task_id

    import threading

    thread = threading.Thread(
        target=_run_crawler_sync,
        args=(req.mode, req.max_pages, req.days, task_id),
        daemon=True,
    )
    thread.start()
    crawler_manager._thread = thread

    return {"task_id": task_id, "status": "started", "message": f"采集任务已启动: mode={req.mode}"}


@router.post("/stop")
async def stop_crawler(_admin: AdminUser) -> dict:
    if not crawler_manager.is_running:
        raise HTTPException(status_code=400, detail="没有正在运行的采集任务")
    crawler_manager._stop_flag = True
    crawler_manager.add_log("用户请求停止采集")
    return {"message": "停止信号已发送"}


@router.get("/status", response_model=CrawlerStatusResponse)
async def get_crawler_status() -> CrawlerStatusResponse:
    data = crawler_manager.to_dict()
    return CrawlerStatusResponse(**data)


@router.websocket("/ws")
async def crawler_websocket(ws: WebSocket) -> None:
    await crawler_manager.add_ws_client(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        crawler_manager.remove_ws_client(ws)


@router.get("/tasks")
async def list_crawl_tasks(
    db: DbSession,
    limit: int = 20,
) -> list[dict]:
    result = await db.execute(select(CrawlTask).order_by(CrawlTask.created_at.desc()).limit(limit))
    tasks = result.scalars().all()
    return [
        {
            "id": t.id,
            "mode": t.mode,
            "status": t.status,
            "max_pages": t.max_pages,
            "days": t.days,
            "list_count": t.list_count,
            "detail_count": t.detail_count,
            "total_records": t.total_records,
            "with_winner": t.with_winner,
            "elapsed_seconds": t.elapsed_seconds,
            "started_at": t.started_at,
            "finished_at": t.finished_at,
            "error_message": t.error_message,
        }
        for t in tasks
    ]


class SiteCreate(BaseModel):
    id: str
    name: str
    base_url: str
    description: str = ""
    crawler_type: str = "deep"
    enabled: bool = True


class SiteUpdate(BaseModel):
    name: str | None = None
    base_url: str | None = None
    description: str | None = None
    crawler_type: str | None = None
    enabled: bool | None = None


@router.get("/sites")
async def list_sites(db: DbSession) -> list[dict]:
    result = await db.execute(select(Site).order_by(Site.created_at.desc()))
    sites = result.scalars().all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "base_url": s.base_url,
            "description": s.description,
            "enabled": s.enabled,
            "crawler_type": s.crawler_type,
            "created_at": s.created_at,
        }
        for s in sites
    ]


@router.post("/sites")
async def create_site(req: SiteCreate, db: DbSession, _admin: AdminUser) -> dict:
    existing = await db.execute(select(Site).where(Site.id == req.id))
    if existing.scalar():
        raise HTTPException(status_code=409, detail="站点ID已存在")

    site = Site(
        id=req.id,
        name=req.name,
        base_url=req.base_url,
        description=req.description,
        crawler_type=req.crawler_type,
        enabled=req.enabled,
    )
    db.add(site)
    await db.flush()
    return {"id": site.id, "name": site.name, "status": "created"}


@router.put("/sites/{site_id}")
async def update_site(site_id: str, req: SiteUpdate, db: DbSession, _admin: AdminUser) -> dict:
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar()
    if not site:
        raise HTTPException(status_code=404, detail="站点不存在")

    if req.name is not None:
        site.name = req.name
    if req.base_url is not None:
        site.base_url = req.base_url
    if req.description is not None:
        site.description = req.description
    if req.crawler_type is not None:
        site.crawler_type = req.crawler_type
    if req.enabled is not None:
        site.enabled = req.enabled

    await db.flush()
    return {"id": site.id, "name": site.name, "status": "updated"}


@router.delete("/sites/{site_id}")
async def delete_site(site_id: str, db: DbSession, _admin: AdminUser) -> dict:
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar()
    if not site:
        raise HTTPException(status_code=404, detail="站点不存在")

    await db.delete(site)
    await db.flush()
    return {"message": "站点已删除"}


@router.post("/sites/{site_id}/toggle")
async def toggle_site(site_id: str, db: DbSession, _admin: AdminUser) -> dict:
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar()
    if not site:
        raise HTTPException(status_code=404, detail="站点不存在")

    site.enabled = not site.enabled
    await db.flush()
    return {"id": site.id, "enabled": site.enabled}
