from fastapi import APIRouter, Depends, HTTPException
from app.api import deps
from app.db.mongodb import get_database
from bson.objectid import ObjectId

router = APIRouter()

@router.get("/attendance", dependencies=[Depends(deps.get_current_active_manager_or_admin)])
async def get_all_attendance(date: str = None, db = Depends(get_database)):
    query = {}
    if date:
        query["date"] = date
        
    cursor = db["attendance"].find(query).sort("date", -1)
    records = await cursor.to_list(length=1000)
    
    # Attach user info
    for r in records:
        r["id"] = str(r["_id"])
        del r["_id"]
        user = await db["users"].find_one({"_id": ObjectId(r["user_id"])})
        if user:
            r["user_name"] = user["name"]
            r["user_email"] = user["email"]
            
    return records

@router.get("/users", dependencies=[Depends(deps.get_current_active_admin)])
async def get_all_users(db = Depends(get_database)):
    cursor = db["users"].find({})
    users = await cursor.to_list(length=100)
    for u in users:
        u["id"] = str(u["_id"])
        del u["_id"]
        u["has_face_registered"] = u.get("face_encoding") is not None
        if "hashed_password" in u:
            del u["hashed_password"]
        if "face_encoding" in u:
            del u["face_encoding"]
    return users

@router.put("/users/{user_id}/disable", dependencies=[Depends(deps.get_current_active_admin)])
async def disable_user(user_id: str, db = Depends(get_database)):
    result = await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": False}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User disabled"}

@router.put("/attendance/{record_id}/invalidate", dependencies=[Depends(deps.get_current_active_admin)])
async def invalidate_attendance(record_id: str, db = Depends(get_database)):
    result = await db["attendance"].update_one(
        {"_id": ObjectId(record_id)},
        {"$set": {"is_valid": False}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"message": "Record marked as invalid/fake"}
