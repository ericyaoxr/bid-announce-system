"""
解析器单元测试 - 适配API格式
"""
from src.core.parser import DetailPageParser, JSONParser, ListPageParser


class TestListPageParser:
    """列表页解析器测试"""

    def test_parse_valid_api_response(self) -> None:
        """测试解析有效的API响应"""
        parser = ListPageParser()

        # 模拟实际API响应格式
        api_response = b'''
        {
            "code": 200,
            "msg": "\u64cd\u4f5c\u6210\u529f",
            "data": {
                "records": [
                    {
                        "announcementId": 12345,
                        "projectId": 100,
                        "projectNo": "SF2024001",
                        "announcementName": "Test Procurement Announcement",
                        "tenderMode": "1",
                        "tenderModeDesc": "Open Tendering",
                        "tenderProjectType": "1",
                        "tenderProjectTypeDesc": "Goods",
                        "releaseTime": "2024-01-15T10:00:00",
                        "releaseEndTime": "2024-01-20T18:00:00",
                        "currentStatus": 1,
                        "projectSource": 1
                    },
                    {
                        "announcementId": 12346,
                        "projectId": 101,
                        "projectNo": "SF2024002",
                        "announcementName": "Second Test Announcement",
                        "tenderMode": "2",
                        "tenderModeDesc": "Selective Tendering",
                        "tenderProjectType": "2",
                        "tenderProjectTypeDesc": "Engineering",
                        "releaseTime": "2024-01-16T10:00:00",
                        "releaseEndTime": "2024-01-21T18:00:00",
                        "currentStatus": 1,
                        "projectSource": 1
                    }
                ],
                "total": 100,
                "size": 20,
                "current": 1,
                "pages": 5
            }
        }
        '''

        result = parser.parse(api_response)

        assert result.success is True
        assert len(result.items) == 2
        assert result.total == 100
        assert result.page == 1
        assert result.page_size == 20
        assert result.total_pages == 5

    def test_parse_error_response(self) -> None:
        """测试解析错误响应"""
        parser = ListPageParser()

        error_response = b'''
        {
            "code": 500,
            "msg": "Internal Server Error",
            "data": null
        }
        '''

        result = parser.parse(error_response)

        assert result.success is False
        assert len(result.errors) > 0

    def test_parse_invalid_json(self) -> None:
        """测试解析无效JSON"""
        parser = ListPageParser()
        result = parser.parse(b"not valid json")

        assert result.success is False

    def test_parse_to_announcements(self) -> None:
        """测试转换为Announcement对象"""
        parser = ListPageParser()

        api_response = b'''
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
        '''

        announcements, errors = parser.parse_to_announcements(api_response, "https://zcpt.szcg.cn")

        assert len(announcements) == 1
        assert len(errors) == 0
        assert announcements[0].id == "12345"
        assert announcements[0].title == "Test Announcement"
        assert announcements[0].project_no == "SF2024001"


class TestJSONParser:
    """JSON解析器测试"""

    def test_parse_simple_list(self) -> None:
        """测试解析简单列表"""
        parser = JSONParser()
        result = parser.parse(b'[{"id": "1"}, {"id": "2"}]')

        assert result.success is True
        assert len(result.items) == 2

    def test_parse_nested_data(self) -> None:
        """测试解析嵌套数据"""
        parser = JSONParser()
        result = parser.parse(b'{"data": [{"id": "1"}], "total": 1}')

        assert result.success is True
        assert len(result.items) == 1

    def test_parse_empty_data(self) -> None:
        """测试解析空数据"""
        parser = JSONParser()
        result = parser.parse(b'{"data": []}')

        assert result.success is True
        assert len(result.items) == 0


class TestDetailPageParser:
    """详情页解析器测试"""

    def test_parse_detail_html(self) -> None:
        """测试解析HTML详情页"""
        parser = DetailPageParser(
            selectors={
                "title": "h1::text",
                "content": "div.content::text",
                "publish_date": "span.publish-date::attr(data-time)",
            }
        )

        html = """
        <html>
        <body>
            <h1>Detailed Announcement Title</h1>
            <div class="content">This is the detailed content...</div>
            <span class="publish-date" data-time="2024-01-15"></span>
        </body>
        </html>
        """

        result = parser.parse(html)

        assert result.success is True
        assert len(result.items) == 1
        assert result.items[0]["title"] == "Detailed Announcement Title"
        assert result.items[0]["content"] == "This is the detailed content..."

    def test_parse_empty_html(self) -> None:
        """测试解析空HTML"""
        parser = DetailPageParser(selectors={"title": "h1::text"})
        result = parser.parse("<html><body></body></html>")

        assert result.success is True
        assert len(result.items) == 0
