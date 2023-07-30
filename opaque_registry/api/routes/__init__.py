from fastapi import Depends, FastAPI

from opaque_registry.api.routes.package import router as package_router

ROUTERS = {"package": package_router}


def load_routers(app: FastAPI):
    for router in ROUTERS.values():
        app.include_router(router)
