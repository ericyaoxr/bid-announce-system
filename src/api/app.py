"""FastAPI后端API - 为前端提供REST接口"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.core.sqlite_storage import SQLiteRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="中标结果公示系统 API",
    description="提供公告查询、统计、采集数据管理接口",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

repo = SQLiteRepository(db_path=str(Path(__file__).parent.parent.parent / "data" / "announcements.db"))


# ========== 响应模型 ==========


class AnnouncementItem(BaseModel):
    id: str
    project_id: int | None = None
    project_no: str | None = None
    title: str
    announcement_type: int | None = None
    tender_mode: str | None = None
    tender_mode_desc: str | None = None
    category: str | None = None
    publish_date: str | None = None
    deadline: str | None = None
    url: str | None = None
    source: str | None = None


class AnnouncementListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[AnnouncementItem]


class StatItem(BaseModel):
    name: str
    value: int


class TrendItem(BaseModel):
    date: str
    count: int


class DashboardStats(BaseModel):
    total: int
    today: int
    this_week: int
    this_month: int
    by_category: list[StatItem]
    by_tender_mode: list[StatItem]
    daily_trend: list[TrendItem]


class CrawlerTaskRequest(BaseModel):
    mode: str = "incremental"  # incremental | full
    max_pages: int = 100


class CrawlerTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


# ========== 接口 ==========


@app.get("/api/dashboard", response_model=DashboardStats)
async def get_dashboard_stats() -> DashboardStats:
    """获取Dashboard统计数据"""
    total = repo.count()

    # 今日数据
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    all_records = repo.list_all(limit=100000)

    today_count = 0
    week_count = 0
    month_count = 0
    category_map: dict[str, int] = {}
    mode_map: dict[str, int] = {}
    daily_map: dict[str, int] = {}

    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    for r in all_records:
        pd_str = r.get("publish_date", "")
        if not pd_str:
            continue
        try:
            pd = datetime.fromisoformat(pd_str)
            if pd.tzinfo is not None:
                pd = pd.replace(tzinfo=None)
        except (ValueError, TypeError):
            continue

        if pd >= today_start:
            today_count += 1
        if pd >= week_ago:
            week_count += 1
        if pd >= month_ago:
            month_count += 1

        # 分类统计
        cat = r.get("category", "未知") or "未知"
        category_map[cat] = category_map.get(cat, 0) + 1

        # 招标方式统计
        mode = r.get("tender_mode_desc", "未知") or "未知"
        mode_map[mode] = mode_map.get(mode, 0) + 1

        # 日趋势
        day_key = pd.strftime("%Y-%m-%d")
        daily_map[day_key] = daily_map.get(day_key, 0) + 1

    by_category = [StatItem(name=k, value=v) for k, v in sorted(category_map.items(), key=lambda x: -x[1])]
    by_tender_mode = [StatItem(name=k, value=v) for k, v in sorted(mode_map.items(), key=lambda x: -x[1])]

    # 最近30天趋势
    daily_trend = [
        TrendItem(date=k, count=v)
        for k, v in sorted(daily_map.items(), reverse=True)[:30]
    ]

    return DashboardStats(
        total=total,
        today=today_count,
        this_week=week_count,
        this_month=month_count,
        by_category=by_category,
        by_tender_mode=by_tender_mode,
        daily_trend=daily_trend,
    )


@app.get("/api/announcements", response_model=AnnouncementListResponse)
async def list_announcements(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页条数"),
    keyword: str | None = Query(None, description="关键词搜索"),
    category: str | None = Query(None, description="分类筛选"),
    tender_mode: str | None = Query(None, description="招标方式"),
    start_date: str | None = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="结束日期 YYYY-MM-DD"),
) -> AnnouncementListResponse:
    """查询公告列表"""
    all_records = repo.list_all(limit=100000)
    filtered = all_records

    if keyword:
        kw = keyword.lower()
        filtered = [r for r in filtered if kw in (r.get("title", "") or "").lower()]

    if category:
        filtered = [r for r in filtered if r.get("category") == category]

    if tender_mode:
        filtered = [r for r in filtered if r.get("tender_mode_desc") == tender_mode]

    if start_date:
        filtered = [r for r in filtered if (r.get("publish_date") or "") >= start_date]

    if end_date:
        filtered = [r for r in filtered if (r.get("publish_date") or "") <= end_date + "T23:59:59"]

    total = len(filtered)
    start = (page - 1) * size
    end = start + size
    page_items = filtered[start:end]

    items = [
        AnnouncementItem(
            id=r["id"],
            project_id=r.get("project_id"),
            project_no=r.get("project_no"),
            title=r.get("title", ""),
            announcement_type=r.get("announcement_type"),
            tender_mode=r.get("tender_mode"),
            tender_mode_desc=r.get("tender_mode_desc"),
            category=r.get("category"),
            publish_date=r.get("publish_date"),
            deadline=r.get("deadline"),
            url=r.get("url"),
            source=r.get("source"),
        )
        for r in page_items
    ]

    return AnnouncementListResponse(total=total, page=page, size=size, items=items)


@app.get("/api/announcements/{announcement_id}")
async def get_announcement(announcement_id: str) -> dict[str, Any]:
    """获取公告详情"""
    record = repo.get_by_id_sync(announcement_id)
    if not record:
        raise HTTPException(status_code=404, detail="公告不存在")
    return record


@app.post("/api/crawler/start", response_model=CrawlerTaskResponse)
async def start_crawler(task: CrawlerTaskRequest) -> CrawlerTaskResponse:
    """启动采集数据任务"""
    from src.config.settings import get_settings

    settings = get_settings()
    url = f"{settings.api_base_url}/officialwebsite/project/page"

    task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    logger.info("crawler_task_started", task_id=task_id, mode=task.mode, max_pages=task.max_pages)

    return CrawlerTaskResponse(
        task_id=task_id,
        status="started",
        message=f"采集数据任务已启动: mode={task.mode}, max_pages={task.max_pages}",
    )


@app.get("/api/categories")
async def get_categories() -> list[str]:
    """获取所有分类"""
    all_records = repo.list_all(limit=100000)
    categories = list({r.get("category") for r in all_records if r.get("category")})
    return sorted(categories)


@app.get("/api/tender-modes")
async def get_tender_modes() -> list[str]:
    """获取所有招标方式"""
    all_records = repo.list_all(limit=100000)
    modes = list({r.get("tender_mode_desc") for r in all_records if r.get("tender_mode_desc")})
    return sorted(modes)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """健康检查"""
    return {"status": "ok", "total_records": str(repo.count())}
