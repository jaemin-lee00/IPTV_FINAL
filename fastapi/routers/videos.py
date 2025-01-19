from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
from services.youtube import get_video_details

router = APIRouter()

@router.get("/video_details/{video_id}")
async def video_details_page(video_id: str):
    return FileResponse("static/MainPage.html")

@router.get("/api/video_details/{video_id}")
async def video_details_api(video_id: str):
    video_data = get_video_details(video_id)
    if not video_data:
        return JSONResponse({"error": "영상 정보를 찾을 수 없습니다."}, status_code=404)
    return JSONResponse({"video": video_data})
