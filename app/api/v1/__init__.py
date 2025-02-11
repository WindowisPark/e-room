# app/api/v1/__init__.py

from fastapi import APIRouter
from .pdf_manager import router as pdf_router

api_router = APIRouter()
api_router.include_router(pdf_router, prefix="/pdf", tags=["PDF Management"])
