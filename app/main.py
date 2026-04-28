from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection

# Define app first
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event handlers
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Attendance Management System API"}

from app.api.auth import router as auth_router
from app.api.attendance import router as attendance_router
from app.api.overtime import router as overtime_router
from app.api.admin import router as admin_router
from app.api.ai import router as ai_router

app.include_router(auth_router, prefix=settings.API_V1_STR + "/auth", tags=["auth"])
app.include_router(attendance_router, prefix=settings.API_V1_STR + "/attendance", tags=["attendance"])
app.include_router(overtime_router, prefix=settings.API_V1_STR + "/overtime", tags=["overtime"])
app.include_router(admin_router, prefix=settings.API_V1_STR + "/admin", tags=["admin"])
app.include_router(ai_router, prefix=settings.API_V1_STR + "/ai", tags=["ai"])
