#이거 일단 스킵하자

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from services.recommendation import recommend_videos
from config import SessionLocal
from models import User, Detail

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/api/recommendations")
async def get_recommendations(user_id: int, db: Session = Depends(get_db)):
    # 사용자 데이터 조회
    user = db.query(User).filter(User.user_id == user_id).first()
    detail = db.query(Detail).filter(Detail.user_id == user_id).first()

    if not user or not detail:
        return JSONResponse({"error": "User or Detail not found"}, status_code=404)

    # 추천 카테고리 결정
    categories = []
    if detail.fatigue_status:
        categories.append("수면장애")
    if detail.hypertension_status:
        categories.append("심혈관질환")
    if detail.cholesterol_status:
        categories.append("당뇨")

    # 추천 비디오 생성
    recommendations = recommend_videos(categories)
    return JSONResponse({"recommendations": recommendations})
