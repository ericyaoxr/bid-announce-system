"""
采集数据集成测试 - 适配当前实现
"""

from src.core.parser import JSONParser, ListPageParser
from src.crawlers.announcement import CrawlerConfig, CrawlResult


class TestListPageParserIntegration:
    """ListPageParser集成测试"""

    def test_parse_real_api_format(self) -> None:
        """测试解析实际API格式"""
        parser = ListPageParser()

        # 模拟实际API响应
        api_response = b"""
        {
            "code": 200,
            "msg": "Success",
            "data": {
                "records": [
                    {
                        "announcementId": 12345,
                        "projectId": 100,
                        "projectNo": "SF2024001",
                        "announcementName": "Shenzhen Government Procurement Test",
                        "tenderMode": "1",
                        "tenderModeDesc": "Open Tendering",
                        "tenderProjectType": "1",
                        "tenderProjectTypeDesc": "Goods",
                        "releaseTime": "2024-01-15T10:00:00",
                        "releaseEndTime": "2024-01-20T18:00:00",
                        "currentStatus": 1,
                        "projectSource": 1
                    }
                ],
                "total": 28715,
                "size": 20,
                "current": 1,
                "pages": 1436
            }
        }
        """

        result = parser.parse(api_response)

        assert result.success is True
        assert result.total == 28715
        assert result.page == 1
        assert result.page_size == 20
        assert result.total_pages == 1436
        assert len(result.items) == 1
        assert result.items[0]["announcementId"] == 12345

    def test_parse_to_announcements_real_format(self) -> None:
        """测试转换为Announcement对象"""
        parser = ListPageParser()

        api_response = b"""
        {
            "code": 200,
            "msg": "Success",
            "data": {
                "records": [
                    {
                        "announcementId": 12345,
                        "projectId": 100,
                        "projectNo": "SF2024001",
                        "announcementName": "Test Announcement",
                        "tenderMode": "1",
                        "tenderModeDesc": "Open Tendering",
                        "tenderProjectType": "1",
                        "tenderProjectTypeDesc": "Goods",
                        "releaseTime": "2024-01-15T10:00:00",
                        "releaseEndTime": "2024-01-20T18:00:00",
                        "currentStatus": 1,
                        "projectSource": 1
                    }
                ],
                "total": 1,
                "size": 20,
                "current": 1,
                "pages": 1
            }
        }
        """

        announcements, errors = parser.parse_to_announcements(api_response, "https://zcpt.szcg.cn")

        assert len(announcements) == 1
        assert len(errors) == 0
        assert announcements[0].id == "12345"
        assert announcements[0].title == "Test Announcement"
        assert announcements[0].project_no == "SF2024001"
        assert announcements[0].category == "Goods"


class TestCrawlerConfig:
    """CrawlerConfig测试"""

    def test_default_config(self) -> None:
        """测试默认配置"""
        config = CrawlerConfig(target_url="https://example.com")

        assert config.max_retries == 3
        assert config.timeout == 30.0
        assert config.rate_limit_rpm == 60
        assert config.batch_size == 20
        assert config.base_url == "https://zcpt.szcg.cn"

    def test_custom_config(self) -> None:
        """测试自定义配置"""
        config = CrawlerConfig(
            target_url="https://example.com",
            max_retries=5,
            timeout=60.0,
            rate_limit_rpm=30,
            batch_size=50,
            base_url="https://custom.com",
        )

        assert config.max_retries == 5
        assert config.timeout == 60.0
        assert config.rate_limit_rpm == 30
        assert config.batch_size == 50
        assert config.base_url == "https://custom.com"


class TestCrawlResult:
    """CrawlResult测试"""

    def test_crawl_result_success(self) -> None:
        """测试成功结果"""
        result = CrawlResult(
            success=True,
            items_fetched=10,
            items_new=5,
            items_updated=3,
            duration_ms=1500,
            page=1,
            total_pages=100,
            total_records=2000,
        )

        assert result.success is True
        assert result.items_fetched == 10
        assert result.items_new == 5
        assert result.items_updated == 3
        assert result.errors == []

    def test_crawl_result_with_errors(self) -> None:
        """测试带错误的结果"""
        result = CrawlResult(
            success=False,
            items_fetched=5,
            errors=["Network timeout", "Parse error"],
            page=1,
        )

        assert result.success is False
        assert len(result.errors) == 2

    def test_crawl_result_defaults(self) -> None:
        """测试默认值"""
        result = CrawlResult(success=True)

        assert result.items_fetched == 0
        assert result.items_new == 0
        assert result.items_updated == 0
        assert result.duration_ms == 0
        assert result.errors == []
        assert result.page is None
        assert result.total_pages is None


class TestJSONParserIntegration:
    """JSONParser集成测试"""

    def test_parse_paginated_response(self) -> None:
        """测试解析分页响应"""
        parser = JSONParser()

        # JSONParser looks for list at top level or nested under common keys
        response = b"""
        {
            "items": [
                {"id": "1", "name": "Item 1"},
                {"id": "2", "name": "Item 2"}
            ],
            "total": 100,
            "page": 1,
            "pageSize": 20
        }
        """

        result = parser.parse(response)

        assert result.success is True
        assert len(result.items) == 2
        assert result.items[0]["id"] == "1"

    def test_parse_simple_list(self) -> None:
        """测试解析简单列表"""
        parser = JSONParser()
        result = parser.parse(b'[{"id": 1}, {"id": 2}, {"id": 3}]')

        assert result.success is True
        assert len(result.items) == 3
