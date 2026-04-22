import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from src.api.deps import AdminUser, DbSession
from src.core.notifier import NotificationService
from src.db.models import NotificationConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["通知推送"])


class NotificationConfigCreate(BaseModel):
    name: str
    ntype: str  # webhook, feishu, dingtalk, wecom, email
    enabled: bool = True
    config: dict


class NotificationConfigUpdate(BaseModel):
    name: str | None = None
    ntype: str | None = None
    enabled: bool | None = None
    config: dict | None = None


class NotificationTestRequest(BaseModel):
    title: str = "测试通知"
    content: str = "这是一条测试通知，用于验证配置是否正确。"


@router.get("/configs")
async def list_configs(db: DbSession) -> list[dict]:
    result = await db.execute(
        select(NotificationConfig).order_by(NotificationConfig.created_at.desc())
    )
    configs = result.scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "ntype": c.ntype,
            "enabled": c.enabled,
            "config": json.loads(c.config),
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in configs
    ]


@router.post("/configs")
async def create_config(req: NotificationConfigCreate, db: DbSession, _admin: AdminUser) -> dict:
    from uuid import uuid4

    config_id = f"nc_{uuid4().hex[:8]}"
    config = NotificationConfig(
        id=config_id,
        name=req.name,
        ntype=req.ntype,
        enabled=req.enabled,
        config=json.dumps(req.config),
    )
    db.add(config)
    await db.flush()
    return {"id": config_id, "name": req.name, "status": "created"}


@router.put("/configs/{config_id}")
async def update_config(
    config_id: str, req: NotificationConfigUpdate, db: DbSession, _admin: AdminUser
) -> dict:
    result = await db.execute(select(NotificationConfig).where(NotificationConfig.id == config_id))
    config = result.scalar()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    if req.name is not None:
        config.name = req.name
    if req.ntype is not None:
        config.ntype = req.ntype
    if req.enabled is not None:
        config.enabled = req.enabled
    if req.config is not None:
        config.config = json.dumps(req.config)

    await db.flush()
    return {"id": config_id, "status": "updated"}


@router.delete("/configs/{config_id}")
async def delete_config(config_id: str, db: DbSession, _admin: AdminUser) -> dict:
    result = await db.execute(select(NotificationConfig).where(NotificationConfig.id == config_id))
    config = result.scalar()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    await db.delete(config)
    await db.flush()
    return {"message": "配置已删除"}


@router.post("/configs/{config_id}/toggle")
async def toggle_config(config_id: str, db: DbSession, _admin: AdminUser) -> dict:
    result = await db.execute(select(NotificationConfig).where(NotificationConfig.id == config_id))
    config = result.scalar()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    config.enabled = not config.enabled
    await db.flush()
    return {"id": config_id, "enabled": config.enabled}


@router.post("/test")
async def test_notification(req: NotificationTestRequest, db: DbSession, _admin: AdminUser) -> dict:
    result = await db.execute(select(NotificationConfig).where(NotificationConfig.enabled))
    configs = result.scalars().all()

    notifier_configs = [
        {
            "type": c.ntype,
            "enabled": c.enabled,
            **json.loads(c.config),
        }
        for c in configs
    ]

    service = NotificationService({"notifiers": notifier_configs})
    results = await service.send(req.title, req.content)
    return {"results": results}


@router.post("/send")
async def send_notification(req: NotificationTestRequest, db: DbSession, _admin: AdminUser) -> dict:
    result = await db.execute(select(NotificationConfig).where(NotificationConfig.enabled))
    configs = result.scalars().all()

    notifier_configs = [
        {
            "type": c.ntype,
            "enabled": c.enabled,
            **json.loads(c.config),
        }
        for c in configs
    ]

    service = NotificationService({"notifiers": notifier_configs})
    results = await service.send(req.title, req.content)
    return {"results": results}
