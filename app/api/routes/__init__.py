# app/api/routes/__init__.py
from fastapi import APIRouter
from app.api.routes.auth import router as auth_router
from app.api.routes.alianzas import router as alianzas_router
from app.api.routes.misiones import router as misiones_router
from app.api.routes.tripulantes import router as tripulantes_router
from app.api.routes.inventario import router as inventario_router     
from app.api.routes.ship import router as ship_router  
from app.api.routes.conflicto import router as conflicto_router
from app.api.routes.crafting import router as crafting_router  
from app.api.routes.mining import router as mining_router
from app.api.routes.map import router as map_router       
from app.api.routes.recursos import router as recursos_router  

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(alianzas_router)
api_router.include_router(misiones_router)
api_router.include_router(tripulantes_router)  
api_router.include_router(inventario_router)    
api_router.include_router(ship_router)
api_router.include_router(conflicto_router)
api_router.include_router(crafting_router) 
api_router.include_router(mining_router) 
api_router.include_router(map_router)
api_router.include_router(recursos_router)