"""
任务调度器 - 基于APScheduler
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ScheduledJob:
    """定时任务定义"""

    id: str
    name: str
    func: Callable[[], Awaitable[None]]
    cron: str | None = None  # Cron表达式，如 "0 2 * * *" (每天凌晨2点)
    interval_seconds: int | None = None
    enabled: bool = True
    max_instances: int = 1
    misfire_grace_time: int = 300  # 5分钟


class JobScheduler:
    """
    任务调度器

    Usage:
        async def my_job():
            print("Job executed")

        scheduler = JobScheduler()
        scheduler.add_job(
            id="my_job",
            name="My Job",
            func=my_job,
            cron="0 2 * * *",  # 每天凌晨2点
        )
        await scheduler.start()
    """

    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler()
        self._jobs: dict[str, ScheduledJob] = {}
        self._is_running = False

    def add_job(
        self,
        id: str,
        name: str,
        func: Callable[[], Awaitable[None]],
        cron: str | None = None,
        interval_seconds: int | None = None,
        enabled: bool = True,
        max_instances: int = 1,
        misfire_grace_time: int = 300,
    ) -> None:
        """
        添加定时任务

        Args:
            id: 任务ID
            name: 任务名称
            func: 异步任务函数
            cron: Cron表达式（与interval_seconds二选一）
            interval_seconds: 间隔秒数
            enabled: 是否启用
            max_instances: 最大并发实例数
            misfire_grace_time: 错过的执行时间窗口（秒）
        """
        job = ScheduledJob(
            id=id,
            name=name,
            func=func,
            cron=cron,
            interval_seconds=interval_seconds,
            enabled=enabled,
            max_instances=max_instances,
            misfire_grace_time=misfire_grace_time,
        )

        self._jobs[id] = job

        if self._is_running:
            self._register_job(job)

        logger.info("job_added", id=id, name=name, cron=cron, interval=interval_seconds)

    def remove_job(self, id: str) -> None:
        """移除定时任务"""
        if id in self._jobs:
            job = self._jobs.pop(id)
            if self._is_running:
                self._scheduler.remove_job(job.id)
            logger.info("job_removed", id=id)

    def pause_job(self, id: str) -> None:
        """暂停任务"""
        if id in self._jobs:
            self._jobs[id].enabled = False
            self._scheduler.pause_job(id)
            logger.info("job_paused", id=id)

    def resume_job(self, id: str) -> None:
        """恢复任务"""
        if id in self._jobs:
            self._jobs[id].enabled = True
            self._scheduler.resume_job(id)
            logger.info("job_resumed", id=id)

    def _register_job(self, job: ScheduledJob) -> None:
        """注册任务到调度器"""
        if not job.enabled:
            return

        trigger: CronTrigger | IntervalTrigger

        if job.cron:
            # 解析Cron表达式
            # 格式: "minute hour day month day_of_week"
            parts = job.cron.split()
            if len(parts) >= 5:
                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4],
                )
            else:
                raise ValueError(f"Invalid cron expression: {job.cron}")
        elif job.interval_seconds:
            trigger = IntervalTrigger(seconds=job.interval_seconds)
        else:
            raise ValueError("Either cron or interval_seconds must be specified")

        self._scheduler.add_job(
            job.func,
            trigger=trigger,
            id=job.id,
            name=job.name,
            max_instances=job.max_instances,
            misfire_grace_time=job.misfire_grace_time,
            replace_existing=True,
        )

    async def start(self) -> None:
        """启动调度器"""
        if self._is_running:
            logger.warning("scheduler_already_running")
            return

        # 注册所有任务
        for job in self._jobs.values():
            self._register_job(job)

        self._scheduler.start()
        self._is_running = True

        logger.info("scheduler_started", job_count=len(self._jobs))

    async def stop(self) -> None:
        """停止调度器"""
        if not self._is_running:
            return

        self._scheduler.shutdown(wait=True)
        self._is_running = False

        logger.info("scheduler_stopped")

    def get_jobs(self) -> list[dict]:
        """获取所有任务状态"""
        return [
            {
                "id": job.id,
                "name": job.name,
                "enabled": job.enabled,
                "cron": job.cron,
                "interval_seconds": job.interval_seconds,
            }
            for job in self._jobs.values()
        ]

    @property
    def is_running(self) -> bool:
        """调度器是否运行中"""
        return self._is_running


# 全局调度器实例
_global_scheduler: JobScheduler | None = None


def get_scheduler() -> JobScheduler:
    """获取全局调度器实例"""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = JobScheduler()
    return _global_scheduler


# 预定义的任务钩子
async def incremental_crawl_job() -> None:
    from src.config.settings import get_settings
    from src.crawlers.deep_crawler import DeepCrawler

    settings = get_settings()
    crawler = DeepCrawler(db_path=settings.db_path, rate_limit_rpm=settings.crawler_rate_limit_rpm)
    logger.info("incremental_crawl_job_started")
    try:
        list_count = await crawler.crawl_list(
            4, max_pages=settings.crawler_default_pages, incremental=True
        )
        detail_count = await crawler.crawl_details(announcement_type=4)
        crawler.remove_no_winner()
        logger.info(
            "incremental_crawl_job_completed", list_count=list_count, detail_count=detail_count
        )
    finally:
        await crawler.close()


async def full_crawl_job() -> None:
    from src.config.settings import get_settings
    from src.crawlers.deep_crawler import DeepCrawler

    settings = get_settings()
    crawler = DeepCrawler(db_path=settings.db_path, rate_limit_rpm=settings.crawler_rate_limit_rpm)
    logger.info("full_crawl_job_started")
    try:
        list_count = await crawler.crawl_list(4, max_pages=1000)
        detail_count = await crawler.crawl_details(announcement_type=4)
        crawler.remove_no_winner()
        logger.info("full_crawl_job_completed", list_count=list_count, detail_count=detail_count)
    finally:
        await crawler.close()


def setup_default_jobs(scheduler: JobScheduler) -> None:
    from src.config.settings import get_settings

    settings = get_settings()

    scheduler.add_job(
        id="incremental_crawl",
        name="增量抓取",
        func=incremental_crawl_job,
        cron=settings.scheduler_incremental_cron,
    )

    scheduler.add_job(
        id="full_crawl",
        name="全量抓取",
        func=full_crawl_job,
        cron=settings.scheduler_full_cron,
    )
