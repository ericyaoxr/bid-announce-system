from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, Float, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(String, primary_key=True)
    project_id = Column(Integer, index=True)
    project_no = Column(String)
    title = Column(String, nullable=False)
    announcement_type = Column(Integer, index=True)
    announcement_type_desc = Column(String)
    tender_mode = Column(String)
    tender_mode_desc = Column(String)
    category = Column(String, index=True)
    category_code = Column(String)
    publish_date = Column(String, index=True)
    deadline = Column(String)
    current_status = Column(Integer)
    project_source = Column(Integer)
    source_url = Column(String)

    purchase_control_price = Column(Float)
    bid_price = Column(Float)
    winning_bidders = Column(Text)
    candidate_info = Column(Text)
    change_records = Column(Text)
    project_address = Column(String)
    project_region = Column(String)
    fund_source = Column(String)
    tender_organize_form = Column(String)
    purchase_process = Column(String)
    grade_method = Column(String)
    qualification_method = Column(String)
    quotation_method = Column(String)
    is_security_deposit = Column(Integer)
    is_consortium_bidding = Column(String)
    is_eval_separate = Column(Integer)
    package_name = Column(String)
    package_category = Column(String)
    tenderer_name = Column(String)
    tenderer_contact = Column(String)
    tenderer_phone = Column(String)
    tenderer_address = Column(String)
    tender_content = Column(Text)
    engineering_name = Column(String)

    detail_fetched = Column(Integer, default=0, index=True)
    raw_list_data = Column(Text)
    raw_detail_data = Column(Text)
    content_hash = Column(String)
    created_at = Column(String, default=lambda: datetime.now(UTC).isoformat())
    updated_at = Column(
        String,
        default=lambda: datetime.now(UTC).isoformat(),
        onupdate=lambda: datetime.now(UTC).isoformat(),
    )

    __table_args__ = (
        Index("idx_announcement_filter", "announcement_type", "category", "publish_date"),
        Index("idx_winner_lookup", "winning_bidders"),
    )


class CrawlTask(Base):
    __tablename__ = "crawl_tasks"

    id = Column(String, primary_key=True)
    mode = Column(String, nullable=False)
    status = Column(String, default="pending")
    max_pages = Column(Integer, default=10)
    days = Column(Integer, nullable=True)
    list_count = Column(Integer, default=0)
    detail_count = Column(Integer, default=0)
    removed_no_winner = Column(Integer, default=0)
    total_records = Column(Integer, default=0)
    with_winner = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(String, nullable=True)
    finished_at = Column(String, nullable=True)
    elapsed_seconds = Column(Float, default=0.0)
    created_at = Column(String, default=lambda: datetime.now(UTC).isoformat())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(String, default=lambda: datetime.now(UTC).isoformat())


class DashboardStat(Base):
    __tablename__ = "dashboard_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_key = Column(String, unique=True, nullable=False, index=True)
    stat_value = Column(Text, nullable=False)
    updated_at = Column(
        String,
        default=lambda: datetime.now(UTC).isoformat(),
        onupdate=lambda: datetime.now(UTC).isoformat(),
    )


class Site(Base):
    __tablename__ = "sites"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    base_url = Column(String, nullable=False)
    description = Column(Text, default="")
    enabled = Column(Boolean, default=True)
    crawler_type = Column(String, default="deep")
    created_at = Column(String, default=lambda: datetime.now(UTC).isoformat())
    updated_at = Column(
        String,
        default=lambda: datetime.now(UTC).isoformat(),
        onupdate=lambda: datetime.now(UTC).isoformat(),
    )


class ScheduleHistory(Base):
    __tablename__ = "schedule_history"

    id = Column(String, primary_key=True)
    schedule_id = Column(String, nullable=False, index=True)
    schedule_name = Column(String, nullable=False)
    mode = Column(String, nullable=False)
    status = Column(String, default="pending")
    list_count = Column(Integer, default=0)
    detail_count = Column(Integer, default=0)
    total_records = Column(Integer, default=0)
    with_winner = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(String, nullable=True)
    finished_at = Column(String, nullable=True)
    elapsed_seconds = Column(Float, default=0.0)
    created_at = Column(String, default=lambda: datetime.now(UTC).isoformat())


class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    mode = Column(String, nullable=False)
    cron = Column(String, nullable=False)
    max_pages = Column(Integer, default=10)
    days = Column(Integer, nullable=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(String, default=lambda: datetime.now(UTC).isoformat())
    updated_at = Column(
        String,
        default=lambda: datetime.now(UTC).isoformat(),
        onupdate=lambda: datetime.now(UTC).isoformat(),
    )


class NotificationConfig(Base):
    __tablename__ = "notification_configs"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    ntype = Column(String, nullable=False)  # webhook, feishu, dingtalk, wecom, email
    enabled = Column(Boolean, default=True)
    config = Column(Text, nullable=False)  # JSON string
    created_at = Column(String, default=lambda: datetime.now(UTC).isoformat())
    updated_at = Column(
        String,
        default=lambda: datetime.now(UTC).isoformat(),
        onupdate=lambda: datetime.now(UTC).isoformat(),
    )
