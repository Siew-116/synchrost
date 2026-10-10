"""API routers for StudyBiz AI."""
from app.routers.dashboard import router as dashboard_router
from app.routers.campaigns import router as campaigns_router
from app.routers.orders import router as orders_router
from app.routers.customers import router as customers_router
from app.routers.inbox import router as inbox_router
from app.routers.exceptions import router as exceptions_router
from app.routers.supplier import router as supplier_router
from app.routers.automation import router as automation_router
from app.routers.agent import router as agent_router
from app.routers.telegram_api import router as telegram_router
from app.routers.settings import router as settings_router
