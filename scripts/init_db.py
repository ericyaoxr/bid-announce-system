"""
数据库初始化脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


async def init_database() -> None:
    """初始化数据库"""
    from src.config.settings import get_settings
    from src.utils.logger import configure_logging, get_logger

    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)

    logger = get_logger(__name__)
    logger.info("initializing_database", database_url=settings.database_url)

    # TODO: 实现数据库初始化逻辑
    # from sqlalchemy.ext.asyncio import create_async_engine
    # from sqlalchemy.orm import sessionmaker
    # from src.models.base import Base

    # engine = create_async_engine(settings.database_url, echo=True)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    logger.info("database_initialization_complete")


if __name__ == "__main__":
    asyncio.run(init_database())
