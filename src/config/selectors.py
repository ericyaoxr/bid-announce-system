"""
选择器配置 - 采购平台API字段映射
"""

from typing import TypedDict


class APIFieldMapping(TypedDict):
    """API字段映射配置"""

    # API响应字段名
    api_field: str
    # 对应的数据模型字段
    model_field: str
    # 是否必填
    required: bool
    # 默认值（可选）
    default: str | None
    # 字段描述
    description: str


# 公告列表API字段映射
ANNOUNCEMENT_LIST_MAPPING: dict[str, APIFieldMapping] = {
    "announcementId": {
        "api_field": "announcementId",
        "model_field": "id",
        "required": True,
        "default": None,
        "description": "公告ID，唯一标识",
    },
    "projectNo": {
        "api_field": "projectNo",
        "model_field": "project_no",
        "required": True,
        "default": None,
        "description": "项目编号",
    },
    "announcementName": {
        "api_field": "announcementName",
        "model_field": "title",
        "required": True,
        "default": None,
        "description": "公告名称/标题",
    },
    "tenderMode": {
        "api_field": "tenderMode",
        "model_field": "tender_mode",
        "required": False,
        "default": "未知",
        "description": "招标方式代码",
    },
    "tenderModeDesc": {
        "api_field": "tenderModeDesc",
        "model_field": "tender_mode_desc",
        "required": False,
        "default": "未知",
        "description": "招标方式描述（如：公开招标、竞价）",
    },
    "tenderProjectType": {
        "api_field": "tenderProjectType",
        "model_field": "project_type_code",
        "required": False,
        "default": None,
        "description": "招标项目类型代码",
    },
    "tenderProjectTypeDesc": {
        "api_field": "tenderProjectTypeDesc",
        "model_field": "category",
        "required": False,
        "default": "未知",
        "description": "招标项目类型描述（工程类/货物类/服务类）",
    },
    "releaseTime": {
        "api_field": "releaseTime",
        "model_field": "publish_date",
        "required": True,
        "default": None,
        "description": "发布时间",
    },
    "releaseEndTime": {
        "api_field": "releaseEndTime",
        "model_field": "deadline",
        "required": False,
        "default": None,
        "description": "发布截止时间",
    },
    "currentStatus": {
        "api_field": "currentStatus",
        "model_field": "status_code",
        "required": False,
        "default": None,
        "description": "当前状态代码",
    },
    "projectId": {
        "api_field": "projectId",
        "model_field": "project_id",
        "required": False,
        "default": None,
        "description": "项目ID",
    },
    "projectSource": {
        "api_field": "projectSource",
        "model_field": "project_source",
        "required": False,
        "default": None,
        "description": "项目来源",
    },
}


# 公告类型枚举映射
ANNOUNCEMENT_TYPE_MAPPING: dict[int, str] = {
    1: "采购公告",
    2: "变更公告",
    3: "候选人公示",
    4: "结果公示",
    5: "邀请函",
}


# 招标项目类型映射
PROJECT_TYPE_MAPPING: dict[str, str] = {
    "D01": "货物类",
    "D02": "工程类",
    "D03": "服务类",
    "A01": "工程类",
    "A02": "货物类",
    "A03": "服务类",
}


# 状态码映射
STATUS_CODE_MAPPING: dict[int, str] = {
    27: "报名中",
    28: "待开标",
    29: "已开标",
    30: "已结束",
}
