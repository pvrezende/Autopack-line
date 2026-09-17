from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.products import router as products_router
from app.api.routes.configurations import router as configurations_router
from app.api.routes.production_orders import router as production_orders_router
from app.api.routes.scans import router as scans_router
from app.api.routes.pallets import router as pallets_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.work_schedules import router as work_schedules_router
from app.api.routes.integrations import router as integrations_router
from app.api.routes.retests import router as retests_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(health_router)
api_router.include_router(products_router)
api_router.include_router(configurations_router)
api_router.include_router(production_orders_router)
api_router.include_router(scans_router)
api_router.include_router(pallets_router)
api_router.include_router(dashboard_router)
api_router.include_router(work_schedules_router)

api_router.include_router(integrations_router)
api_router.include_router(retests_router)
