"""
采集数据启动脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import get_settings
from src.utils.logger import configure_logging, get_logger
from src.crawlers.announcement import create_announcement_crawler
from src.core.scheduler import JobScheduler, setup_default_jobs

logger = get_logger(__name__)


async def run_incremental_crawl() -> None:
    """运行增量抓取"""
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)

    logger.info("starting_incremental_crawl", target=settings.api_base_url)

    crawler = create_announcement_crawler(
        target_url=f"{settings.api_base_url}/officialwebsite/project/page",
        rate_limit_rpm=settings.crawler_rate_limit_rpm,
    )

    result = await crawler.crawl_incremental(days=1)

    logger.info(
        "crawl_completed",
        success=result.success,
        items_fetched=result.items_fetched,
        items_new=result.items_new,
        items_updated=result.items_updated,
        duration_ms=result.duration_ms,
    )

    if result.errors:
        logger.error("crawl_errors", errors=result.errors)


async def run_full_crawl(max_pages: int = 1000, use_sqlite: bool = True) -> None:
    """运行全量抓取"""
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)

    logger.info("starting_full_crawl", target=settings.api_base_url, max_pages=max_pages, use_sqlite=use_sqlite)

    crawler = create_announcement_crawler(
        target_url=f"{settings.api_base_url}/officialwebsite/project/page",
        rate_limit_rpm=settings.crawler_rate_limit_rpm,
        use_sqlite=use_sqlite,
    )

    page = 1
    total_fetched = 0
    total_new = 0
    total_updated = 0

    try:
        async for result in crawler.crawl_paginated(start_page=1, max_pages=max_pages):
            total_fetched += result.items_fetched
            total_new += result.items_new
            total_updated += result.items_updated

            logger.info(
                "page_completed",
                page=page,
                items=result.items_fetched,
                new=result.items_new,
                updated=result.items_updated,
            )
            page += 1

        logger.info(
            "full_crawl_completed",
            total_pages=page - 1,
            total_fetched=total_fetched,
            total_new=total_new,
            total_updated=total_updated,
        )

        # 导出数据
        if use_sqlite:
            from src.core.sqlite_storage import SQLiteRepository
            repo = SQLiteRepository()
            print(f"\n当前数据库共 {repo.count()} 条记录")
            print(f"数据存储位置: data/announcements.db")
    finally:
        await crawler.close()


async def run_scheduled() -> None:
    """运行定时任务模式"""
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)

    logger.info("starting_scheduled_mode")

    scheduler = get_scheduler()
    setup_default_jobs(scheduler)

    await scheduler.start()

    try:
        # 运行24小时后退出（可配置）
        await asyncio.sleep(86400)
    except KeyboardInterrupt:
        logger.info("scheduler_interrupted")
    finally:
        await scheduler.stop()


def main() -> None:
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(description="中标结果采集系统")
    parser.add_argument(
        "mode",
        choices=["incremental", "full", "scheduled"],
        help="运行模式：incremental=增量抓取, full=全量抓取, scheduled=定时任务",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=1000,
        help="全量抓取的最大页数（默认1000）",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="配置文件路径",
    )

    args = parser.parse_args()

    try:
        if args.mode == "incremental":
            asyncio.run(run_incremental_crawl())
        elif args.mode == "full":
            asyncio.run(run_full_crawl(max_pages=args.max_pages))
        elif args.mode == "scheduled":
            asyncio.run(run_scheduled())
    except KeyboardInterrupt:
        logger.info("program_interrupted")
        sys.exit(0)
    except Exception as e:
        logger.error("program_error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
