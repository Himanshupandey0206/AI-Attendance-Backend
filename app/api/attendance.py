from fastapi import APIRouter, Depends, HTTPException, Body
from app.api import deps
from app.db.mongodb import get_database
from app.models.user import UserInDB
from app.services.face_recognition_service import get_face_encoding, verify_face
from datetime import datetime
from bson.objectid import ObjectId

router = APIRouter()

@router.post("/register-face")
async def register_face(
    image_data: str = Body(..., embed=True),
    current_user: UserInDB = Depends(deps.get_current_active_user),
    db = Depends(get_database)
):
    if current_user.face_encoding is not None:
        raise HTTPException(status_code=400, detail="Face already registered")
        
    encoding = get_face_encoding(image_data)
    if not encoding:
        raise HTTPException(status_code=400, detail="No face detected in the image")
        
    await db["users"].update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"face_encoding": encoding}}
    )
    
    return {"message": "Face registered successfully"}

@router.post("/punch-in")
async def punch_in(
    image_data: str = Body(..., embed=True),
    latitude: float = Body(..., embed=True),
    longitude: float = Body(..., embed=True),
    current_user: UserInDB = Depends(deps.get_current_active_user),
    db = Depends(get_database)
):
    if current_user.face_encoding is None:
        raise HTTPException(status_code=400, detail="Face not registered. Please register first.")
        
    # Verify face
    is_match = verify_face(current_user.face_encoding, image_data)
    if not is_match:
        raise HTTPException(status_code=400, detail="Face mismatch. Authentication failed.")
        
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Check if already punched in
    existing = await db["attendance"].find_one({
        "user_id": current_user.id,
        "date": today
    })
    
    if existing and existing.get("punch_in"):
        raise HTTPException(status_code=400, detail="Already punched in today")
        
    attendance_data = {
        "user_id": current_user.id,
        "date": today,
        "punch_in": {
            "time": datetime.now(),
            "location": {"latitude": latitude, "longitude": longitude},
            "selfie_url": "dummy_url_or_base64_log" # In production, upload to S3/Cloudinary and store URL
        },
        "status": "Pending",
        "total_hours": 0.0,
        "is_valid": True
    }
    
    if existing:
        await db["attendance"].update_one({"_id": existing["_id"]}, {"$set": {"punch_in": attendance_data["punch_in"]}})
    else:
        await db["attendance"].insert_one(attendance_data)
        
    return {"message": "Punched in successfully"}

@router.post("/punch-out")
async def punch_out(
    image_data: str = Body(..., embed=True),
    latitude: float = Body(..., embed=True),
    longitude: float = Body(..., embed=True),
    current_user: UserInDB = Depends(deps.get_current_active_user),
    db = Depends(get_database)
):
    if current_user.face_encoding is None:
        raise HTTPException(status_code=400, detail="Face not registered.")
        
    is_match = verify_face(current_user.face_encoding, image_data)
    if not is_match:
        raise HTTPException(status_code=400, detail="Face mismatch. Authentication failed.")
        
    today = datetime.now().strftime("%Y-%m-%d")
    record = await db["attendance"].find_one({
        "user_id": current_user.id,
        "date": today
    })
    
    if not record or not record.get("punch_in"):
        raise HTTPException(status_code=400, detail="No punch-in record found for today")
        
    if record.get("punch_out"):
        raise HTTPException(status_code=400, detail="Already punched out today")
        
    punch_out_time = datetime.now()
    punch_in_time = record["punch_in"]["time"]
    
    duration = punch_out_time - punch_in_time
    hours_worked = duration.total_seconds() / 3600
    
    status = "Present" if hours_worked >= 8.0 else "Incomplete"
    
    await db["attendance"].update_one(
        {"_id": record["_id"]},
        {
            "$set": {
                "punch_out": {
                    "time": punch_out_time,
                    "location": {"latitude": latitude, "longitude": longitude},
                    "selfie_url": "dummy_url_or_base64_log"
                },
                "total_hours": hours_worked,
                "status": status
            }
        }
    )
    
    return {"message": f"Punched out successfully. Total hours: {hours_worked:.2f}", "status": status}

@router.get("/my-records")
async def get_my_records(
    current_user: UserInDB = Depends(deps.get_current_active_user),
    db = Depends(get_database)
):
    cursor = db["attendance"].find({"user_id": current_user.id}).sort("date", -1)
    records = await cursor.to_list(length=100)
    for r in records:
        r["id"] = str(r["_id"])
        del r["_id"]
    return records
