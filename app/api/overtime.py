from fastapi import APIRouter, Depends, HTTPException, Body
from app.api import deps
from app.db.mongodb import get_database
from app.models.user import UserInDB
from app.models.attendance import OvertimeRequestBase
from datetime import datetime
from bson.objectid import ObjectId

router = APIRouter()

@router.post("/request")
async def request_overtime(
    req: OvertimeRequestBase,
    current_user: UserInDB = Depends(deps.get_current_active_user),
    db = Depends(get_database)
):
    if req.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only request overtime for yourself")
        
    ot_doc = req.dict()
    ot_doc["status"] = "Pending"
    
    result = await db["overtime_requests"].insert_one(ot_doc)
    ot_doc["id"] = str(result.inserted_id)
    ot_doc.pop("_id", None)
    
    return ot_doc

@router.get("/my-requests")
async def my_overtime_requests(
    current_user: UserInDB = Depends(deps.get_current_active_user),
    db = Depends(get_database)
):
    cursor = db["overtime_requests"].find({"user_id": current_user.id}).sort("date", -1)
    records = await cursor.to_list(length=100)
    for r in records:
        r["id"] = str(r["_id"])
        del r["_id"]
    return records

@router.get("/pending", dependencies=[Depends(deps.get_current_active_manager_or_admin)])
async def get_pending_requests(db = Depends(get_database)):
    cursor = db["overtime_requests"].find({"status": "Pending"})
    records = await cursor.to_list(length=100)
    for r in records:
        r["id"] = str(r["_id"])
        del r["_id"]
        # Fetch user name for context
        user = await db["users"].find_one({"_id": ObjectId(r["user_id"])})
        if user:
            r["user_name"] = user["name"]
    return records

@router.post("/{request_id}/approve", dependencies=[Depends(deps.get_current_active_manager_or_admin)])
async def approve_overtime(request_id: str, db = Depends(get_database)):
    result = await db["overtime_requests"].update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"status": "Approved"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Request not found or already processed")
    return {"message": "Overtime approved"}

@router.post("/{request_id}/reject", dependencies=[Depends(deps.get_current_active_manager_or_admin)])
async def reject_overtime(request_id: str, db = Depends(get_database)):
    result = await db["overtime_requests"].update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"status": "Rejected"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Request not found or already processed")
    return {"message": "Overtime rejected"}
