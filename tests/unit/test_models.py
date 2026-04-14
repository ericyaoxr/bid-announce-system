"""
Pydantic模型单元测试
"""
from datetime import UTC, datetime, timedelta

from src.models.announcement import Announcement, AnnouncementCreate
from src.models.enums import AnnouncementType, Category


class TestAnnouncement:
    """Announcement模型测试"""

    def test_create_announcement(self) -> None:
        """测试创建公告"""
        announcement = Announcement(
            id="test-123",
            project_no="SF2024001",
            tender_mode="1",
            tender_mode_desc="公开招标",
            title="测试公告",
            category="货物",
            publish_date=datetime.now(UTC),
            url="https://example.com/123",
            content_hash="abc123",
        )

        assert announcement.id == "test-123"
        assert announcement.title == "测试公告"
        assert announcement.tender_mode_desc == "公开招标"
        assert announcement.source == "zcpt.szcg.cn"  # 默认值

    def test_announcement_url_validation(self) -> None:
        """测试URL验证"""
        # 使用正确的URL格式
        announcement = Announcement(
            id="test-124",
            project_no="SF2024002",
            tender_mode="1",
            tender_mode_desc="公开招标",
            title="测试",
            category="货物",
            publish_date=datetime.now(UTC),
            url="https://example.com/123",
            content_hash="abc124",
        )
        assert str(announcement.url) == "https://example.com/123"

    def test_announcement_compute_hash(self) -> None:
        """测试哈希计算"""
        announcement = Announcement(
            id="test-125",
            project_no="SF2024003",
            tender_mode="1",
            tender_mode_desc="公开招标",
            title="测试公告",
            category="货物",
            publish_date=datetime.now(UTC),
            url="https://example.com/125",
            content_hash="abc125",
        )
        hash1 = announcement.compute_self_hash()
        hash2 = announcement.compute_self_hash()

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 produces 64 hex characters

    def test_announcement_is_expired(self) -> None:
        """测试过期判断"""
        # 未过期的公告 - 使用固定的未来日期
        announcement = Announcement(
            id="test-126",
            project_no="SF2024004",
            tender_mode="1",
            tender_mode_desc="公开招标",
            title="测试",
            category="货物",
            publish_date=datetime.now(UTC),
            deadline=datetime(2099, 12, 31, 12, 0, 0, tzinfo=UTC),  # 未来日期
            url="https://example.com/126",
            content_hash="abc126",
        )
        assert announcement.is_expired is False

        # 已过期的公告
        announcement.deadline = datetime(2020, 1, 1, 12, 0, 0, tzinfo=UTC)
        assert announcement.is_expired is True

        # 无截止日期
        announcement.deadline = None
        assert announcement.is_expired is False

    def test_announcement_days_until_deadline(self) -> None:
        """测试距离截止天数"""
        announcement = Announcement(
            id="test-127",
            project_no="SF2024005",
            tender_mode="1",
            tender_mode_desc="公开招标",
            title="测试",
            category="货物",
            publish_date=datetime.now(UTC),
            deadline=datetime.now(UTC) + timedelta(days=30),
            url="https://example.com/127",
            content_hash="abc127",
        )
        assert announcement.days_until_deadline is not None
        assert 29 <= announcement.days_until_deadline <= 30

    def test_announcement_to_dict(self) -> None:
        """测试转换为字典"""
        announcement = Announcement(
            id="test-128",
            project_no="SF2024006",
            tender_mode="1",
            tender_mode_desc="公开招标",
            title="测试公告",
            category="货物",
            publish_date=datetime.now(UTC),
            url="https://example.com/128",
            content_hash="abc128",
        )

        data = announcement.to_dict()
        assert isinstance(data, dict)
        assert data["id"] == "test-128"
        assert data["title"] == "测试公告"
        assert data["project_no"] == "SF2024006"

    def test_announcement_from_api_response(self) -> None:
        """测试从API响应创建模型"""
        api_data = {
            "announcementId": 12345,
            "projectId": 100,
            "projectNo": "SF2024001",
            "announcementName": "测试采购公告",
            "tenderMode": "1",
            "tenderModeDesc": "公开招标",
            "tenderProjectType": "1",
            "tenderProjectTypeDesc": "货物类",
            "releaseTime": "2024-01-15T10:00:00",
            "releaseEndTime": "2024-01-20T18:00:00",
            "currentStatus": 1,
            "projectSource": 1,
        }

        announcement = Announcement.from_api_response(api_data, "https://zcpt.szcg.cn")

        assert announcement.id == "12345"
        assert announcement.title == "测试采购公告"
        assert announcement.project_no == "SF2024001"
        assert announcement.tender_mode_desc == "公开招标"
        assert announcement.category == "货物"
        assert announcement.content_hash != ""


class TestAnnouncementCreate:
    """AnnouncementCreate模型测试"""

    def test_create_with_minimal_fields(self) -> None:
        """测试最小字段创建"""
        create = AnnouncementCreate(
            title="测试公告",
            announcement_type=1,
            category="货物",
            publish_date=datetime.now(),
            url="https://example.com/123",
        )

        assert create.title == "测试公告"
        assert create.deadline is None
        assert create.org_name is None

    def test_create_with_all_fields(self) -> None:
        """测试完整字段创建"""
        create = AnnouncementCreate(
            title="完整公告",
            announcement_type=1,
            category="工程",
            publish_date=datetime.now(),
            deadline=datetime.now(),
            url="https://example.com/456",
            org_name="测试单位",
            contact_info="010-12345678",
            raw_content="这是原始内容",
        )

        assert create.org_name == "测试单位"
        assert create.contact_info == "010-12345678"
        assert create.raw_content == "这是原始内容"


class TestAnnouncementType:
    """AnnouncementType枚举测试"""

    def test_from_string(self) -> None:
        """测试从字符串解析"""
        assert AnnouncementType.from_string("采购公告") == AnnouncementType.PROCUREMENT
        assert AnnouncementType.from_string("变更公告") == AnnouncementType.CHANGE
        assert AnnouncementType.from_string("候选人公示") == AnnouncementType.CANDIDATE

    def test_from_string_unknown(self) -> None:
        """测试未知类型"""
        assert AnnouncementType.from_string("未知类型") == AnnouncementType.OTHER


class TestCategory:
    """Category枚举测试"""

    def test_from_string(self) -> None:
        """测试从字符串解析"""
        assert Category.from_string("工程") == Category.ENGINEERING
        assert Category.from_string("货物") == Category.GOODS
        assert Category.from_string("服务") == Category.SERVICE

    def test_from_string_unknown(self) -> None:
        """测试未知类别"""
        assert Category.from_string("未知类别") == Category.OTHER
