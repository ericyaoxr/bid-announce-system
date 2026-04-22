import json
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select, text

from src.api.deps import DbSession
from src.db.models import Announcement

router = APIRouter(prefix="/api/dashboard", tags=["数据概览"])


class StatItem(BaseModel):
    name: str
    value: int


class TrendItem(BaseModel):
    date: str
    count: int


class TopCompany(BaseModel):
    rank: int = 0
    name: str
    count: int = 0
    total_amount: float = 0.0


class CrawlTaskRecord(BaseModel):
    id: str
    task_type: str  # manual or scheduled
    mode: str
    status: str
    record_count: int | None
    elapsed_seconds: float | None
    started_at: str | None
    finished_at: str | None
    error_message: str | None


class DashboardStats(BaseModel):
    total: int
    today: int
    this_week: int
    this_month: int
    by_category: list[StatItem]
    by_type: list[StatItem]
    by_tender_mode: list[StatItem]
    daily_trend: list[TrendItem]
    total_bid_amount: float
    winning_count: int
    top_count_companies: list[TopCompany] = []
    top_amount_companies: list[TopCompany] = []
    crawl_stats: dict = {}
    recent_crawl_tasks: list[CrawlTaskRecord] = []


@router.get("", response_model=DashboardStats)
async def get_dashboard_stats(db: DbSession) -> DashboardStats:
    now = datetime.now(UTC)
    today_str = now.strftime("%Y-%m-%d")
    week_ago_str = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    month_ago_str = (now - timedelta(days=30)).strftime("%Y-%m-%d")

    total_result = await db.execute(select(func.count(Announcement.id)))
    total = total_result.scalar() or 0

    today_count = (
        await db.execute(
            select(func.count(Announcement.id)).where(Announcement.publish_date >= today_str)
        )
    ).scalar() or 0

    week_count = (
        await db.execute(
            select(func.count(Announcement.id)).where(Announcement.publish_date >= week_ago_str)
        )
    ).scalar() or 0

    month_count = (
        await db.execute(
            select(func.count(Announcement.id)).where(Announcement.publish_date >= month_ago_str)
        )
    ).scalar() or 0

    category_rows = await db.execute(
        select(Announcement.category, func.count(Announcement.id))
        .group_by(Announcement.category)
        .order_by(func.count(Announcement.id).desc())
    )
    by_category = [StatItem(name=r[0] or "未知", value=r[1]) for r in category_rows.all()]

    type_rows = await db.execute(
        select(Announcement.announcement_type_desc, func.count(Announcement.id))
        .group_by(Announcement.announcement_type_desc)
        .order_by(func.count(Announcement.id).desc())
    )
    by_type = [StatItem(name=r[0] or "未知", value=r[1]) for r in type_rows.all()]

    mode_rows = await db.execute(
        select(Announcement.tender_mode_desc, func.count(Announcement.id))
        .group_by(Announcement.tender_mode_desc)
        .order_by(func.count(Announcement.id).desc())
    )
    by_tender_mode = [StatItem(name=r[0] or "未知", value=r[1]) for r in mode_rows.all()]

    trend_rows = await db.execute(
        select(Announcement.publish_date, func.count(Announcement.id))
        .where(Announcement.publish_date >= month_ago_str)
        .group_by(Announcement.publish_date)
        .order_by(Announcement.publish_date.desc())
        .limit(30)
    )
    daily_trend = [
        TrendItem(date=r[0][:10] if r[0] else "", count=r[1]) for r in trend_rows.all() if r[0]
    ]

    company_stats: dict[str, dict] = {}
    total_bid = 0.0
    winning_count = 0

    winner_rows = await db.execute(
        select(Announcement.winning_bidders).where(
            Announcement.winning_bidders.isnot(None),
            Announcement.winning_bidders != "",
            Announcement.winning_bidders != "[]",
        )
    )
    for (wb_str,) in winner_rows.all():
        try:
            wbs = json.loads(wb_str)
        except (json.JSONDecodeError, TypeError):
            continue
        for w in wbs:
            if w.get("is_winning") != 1:
                continue
            winning_count += 1
            amt = w.get("bid_amount")
            if amt:
                total_bid += float(amt)
            supplier = w.get("supplier_name", "")
            if supplier:
                if supplier not in company_stats:
                    company_stats[supplier] = {"count": 0, "total_amount": 0.0}
                company_stats[supplier]["count"] += 1
                if amt:
                    company_stats[supplier]["total_amount"] += float(amt)

    top_count_companies = []
    if company_stats:
        sorted_by_count = sorted(company_stats.items(), key=lambda x: -x[1]["count"])[:10]
        for rank, (name, stats) in enumerate(sorted_by_count, 1):
            top_count_companies.append(
                TopCompany(
                    rank=rank, name=name, count=stats["count"], total_amount=stats["total_amount"]
                )
            )

    top_amount_companies = []
    if company_stats:
        sorted_by_amount = sorted(company_stats.items(), key=lambda x: -x[1]["total_amount"])[:10]
        for rank, (name, stats) in enumerate(sorted_by_amount, 1):
            top_amount_companies.append(
                TopCompany(
                    rank=rank, name=name, count=stats["count"], total_amount=stats["total_amount"]
                )
            )

    crawl_stats = {
        "data_source_count": 1,
        "running_tasks": 0,
        "failed_tasks": 0,
        "total_records": total,
    }

    from src.db.models import CrawlTask, ScheduleHistory

    crawl_task_rows = await db.execute(
        select(
            CrawlTask.id,
            CrawlTask.mode,
            CrawlTask.status,
            CrawlTask.total_records,
            CrawlTask.elapsed_seconds,
            CrawlTask.started_at,
            CrawlTask.finished_at,
            CrawlTask.error_message,
        )
        .order_by(CrawlTask.created_at.desc())
        .limit(10)
    )
    recent_tasks: list[CrawlTaskRecord] = []
    for row in crawl_task_rows.all():
        recent_tasks.append(
            CrawlTaskRecord(
                id=row[0],
                task_type="manual",
                mode=row[1],
                status=row[2],
                record_count=row[3],
                elapsed_seconds=row[4],
                started_at=row[5],
                finished_at=row[6],
                error_message=row[7],
            )
        )

    schedule_rows = await db.execute(
        select(
            ScheduleHistory.id,
            ScheduleHistory.mode,
            ScheduleHistory.status,
            ScheduleHistory.total_records,
            ScheduleHistory.elapsed_seconds,
            ScheduleHistory.started_at,
            ScheduleHistory.finished_at,
            ScheduleHistory.error_message,
        )
        .order_by(ScheduleHistory.created_at.desc())
        .limit(10)
    )
    for row in schedule_rows.all():
        recent_tasks.append(
            CrawlTaskRecord(
                id=row[0],
                task_type="scheduled",
                mode=row[1],
                status=row[2],
                record_count=row[3],
                elapsed_seconds=row[4],
                started_at=row[5],
                finished_at=row[6],
                error_message=row[7],
            )
        )

    recent_tasks.sort(key=lambda x: x.started_at or "", reverse=True)
    recent_tasks = recent_tasks[:10]

    return DashboardStats(
        total=total,
        today=today_count,
        this_week=week_count,
        this_month=month_count,
        by_category=by_category,
        by_type=by_type,
        by_tender_mode=by_tender_mode,
        daily_trend=daily_trend,
        total_bid_amount=total_bid,
        winning_count=winning_count,
        top_count_companies=top_count_companies,
        top_amount_companies=top_amount_companies,
        crawl_stats=crawl_stats,
        recent_crawl_tasks=recent_tasks,
    )
