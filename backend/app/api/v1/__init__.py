from fastapi import APIRouter
from .historical import router as historical_router

router = APIRouter()

router.include_router(historical_router)