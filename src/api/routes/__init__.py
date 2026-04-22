from src.api.routes.announcements import router as announcements_router
from src.api.routes.auth import router as auth_router
from src.api.routes.crawler import router as crawler_router
from src.api.routes.dashboard import router as dashboard_router
from src.api.routes.export import router as export_router
from src.api.routes.marketing import router as marketing_router
from src.api.routes.notifications import router as notifications_router
from src.api.routes.schedules import router as schedules_router

__all__ = [
    "auth_router",
    "crawler_router",
    "dashboard_router",
    "export_router",
    "marketing_router",
    "notifications_router",
    "schedules_router",
    "announcements_router",
]
