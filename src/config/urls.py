"""
URL配置 - 采购平台API
"""
from typing import TypedDict


class APIEndpoint(TypedDict, total=False):
    """API端点配置"""
    path: str
    method: str
    description: str


class URLConfig(TypedDict):
    """URL配置"""
    base_url: str
    api_base: str
    endpoints: dict[str, APIEndpoint]


# 采购平台 URL配置
URL_PATTERNS: dict[str, URLConfig] = {
    "production": {
        "base_url": "https://zcpt.szcg.cn",
        "api_base": "/group-tendering-website",
        "endpoints": {
            # 公告列表 - announcementType: 1=采购公告, 2=变更公告, 3=候选人公示
            "announcement_list": {
                "path": "/officialwebsite/project/page",
                "method": "GET",
                "description": "公告分页列表",
            },
            # 公告详情
            "announcement_detail": {
                "path": "/officialwebsite/project/detail/{announcementId}",
                "method": "GET",
                "description": "公告详情",
            },
            # 附件下载
            "attachment_download": {
                "path": "/officialwebsite/attachment/download/{fileId}",
                "method": "GET",
                "description": "附件下载",
            },
        },
    },
    "staging": {
        "base_url": "https://staging.zcpt.szcg.cn",
        "api_base": "/group-tendering-website",
        "endpoints": {
            "announcement_list": {
                "path": "/officialwebsite/project/page",
                "method": "GET",
                "description": "公告分页列表",
            },
        },
    },
}


def build_list_url(
    base_url: str,
    announcement_type: int = 1,
    current: int = 1,
    size: int = 20,
    tender_project_type: str = "",
    ext: str = "",
) -> str:
    """
    构建公告列表URL

    Args:
        base_url: API基础URL
        announcement_type: 公告类型 (1=采购公告, 2=变更公告, 3=候选人公示等)
        current: 页码
        size: 每页条数
        tender_project_type: 招标项目类型
        ext: 扩展筛选条件

    Returns:
        完整的列表API URL
    """
    params = [
        f"announcementType={announcement_type}",
        f"current={current}",
        f"size={size}",
    ]

    if tender_project_type:
        params.append(f"tenderProjectType={tender_project_type}")
    if ext:
        params.append(f"ext={ext}")

    return f"{base_url}/officialwebsite/project/page?{'&'.join(params)}"


def build_detail_url(base_url: str, announcement_id: str) -> str:
    """
    构建公告详情URL

    Args:
        base_url: API基础URL
        announcement_id: 公告ID

    Returns:
        完整的详情API URL
    """
    return f"{base_url}/officialwebsite/project/detail/{announcement_id}"
