import json

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select

from src.api.deps import DbSession
from src.db.models import Announcement

router = APIRouter(prefix="/api/announcements", tags=["中标结果"])


class WinningBidder(BaseModel):
    supplier_name: str | None = None
    bid_amount: float | None = None
    is_winning: int | None = None
    rank: int | None = None
    social_credit_code: str | None = None


class AnnouncementItem(BaseModel):
    id: str
    project_no: str | None = None
    title: str
    category: str | None = None
    tender_mode_desc: str | None = None
    tenderer_name: str | None = None
    tenderer_contact: str | None = None
    tenderer_phone: str | None = None
    publish_date: str | None = None
    winner_supplier: str = ""
    winner_amount: float | None = None
    winner_credit_code: str = ""
    source_url: str | None = None
    purchase_control_price: float | None = None
    bid_price: float | None = None
    project_address: str | None = None
    fund_source: str | None = None
    detail_fetched: int = 0


class AnnouncementDetail(BaseModel):
    id: str
    project_id: int | None = None
    project_no: str | None = None
    title: str
    announcement_type: int | None = None
    announcement_type_desc: str | None = None
    tender_mode_desc: str | None = None
    category: str | None = None
    publish_date: str | None = None
    deadline: str | None = None
    source_url: str | None = None
    purchase_control_price: float | None = None
    bid_price: float | None = None
    winning_bidders: list[WinningBidder] | None = None
    tenderer_name: str | None = None
    tenderer_contact: str | None = None
    tenderer_phone: str | None = None
    project_address: str | None = None
    fund_source: str | None = None
    tender_content: str | None = None
    detail_fetched: int = 0


class AnnouncementListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[AnnouncementItem]


@router.get("", response_model=AnnouncementListResponse)
async def list_announcements(
    db: DbSession,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None),
    category: str | None = Query(None),
    tender_mode: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
) -> AnnouncementListResponse:
    query = select(Announcement).order_by(Announcement.publish_date.desc())

    if keyword:
        kw = f"%{keyword}%"
        query = query.where(
            (Announcement.title.ilike(kw))
            | (Announcement.project_no.ilike(kw))
            | (Announcement.tenderer_name.ilike(kw))
        )
    if category:
        query = query.where(Announcement.category == category)
    if tender_mode:
        query = query.where(Announcement.tender_mode_desc == tender_mode)
    if start_date:
        query = query.where(Announcement.publish_date >= start_date)
    if end_date:
        query = query.where(Announcement.publish_date <= end_date + "T23:59:59")

    from sqlalchemy import func

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    result = await db.execute(query)
    rows = result.scalars().all()

    items: list[AnnouncementItem] = []
    for r in rows:
        wbs_all = []
        if r.winning_bidders and r.winning_bidders not in ("", "[]"):
            try:
                wbs_all = json.loads(r.winning_bidders)
            except (json.JSONDecodeError, TypeError):
                pass

        wbs = [w for w in wbs_all if w.get("is_winning") == 1]

        if not wbs:
            items.append(
                AnnouncementItem(
                    id=r.id,
                    project_no=r.project_no,
                    title=r.title or "",
                    category=r.category,
                    tender_mode_desc=r.tender_mode_desc,
                    tenderer_name=r.tenderer_name,
                    tenderer_contact=r.tenderer_contact,
                    tenderer_phone=r.tenderer_phone,
                    publish_date=r.publish_date,
                    source_url=r.source_url,
                    purchase_control_price=r.purchase_control_price,
                    bid_price=r.bid_price,
                    detail_fetched=r.detail_fetched or 0,
                )
            )
        else:
            for w in wbs:
                items.append(
                    AnnouncementItem(
                        id=r.id,
                        project_no=r.project_no,
                        title=r.title or "",
                        category=r.category,
                        tender_mode_desc=r.tender_mode_desc,
                        tenderer_name=r.tenderer_name,
                        tenderer_contact=r.tenderer_contact,
                        tenderer_phone=r.tenderer_phone,
                        publish_date=r.publish_date,
                        source_url=r.source_url,
                        purchase_control_price=r.purchase_control_price,
                        bid_price=r.bid_price,
                        winner_supplier=w.get("supplier_name", ""),
                        winner_amount=w.get("bid_amount"),
                        winner_credit_code=w.get("social_credit_code", ""),
                        detail_fetched=r.detail_fetched or 0,
                    )
                )

    return AnnouncementListResponse(total=total, page=page, size=size, items=items)


@router.get("/categories")
async def get_categories(db: DbSession) -> list[str]:
    from sqlalchemy import func

    result = await db.execute(
        select(Announcement.category)
        .where(Announcement.category.isnot(None), Announcement.category != "")
        .group_by(Announcement.category)
        .order_by(func.count(Announcement.id).desc())
    )
    return [r[0] for r in result.all()]


@router.get("/tender-modes")
async def get_tender_modes(db: DbSession) -> list[str]:
    from sqlalchemy import func

    result = await db.execute(
        select(Announcement.tender_mode_desc)
        .where(Announcement.tender_mode_desc.isnot(None), Announcement.tender_mode_desc != "")
        .group_by(Announcement.tender_mode_desc)
        .order_by(func.count(Announcement.id).desc())
    )
    return [r[0] for r in result.all()]


@router.get("/{announcement_id}", response_model=AnnouncementDetail)
async def get_announcement(announcement_id: str, db: DbSession) -> AnnouncementDetail:
    result = await db.execute(select(Announcement).where(Announcement.id == announcement_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="公告不存在")

    wbs = []
    if r.winning_bidders and r.winning_bidders not in ("", "[]"):
        try:
            wbs = [WinningBidder(**w) for w in json.loads(r.winning_bidders)]
        except (json.JSONDecodeError, TypeError):
            pass

    return AnnouncementDetail(
        id=r.id,
        project_id=r.project_id,
        project_no=r.project_no,
        title=r.title or "",
        announcement_type=r.announcement_type,
        announcement_type_desc=r.announcement_type_desc,
        tender_mode_desc=r.tender_mode_desc,
        category=r.category,
        publish_date=r.publish_date,
        deadline=r.deadline,
        source_url=r.source_url,
        purchase_control_price=r.purchase_control_price,
        bid_price=r.bid_price,
        winning_bidders=wbs,
        tenderer_name=r.tenderer_name,
        tenderer_contact=r.tenderer_contact,
        tenderer_phone=r.tenderer_phone,
        project_address=r.project_address,
        fund_source=r.fund_source,
        tender_content=r.tender_content,
        detail_fetched=r.detail_fetched or 0,
    )
