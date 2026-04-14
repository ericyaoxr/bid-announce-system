"""深度采集数据 - 抓取5种公告类型 + 详情页（中标人/金额等）"""
from __future__ import annotations

import asyncio
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from src.utils.logger import get_logger

logger = get_logger(__name__)

BASE_URL = "https://zcpt.szcg.cn/group-tendering-website/officialwebsite"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://zcpt.szcg.cn/announcement",
}

# 公告类型映射
ANNOUNCEMENT_TYPES = {
    1: "招标公告",
    2: "变更公告",
    3: "候选人公示",
    4: "结果公示",
    5: "邀请函",
}


class DeepCrawler:
    """深度采集数据 - 列表页 + 详情页"""

    def __init__(self, db_path: str = "data/announcements_deep.db", rate_limit_rpm: int = 120):
        self.db_path = db_path
        self.rate_limit_rpm = rate_limit_rpm
        self.client: httpx.AsyncClient | None = None
        self._request_interval = 60.0 / rate_limit_rpm
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # 确保联系人/联系电话字段存在（兼容旧数据库）
        self._ensure_columns()

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id TEXT PRIMARY KEY,
                project_id INTEGER,
                project_no TEXT,
                title TEXT,
                announcement_type INTEGER,
                announcement_type_desc TEXT,
                tender_mode TEXT,
                tender_mode_desc TEXT,
                category TEXT,
                category_code TEXT,
                publish_date TEXT,
                deadline TEXT,
                current_status INTEGER,
                project_source INTEGER,
                source_url TEXT,

                -- 详情字段
                purchase_control_price REAL,
                bid_price REAL,
                winning_bidders TEXT,
                candidate_info TEXT,
                change_records TEXT,
                project_address TEXT,
                project_region TEXT,
                fund_source TEXT,
                tender_organize_form TEXT,
                purchase_process TEXT,
                grade_method TEXT,
                qualification_method TEXT,
                quotation_method TEXT,
                is_security_deposit INTEGER,
                is_consortium_bidding TEXT,
                is_eval_separate INTEGER,
                package_name TEXT,
                package_category TEXT,
                tenderer_name TEXT,
                tenderer_contact TEXT,
                tenderer_phone TEXT,
                tenderer_address TEXT,
                tender_content TEXT,
                engineering_name TEXT,

                -- 元数据
                detail_fetched INTEGER DEFAULT 0,
                raw_list_data TEXT,
                raw_detail_data TEXT,
                content_hash TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # 创建索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON announcements(announcement_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_publish_date ON announcements(publish_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON announcements(category)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_project_id ON announcements(project_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_detail_fetched ON announcements(detail_fetched)")
        conn.commit()
        conn.close()
        logger.info("database_initialized", db_path=self.db_path)

    @staticmethod
    def _extract_mobile(phone: str | None) -> str | None:
        """从电话号码中提取手机号（1开头11位数字）"""
        if not phone:
            return None
        phone_str = str(phone).strip()
        # 匹配中国大陆手机号: 1开头，第二位3-9，共11位
        match = re.search(r'1[3-9]\d{9}', phone_str)
        return match.group(0) if match else None

    def _ensure_columns(self):
        """确保数据库有最新字段（兼容旧版本）"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("SELECT tenderer_contact FROM announcements LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute("ALTER TABLE announcements ADD COLUMN tenderer_contact TEXT")
        try:
            conn.execute("SELECT tenderer_phone FROM announcements LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute("ALTER TABLE announcements ADD COLUMN tenderer_phone TEXT")
        conn.commit()
        conn.close()

    async def _ensure_client(self):
        if self.client is None:
            self.client = httpx.AsyncClient(
                headers=HEADERS,
                timeout=30,
                follow_redirects=True,
            )

    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    async def _request(self, url: str, params: dict | None = None) -> dict | None:
        """带限流的请求"""
        await self._ensure_client()
        try:
            resp = await self.client.get(url, params=params)
            await asyncio.sleep(self._request_interval)
            if resp.status_code == 200:
                return resp.json()
            else:
                logger.warning("request_failed", url=url, status=resp.status_code)
                return None
        except Exception as e:
            logger.error("request_error", url=url, error=str(e))
            return None

    # ===== 列表页抓取 =====

    async def fetch_list_page(self, announcement_type: int, page: int = 1, size: int = 20) -> tuple[list[dict], int]:
        """抓取列表页"""
        data = await self._request(
            f"{BASE_URL}/project/page",
            params={"announcementType": str(announcement_type), "current": str(page), "size": str(size), "tenderProjectType": "", "ext": ""},
        )
        if not data or not data.get("data"):
            return [], 0

        records = data["data"].get("records", [])
        total = data["data"].get("total", 0)
        return records, total

    async def crawl_list(self, announcement_type: int, max_pages: int | None = None, size: int = 20, incremental: bool = False) -> int:
        """抓取指定类型的列表页
        
        Args:
            announcement_type: 公告类型
            max_pages: 最大页数
            size: 每页条数
            incremental: 是否增量模式（遇到已存在记录即停止翻页）
        """
        type_name = ANNOUNCEMENT_TYPES.get(announcement_type, f"类型{announcement_type}")
        logger.info("crawl_list_start", type=type_name, announcement_type=announcement_type, incremental=incremental)

        # 先获取第一页确定总页数
        records, total = await self.fetch_list_page(announcement_type, 1, size)
        if not records:
            logger.info("crawl_list_empty", type=type_name)
            return 0

        total_pages = (total + size - 1) // size
        if max_pages:
            total_pages = min(total_pages, max_pages)

        count = 0
        # 保存第一页
        new_count = self._save_list_records(records, announcement_type)
        count += new_count

        # 增量模式：如果第一页全部是已有记录，说明没有新数据，直接返回
        if incremental and new_count == 0:
            logger.info("crawl_list_incremental_no_new", type=type_name, message="无新数据，跳过")
            return 0

        # 继续抓取后续页
        for page in range(2, total_pages + 1):
            records, _ = await self.fetch_list_page(announcement_type, page, size)
            if not records:
                break
            new_count = self._save_list_records(records, announcement_type)
            count += new_count

            # 增量模式：如果某页全部是已有记录，说明后续页也都是旧数据，停止
            if incremental and new_count == 0:
                logger.info("crawl_list_incremental_stop", type=type_name, page=page, message="遇到全旧页，停止翻页")
                break

            if page % 50 == 0:
                logger.info("crawl_list_progress", type=type_name, page=page, total_pages=total_pages, count=count)

        logger.info("crawl_list_done", type=type_name, count=count, total=total)
        return count

    def _save_list_records(self, records: list[dict], announcement_type: int) -> int:
        """保存列表页记录（增量：已有记录不覆盖，保留详情数据）"""
        conn = sqlite3.connect(self.db_path)
        count = 0
        now = datetime.now(timezone.utc).isoformat()

        for r in records:
            aid = str(r.get("announcementId", ""))
            if not aid:
                continue

            try:
                # INSERT OR IGNORE: 主键冲突时忽略，保留已有记录（含详情数据）
                # 这样增量采集不会覆盖已抓取的详情
                cursor = conn.execute("""
                    INSERT OR IGNORE INTO announcements (
                        id, project_id, project_no, title,
                        announcement_type, announcement_type_desc,
                        tender_mode, tender_mode_desc,
                        category, category_code,
                        publish_date, deadline,
                        current_status, project_source,
                        source_url, raw_list_data,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    aid,
                    r.get("projectId"),
                    r.get("projectNo"),
                    r.get("announcementName"),
                    announcement_type,
                    ANNOUNCEMENT_TYPES.get(announcement_type, ""),
                    r.get("tenderMode"),
                    r.get("tenderModeDesc"),
                    r.get("tenderProjectTypeDesc", "").replace("类", "") if r.get("tenderProjectTypeDesc") else None,
                    r.get("tenderProjectType"),
                    r.get("releaseTime"),
                    r.get("releaseEndTime"),
                    r.get("currentStatus"),
                    r.get("projectSource"),
                    f"https://zcpt.szcg.cn/announcement/{r.get('projectId', '')}?projectSource=1",
                    json.dumps(r, ensure_ascii=False),
                    now,
                    now,
                ))
                if cursor.rowcount > 0:
                    count += 1
            except Exception as e:
                logger.error("save_record_error", id=aid, error=str(e))

        conn.commit()
        conn.close()
        return count

    # ===== 详情页抓取 =====

    async def fetch_detail(self, project_id: int, announcement_type: int) -> dict | None:
        """抓取详情页"""
        if announcement_type == 4:
            # 结果公示
            return await self._fetch_result_detail(project_id)
        elif announcement_type == 3:
            # 候选人公示
            return await self._fetch_candidate_detail(project_id)
        elif announcement_type == 2:
            # 变更公告
            return await self._fetch_change_detail(project_id)
        else:
            # 招标公告/邀请函 - 基本信息
            return await self._fetch_project_detail(project_id)

    async def _fetch_result_detail(self, project_id: int) -> dict | None:
        """抓取结果公示详情 - 含中标人/金额"""
        data = await self._request(f"{BASE_URL}/project/resultInfoDetail/{project_id}")
        if not data or not data.get("data"):
            return None
        return data["data"]

    async def _fetch_candidate_detail(self, project_id: int) -> dict | None:
        """抓取候选人公示详情"""
        # 候选人详情API可能和结果公示相同
        data = await self._request(f"{BASE_URL}/project/resultInfoDetail/{project_id}")
        if not data or not data.get("data"):
            return None
        return data["data"]

    async def _fetch_change_detail(self, project_id: int) -> dict | None:
        """抓取变更公告详情"""
        data = await self._request(f"{BASE_URL}/project/announcementChangeDetail/{project_id}")
        if not data or not data.get("data"):
            return None
        return data["data"]

    async def _fetch_project_detail(self, project_id: int) -> dict | None:
        """抓取招标公告/邀请函详情"""
        # 尝试resultInfoDetail（包含项目完整信息）
        data = await self._request(f"{BASE_URL}/project/resultInfoDetail/{project_id}")
        if data and data.get("data"):
            return data["data"]
        return None

    async def crawl_details(self, batch_size: int = 100, max_items: int | None = None, announcement_type: int | None = None) -> int:
        """抓取所有未获取详情的记录
        
        Args:
            batch_size: 批次大小
            max_items: 最大条数
            announcement_type: 仅抓取指定公告类型的详情（如4=结果公示）
        """
        conn = sqlite3.connect(self.db_path)

        query = "SELECT id, project_id, announcement_type FROM announcements WHERE detail_fetched = 0 AND project_id IS NOT NULL"
        if announcement_type:
            query += f" AND announcement_type = {announcement_type}"
        if max_items:
            query += f" LIMIT {max_items}"

        rows = conn.execute(query).fetchall()
        conn.close()

        total = len(rows)
        logger.info("crawl_details_start", total=total)
        count = 0

        for i, (aid, pid, atype) in enumerate(rows):
            if not pid:
                continue

            detail = await self.fetch_detail(pid, atype)
            if detail:
                self._save_detail(aid, pid, atype, detail)
                count += 1

            if (i + 1) % 50 == 0:
                logger.info("crawl_details_progress", done=i + 1, total=total, saved=count)

        logger.info("crawl_details_done", total=total, saved=count)
        return count

    def _save_detail(self, aid: str, project_id: int, announcement_type: int, detail):
        """保存详情数据（兼容 dict 和 list 格式）"""
        conn = sqlite3.connect(self.db_path)
        now = datetime.now(timezone.utc).isoformat()

        # 处理变更公告返回 list 的情况
        if isinstance(detail, list):
            # 变更公告: detail 是变更记录列表
            pi = {}
            winning_bidders = []
            ppr = None
            change_records = []
            for change in detail:
                if isinstance(change, dict):
                    cr = {
                        "change_person": change.get("changePerson"),
                        "change_time": change.get("changeTime"),
                        "reason": change.get("reason"),
                        "details": change.get("recordDetailVOS", []),
                    }
                    change_records.append(cr)
        elif isinstance(detail, dict):
            # 标准格式: detail 包含 projectInfo + projectPublicityRecordVO
            pi = detail.get("projectInfo") or {}
            if not isinstance(pi, dict):
                pi = {}

            # 提取中标人信息
            winning_bidders = []
            ppr = detail.get("projectPublicityRecordVO")
            if ppr and isinstance(ppr, dict) and ppr.get("winningBidders"):
                for wb in ppr["winningBidders"]:
                    winning_bidders.append({
                        "supplier_name": wb.get("supplierName"),
                        "bid_amount": wb.get("candidateBidPrice") or wb.get("bidPrice"),
                        "is_winning": wb.get("isBid"),
                        "rank": wb.get("sort"),
                        "supplier_id": wb.get("supplierId"),
                        "social_credit_code": wb.get("socialCreditCode"),
                        "is_joint": wb.get("isJoint"),
                        "is_be_noticed": wb.get("isBeNoticed"),
                    })

            # 提取变更记录（dict格式中也可能有）
            change_records = []
        else:
            # 未知格式，跳过
            logger.warning("save_detail_unknown_format", aid=aid, dtype=type(detail).__name__)
            conn.close()
            return

        try:
            conn.execute("""
                UPDATE announcements SET
                    purchase_control_price = ?,
                    bid_price = ?,
                    winning_bidders = ?,
                    candidate_info = ?,
                    change_records = ?,
                    project_address = ?,
                    project_region = ?,
                    fund_source = ?,
                    tender_organize_form = ?,
                    purchase_process = ?,
                    grade_method = ?,
                    qualification_method = ?,
                    quotation_method = ?,
                    is_security_deposit = ?,
                    is_consortium_bidding = ?,
                    is_eval_separate = ?,
                    package_name = ?,
                    package_category = ?,
                    tenderer_name = ?,
                    tenderer_contact = ?,
                    tenderer_phone = ?,
                    tenderer_address = ?,
                    tender_content = ?,
                    engineering_name = ?,
                    detail_fetched = 1,
                    raw_detail_data = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                pi.get("purchaseControlPrice"),
                pi.get("bidPrice"),
                json.dumps(winning_bidders, ensure_ascii=False) if winning_bidders else None,
                json.dumps(ppr, ensure_ascii=False) if ppr else None,
                json.dumps(change_records, ensure_ascii=False) if change_records else None,
                pi.get("address"),
                pi.get("districtDesc") or pi.get("regionCode"),
                pi.get("fundSourceDesc"),
                pi.get("tenderOrganizeFormDesc"),
                pi.get("purchaseProcessDesc"),
                pi.get("gradeMethodDesc"),
                pi.get("qualificationMethodDesc"),
                pi.get("quotationMethodDesc"),
                pi.get("isSecurityDeposit"),
                pi.get("isConsortiumBidding"),
                pi.get("isEvalSeparate"),
                pi.get("packageName"),
                pi.get("packageLatterTypeDesc"),
                pi.get("tenderCompanyName") or pi.get("enterpriseName"),
                pi.get("connector"),
                DeepCrawler._extract_mobile(pi.get("foreignContactPhone")),
                pi.get("companyAddress"),
                pi.get("tendererContent"),
                pi.get("engineeringName"),
                json.dumps(detail, ensure_ascii=False),
                now,
                aid,
            ))
            conn.commit()

            # 日志中标信息
            if winning_bidders:
                for wb in winning_bidders:
                    if wb.get("is_winning") or wb.get("supplier_name"):
                        logger.info("winning_bidder_found",
                                    aid=aid, supplier=wb.get("supplier_name"),
                                    amount=wb.get("bid_amount"),
                                    is_winning=wb.get("is_winning"))

        except Exception as e:
            logger.error("save_detail_error", aid=aid, error=str(e))
        finally:
            conn.close()

    # ===== 全量抓取 =====

    async def crawl_all(self, max_pages_per_type: int | None = None):
        """全量抓取 - 列表页 + 详情页"""
        logger.info("crawl_all_start")

        # Step 1: 抓取所有类型的列表页
        for atype in [1, 2, 3, 4, 5]:
            count = await self.crawl_list(atype, max_pages=max_pages_per_type)
            logger.info("list_type_done", type=ANNOUNCEMENT_TYPES.get(atype), count=count)

        # Step 2: 抓取详情页
        detail_count = await self.crawl_details()
        logger.info("crawl_all_done", detail_count=detail_count)

    async def crawl_test(self, pages: int = 2):
        """测试抓取"""
        logger.info("crawl_test_start", pages=pages)

        # 先抓结果公示(type=4)和候选人公示(type=3)的列表
        for atype in [4, 3, 1]:
            count = await self.crawl_list(atype, max_pages=pages)
            logger.info("test_list_done", type=ANNOUNCEMENT_TYPES.get(atype), count=count)

        # 抓详情
        detail_count = await self.crawl_details(max_items=20)
        logger.info("crawl_test_done", detail_count=detail_count)

        # 统计
        self._print_stats()

    def _print_stats(self):
        """打印统计信息"""
        conn = sqlite3.connect(self.db_path)

        total = conn.execute("SELECT COUNT(*) FROM announcements").fetchone()[0]
        with_detail = conn.execute("SELECT COUNT(*) FROM announcements WHERE detail_fetched = 1").fetchone()[0]
        with_winner = conn.execute("SELECT COUNT(*) FROM announcements WHERE winning_bidders IS NOT NULL AND winning_bidders != '[]'").fetchone()[0]

        print(f"\n{'=' * 50}")
        print(f"  数据统计")
        print(f"{'=' * 50}")
        print(f"  总记录数: {total}")
        print(f"  已获取详情: {with_detail}")
        print(f"  含中标人: {with_winner}")

        # 按类型统计
        print(f"\n  按类型统计:")
        for row in conn.execute("SELECT announcement_type_desc, COUNT(*) FROM announcements GROUP BY announcement_type ORDER BY COUNT(*) DESC"):
            print(f"    {row[0]}: {row[1]}")

        # 中标人示例
        print(f"\n  中标人示例:")
        for row in conn.execute("SELECT id, title, winning_bidders FROM announcements WHERE winning_bidders IS NOT NULL AND winning_bidders != '[]' LIMIT 5"):
            wbs = json.loads(row[2])
            for wb in wbs:
                if wb.get("supplier_name"):
                    print(f"    [{row[0]}] {wb['supplier_name']} - {wb.get('bid_amount', 'N/A')}")

        conn.close()

    def remove_no_winner(self) -> int:
        """删除已获取详情但无中标人的记录（结果公示专用）
        
        Returns:
            删除的记录数
        """
        conn = sqlite3.connect(self.db_path)
        # 删除：已获取详情 + 无中标人（winning_bidders为空或[]）
        cursor = conn.execute("""
            DELETE FROM announcements 
            WHERE detail_fetched = 1 
            AND (winning_bidders IS NULL OR winning_bidders = '' OR winning_bidders = '[]')
        """)
        removed = cursor.rowcount
        conn.commit()
        conn.close()
        if removed > 0:
            logger.info("removed_no_winner", count=removed)
        return removed
