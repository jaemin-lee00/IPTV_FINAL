from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from config import SessionLocal
from models import Detail

router = APIRouter()

# 데이터베이스 세션 생성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 상세 정보 저장 API
@router.post("/api/details")
async def save_detail(
    user_id: int = Form(...),
    systolic_bp: int = Form(...),
    diastolic_bp: int = Form(...),
    heart_rate: int = Form(...),
    daily_steps: int = Form(...),
    cholesterol_status: bool = Form(...),
    daily_sleep: float = Form(...),
    hypertension_status: bool = Form(...)
):
    db = next(get_db())
    new_detail = Detail(
        user_id=user_id,
        systolic_bp=systolic_bp,
        diastolic_bp=diastolic_bp,
        heart_rate=heart_rate,
        daily_steps=daily_steps,
        cholesterol_status=cholesterol_status,
        daily_sleep=daily_sleep,
        hypertension_status=hypertension_status
    )
    db.add(new_detail)
    db.commit()
    db.refresh(new_detail)

    return JSONResponse({"message": "Detail data saved successfully", "detail_id": new_detail.detail_id})

# 특정 사용자 상세 정보 조회 API
@router.get("/api/details/{user_id}")
async def get_detail(user_id: int, db: Session = Depends(get_db)):
    detail = db.query(Detail).filter(Detail.user_id == user_id).first()
    if not detail:
        raise HTTPException(status_code=404, detail="Detail not found")
    detail_data = {
        "detail_id": detail.detail_id,
        "systolic_bp": detail.systolic_bp,
        "diastolic_bp": detail.diastolic_bp,
        "heart_rate": detail.heart_rate,
        "daily_steps": detail.daily_steps,
        "cholesterol_status": detail.cholesterol_status,
        "daily_sleep": detail.daily_sleep,
        "hypertension_status": detail.hypertension_status
    }
    return JSONResponse(detail_data)

# 상세 정보 삭제 API
@router.delete("/api/details/{user_id}")
async def delete_detail(user_id: int, db: Session = Depends(get_db)):
    detail = db.query(Detail).filter(Detail.user_id == user_id).first()
    if not detail:
        raise HTTPException(status_code=404, detail="Detail not found")
    db.delete(detail)
    db.commit()
    return {"message": "Detail deleted successfully"}
