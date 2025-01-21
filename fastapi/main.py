from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from config import engine, Base
from routers import user, detail
from STT_Model.Voice_Input_API.api import app as api_app
import uvicorn

app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(user.router)
app.include_router(detail.router)
app.mount("/api", api_app)  # api_app을 /api 경로에 마운트

# Serve static files
app.mount(
    "/static",
    StaticFiles(directory="C:/Users/Admin/Documents/GitHub/IPTV_FINAL/fastapi/static/build"),
    name="static",
)

# Serve Svelte index.html
@app.get("/")
async def serve_index():
    return FileResponse("C:/Users/Admin/Documents/GitHub/IPTV_FINAL/fastapi/static/build/index.html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)