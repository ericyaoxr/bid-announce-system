from src.crawlers.deep_crawler import DeepCrawler
from src.crawlers.registry import register_crawler

register_crawler(
    DeepCrawler,
    site_id="szcg",
    site_name="特区建工集团采购平台",
    base_url="https://zcpt.szcg.cn",
    description="特区建工集团采购平台，支持招标/变更/候选人/结果公示/邀请函采集",
    enabled=True,
)
