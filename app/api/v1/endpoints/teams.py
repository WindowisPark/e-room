# app/api/v1/endpoints/teams.py 파일을 매우 간단한 버전으로 교체
from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
def test_route():
    return {"message": "Test successful"}