from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from config import SessionLocal
from models import User

router = APIRouter()

# 데이터베이스 세션 생성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 사용자 데이터 저장 API
@router.post("/api/users")
async def save_user(
    name: str = Form(...),
    age: int = Form(...),
    gender: bool = Form(...),
    weight: float = Form(...),
    height: float = Form(...),
    bmi: float = Form(...),
    drinking_status: bool = Form(...),
    smoking_status: bool = Form(...),
    obesity_status: bool = Form(...),
    fatigue_status: bool = Form(...)
):
    db = next(get_db())
    new_user = User(
        name=name,
        age=age,
        gender=gender,
        weight=weight,
        height=height,
        bmi=bmi,
        drinking_status=drinking_status,
        smoking_status=smoking_status,
        obesity_status=obesity_status,
        fatigue_status=fatigue_status
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return JSONResponse({"message": "User data saved successfully", "user_id": new_user.user_id})

# 특정 사용자 데이터 조회 API
@router.get("/api/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_data = {
        "user_id": user.user_id,
        "name": user.name,
        "age": user.age,
        "gender": user.gender,
        "weight": user.weight,
        "height": user.height,
        "bmi": user.bmi,
        "drinking_status": user.drinking_status,
        "smoking_status": user.smoking_status,
        "obesity_status": user.obesity_status,
        "fatigue_status": user.fatigue_status
    }
    return JSONResponse(user_data)

# 모든 사용자 데이터 조회 API
@router.get("/api/users")
async def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    user_list = [
        {
            "user_id": user.user_id,
            "name": user.name,
            "age": user.age,
            "gender": user.gender,
            "weight": user.weight,
            "height": user.height,
            "bmi": user.bmi,
            "drinking_status": user.drinking_status,
            "smoking_status": user.smoking_status,
            "obesity_status": user.obesity_status,
            "fatigue_status": user.fatigue_status
        }
        for user in users
    ]
    return JSONResponse({"users": user_list})
