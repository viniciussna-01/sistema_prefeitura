from fastapi import APIRouter

from app.api.v1 import (
    agents,
    audit,
    auth,
    certificates,
    companies,
    dashboard,
    downloads,
    executions,
    schedules,
    users,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(companies.router)
api_router.include_router(certificates.router)
api_router.include_router(agents.router)
api_router.include_router(executions.router)
api_router.include_router(schedules.router)
api_router.include_router(downloads.router)
api_router.include_router(dashboard.router)
api_router.include_router(audit.router)
