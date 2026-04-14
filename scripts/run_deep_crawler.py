"""深度采集数据启动脚本 - 仅采集结果公示+有中标"""
import argparse
import asyncio

from src.crawlers.deep_crawler import DeepCrawler, ANNOUNCEMENT_TYPES


async def main():
    parser = argparse.ArgumentParser(description="中标结果采集系统")
    parser.add_argument("mode", choices=["list", "detail", "all", "test"], help="运行模式: list=仅列表, detail=仅详情, all=全部, test=测试")
    parser.add_argument("--max-pages", type=int, default=None, help="最大页数")
    parser.add_argument("--max-details", type=int, default=None, help="最大详情抓取数")
    parser.add_argument("--db", default="data/announcements_deep.db", help="数据库路径")
    parser.add_argument("--rpm", type=int, default=120, help="每分钟请求数")
    args = parser.parse_args()

    crawler = DeepCrawler(db_path=args.db, rate_limit_rpm=args.rpm)

    try:
        if args.mode == "test":
            # 测试: 抓2页结果公示 + 详情 + 删除无中标
            count = await crawler.crawl_list(4, max_pages=2)
            print(f"  结果公示: {count} 条")
            detail_count = await crawler.crawl_details(announcement_type=4, max_items=20)
            print(f"  详情抓取: {detail_count} 条")
            removed = crawler.remove_no_winner()
            if removed:
                print(f"  清理无中标记录: {removed} 条")

        elif args.mode == "list":
            # 仅列表: 抓结果公示(type=4)
            count = await crawler.crawl_list(4, max_pages=args.max_pages)
            print(f"  结果公示: {count} 条")

        elif args.mode == "detail":
            # 仅详情: 抓结果公示未获取详情的
            count = await crawler.crawl_details(announcement_type=4, max_items=args.max_details)
            print(f"  详情抓取: {count} 条")
            removed = crawler.remove_no_winner()
            if removed:
                print(f"  清理无中标记录: {removed} 条")

        elif args.mode == "all":
            # 全部: 列表 + 详情 + 删除无中标
            count = await crawler.crawl_list(4, max_pages=args.max_pages)
            print(f"  结果公示: {count} 条")
            detail_count = await crawler.crawl_details(announcement_type=4)
            print(f"  详情抓取: {detail_count} 条")
            removed = crawler.remove_no_winner()
            if removed:
                print(f"  清理无中标记录: {removed} 条")

        crawler._print_stats()

    finally:
        await crawler.close()


if __name__ == "__main__":
    asyncio.run(main())
