# app/api/routes/__init__.py
from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.config import router as config_router
from app.api.routes.crafting import router as crafting_router
from app.api.routes.db_check import router as dbcheck
from app.api.routes.health import router as health
from app.api.routes.map import router as map_router
from app.api.routes.misiones import router as misiones_router
from app.api.routes.player import router as player_routes
from app.api.routes.mining import router as mining_router # <-- AÑADIR
from app.api.routes.recursos import router as recursos_router
from app.api.routes.server import router as server_router
from app.api.routes.ship import router as ship_router
from app.api.routes.tripulantes import router as tripulantes_router
from app.api.routes.unidades import router as unidades_router
from app.api.routes.users import router as users


api_router = APIRouter()
api_router.include_router(health)
api_router.include_router(auth_router)
api_router.include_router(server_router)
api_router.include_router(users)
api_router.include_router(dbcheck)
api_router.include_router(map_router)
api_router.include_router(player_routes)
api_router.include_router(ship_router)
api_router.include_router(mining_router) # <-- AÑADIR
api_router.include_router(recursos_router)
api_router.include_router(misiones_router)
api_router.include_router(crafting_router)
api_router.include_router(unidades_router)
api_router.include_router(config_router)
api_router.include_router(tripulantes_router)