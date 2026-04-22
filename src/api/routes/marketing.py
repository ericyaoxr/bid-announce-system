"""营销分析 API - 为营销决策提供数据支撑"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select

from src.api.deps import DbSession
from src.db.models import Announcement

router = APIRouter(prefix="/api/marketing", tags=["营销分析"])


class RegionStat(BaseModel):
    region: str
    count: int = 0
    total_amount: float = 0.0


class CompetitorInfo(BaseModel):
    name: str
    win_count: int = 0
    total_amount: float = 0.0
    avg_amount: float = 0.0
    categories: list[str] = []
    recent_projects: list[str] = []


class OpportunityItem(BaseModel):
    category: str
    count: int = 0
    total_amount: float = 0.0
    avg_amount: float = 0.0
    competitor_count: int = 0
    top_competitors: list[str] = []


class MonthlyTrend(BaseModel):
    month: str
    count: int = 0
    total_amount: float = 0.0
    avg_amount: float = 0.0


class MarketingStats(BaseModel):
    region_distribution: list[RegionStat] = []
    competitors: list[CompetitorInfo] = []
    opportunities: list[OpportunityItem] = []
    monthly_trend: list[MonthlyTrend] = []
    category_competition: list[dict] = []
    key_metrics: dict = {}


@router.get("", response_model=MarketingStats)
async def get_marketing_stats(db: DbSession) -> MarketingStats:
    now = datetime.now(UTC)
    six_months_ago = (now - timedelta(days=180)).isoformat()

    result = MarketingStats()

    await _compute_region_distribution(db, result)
    await _compute_competitor_analysis(db, result)
    await _compute_market_opportunities(db, result)
    await _compute_monthly_trend(db, result)
    await _compute_category_competition(db, result)
    await _compute_key_metrics(db, result, six_months_ago)

    return result


async def _compute_region_distribution(db: DbSession, result: MarketingStats) -> None:
    rows = await db.execute(
        select(Announcement.project_region, func.count(Announcement.id))
        .where(Announcement.project_region.isnot(None), Announcement.project_region != "")
        .group_by(Announcement.project_region)
        .order_by(func.count(Announcement.id).desc())
        .limit(15)
    )
    result.region_distribution = [RegionStat(region=r[0] or "未知", count=r[1]) for r in rows.all()]


async def _compute_competitor_analysis(db: DbSession, result: MarketingStats) -> None:
    winner_rows = await db.execute(
        select(Announcement.winning_bidders, Announcement.title, Announcement.category).where(
            Announcement.winning_bidders.isnot(None),
            Announcement.winning_bidders != "",
            Announcement.winning_bidders != "[]",
        )
    )

    competitor_data: dict[str, dict] = {}
    for wb_str, title, category in winner_rows.all():
        try:
            wbs = json.loads(wb_str)
        except (json.JSONDecodeError, TypeError):
            continue
        for w in wbs:
            if w.get("is_winning") != 1:
                continue
            supplier = w.get("supplier_name", "")
            if not supplier:
                continue
            amt = float(w.get("bid_amount") or 0)
            if supplier not in competitor_data:
                competitor_data[supplier] = {
                    "count": 0,
                    "total_amount": 0.0,
                    "categories": set(),
                    "projects": [],
                }
            competitor_data[supplier]["count"] += 1
            competitor_data[supplier]["total_amount"] += amt
            if category:
                competitor_data[supplier]["categories"].add(category)
            if title and len(competitor_data[supplier]["projects"]) < 3:
                competitor_data[supplier]["projects"].append(title[:50])

    sorted_competitors = sorted(competitor_data.items(), key=lambda x: -x[1]["total_amount"])[:15]
    result.competitors = [
        CompetitorInfo(
            name=name,
            win_count=data["count"],
            total_amount=data["total_amount"],
            avg_amount=data["total_amount"] / data["count"] if data["count"] else 0,
            categories=list(data["categories"])[:5],
            recent_projects=data["projects"],
        )
        for name, data in sorted_competitors
    ]


async def _compute_market_opportunities(db: DbSession, result: MarketingStats) -> None:
    category_rows = await db.execute(
        select(
            Announcement.category,
            func.count(Announcement.id),
            func.avg(Announcement.bid_price),
        )
        .where(
            Announcement.category.isnot(None),
            Announcement.category != "",
            Announcement.publish_date >= (datetime.now(UTC) - timedelta(days=180)).isoformat(),
        )
        .group_by(Announcement.category)
        .order_by(func.count(Announcement.id).desc())
    )

    for row in category_rows.all():
        cat, count, avg_amt = row
        competitor_count = 0
        top_suppliers: list[str] = []

        wb_rows = await db.execute(
            select(Announcement.winning_bidders)
            .where(
                Announcement.category == cat,
                Announcement.winning_bidders.isnot(None),
                Announcement.winning_bidders != "",
                Announcement.winning_bidders != "[]",
            )
            .limit(200)
        )
        supplier_count: dict[str, int] = {}
        for (wb_str,) in wb_rows.all():
            try:
                for w in json.loads(wb_str):
                    if w.get("is_winning") == 1 and w.get("supplier_name"):
                        supplier_count[w["supplier_name"]] = (
                            supplier_count.get(w["supplier_name"], 0) + 1
                        )
            except (json.JSONDecodeError, TypeError):
                pass
        competitor_count = len(supplier_count)
        top_suppliers = [s for s, _ in sorted(supplier_count.items(), key=lambda x: -x[1])[:5]]

        result.opportunities.append(
            OpportunityItem(
                category=cat or "未知",
                count=count,
                total_amount=0,
                avg_amount=avg_amt or 0,
                competitor_count=competitor_count,
                top_competitors=top_suppliers,
            )
        )


async def _compute_monthly_trend(db: DbSession, result: MarketingStats) -> None:
    rows = await db.execute(
        select(
            func.substr(Announcement.publish_date, 1, 7),
            func.count(Announcement.id),
            func.avg(Announcement.bid_price),
        )
        .where(
            Announcement.publish_date >= (datetime.now(UTC) - timedelta(days=365)).isoformat(),
            Announcement.publish_date.isnot(None),
        )
        .group_by(func.substr(Announcement.publish_date, 1, 7))
        .order_by(func.substr(Announcement.publish_date, 1, 7))
    )
    result.monthly_trend = [
        MonthlyTrend(
            month=r[0] or "",
            count=r[1],
            total_amount=0,
            avg_amount=r[2] or 0,
        )
        for r in rows.all()
    ]


async def _compute_category_competition(db: DbSession, result: MarketingStats) -> None:
    categories = ["工程", "货物", "服务"]
    for cat in categories:
        wb_rows = await db.execute(
            select(Announcement.winning_bidders)
            .where(
                Announcement.category == cat,
                Announcement.winning_bidders.isnot(None),
                Announcement.winning_bidders != "",
                Announcement.winning_bidders != "[]",
            )
            .limit(300)
        )
        supplier_count: dict[str, int] = {}
        for (wb_str,) in wb_rows.all():
            try:
                for w in json.loads(wb_str):
                    if w.get("is_winning") == 1 and w.get("supplier_name"):
                        supplier_count[w["supplier_name"]] = (
                            supplier_count.get(w["supplier_name"], 0) + 1
                        )
            except (json.JSONDecodeError, TypeError):
                pass
        top5 = sorted(supplier_count.items(), key=lambda x: -x[1])[:5]
        result.category_competition.append(
            {
                "category": cat,
                "total_competitors": len(supplier_count),
                "top_competitors": [{"name": n, "count": c} for n, c in top5],
            }
        )


async def _compute_key_metrics(db: DbSession, result: MarketingStats, since: str) -> None:
    total_result = await db.execute(
        select(func.count(Announcement.id)).where(
            Announcement.publish_date >= since,
            Announcement.publish_date.isnot(None),
        )
    )
    total = total_result.scalar() or 0

    with_winner = await db.execute(
        select(func.count(Announcement.id)).where(
            Announcement.publish_date >= since,
            Announcement.winning_bidders.isnot(None),
            Announcement.winning_bidders != "",
            Announcement.winning_bidders != "[]",
        )
    )
    winner_count = with_winner.scalar() or 0

    total_amount_result = await db.execute(
        select(func.sum(Announcement.bid_price)).where(
            Announcement.publish_date >= since,
            Announcement.bid_price.isnot(None),
        )
    )
    total_amount = total_amount_result.scalar() or 0

    avg_amount = total_amount / winner_count if winner_count else 0

    result.key_metrics = {
        "total_announcements_6m": total,
        "with_winner_6m": winner_count,
        "total_amount_6m": total_amount,
        "avg_amount_6m": avg_amount,
        "coverage_rate": round(winner_count / total * 100, 1) if total else 0,
    }
