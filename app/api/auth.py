from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import get_password_hash, verify_password, create_access_token
from app.db.mongodb import get_database
from app.models.user import UserCreate, UserResponse, UserInDB
from app.api import deps
from bson.objectid import ObjectId

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db = Depends(get_database)):
    # Check if user exists
    existing_user = await db["users"].find_one({"email": user_in.email})
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    
    user_data = user_in.dict(exclude={"password"})
    user_data["hashed_password"] = get_password_hash(user_in.password)
    user_data["is_active"] = True
    user_data["face_encoding"] = None

    result = await db["users"].insert_one(user_data)
    
    user_data["_id"] = str(result.inserted_id)
    user_data["id"] = user_data["_id"]
    user_data["has_face_registered"] = False
    
    return UserResponse(**user_data)

@router.post("/login")
async def login(
    db = Depends(get_database), form_data: OAuth2PasswordRequestForm = Depends()
):
    user_data = await db["users"].find_one({"email": form_data.username})
    if not user_data:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    if not verify_password(form_data.password, user_data["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    if not user_data.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")

    user_id = str(user_data["_id"])
    access_token = create_access_token(subject=user_id)
    
    has_face_registered = user_data.get("face_encoding") is not None
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "name": user_data["name"],
            "email": user_data["email"],
            "role": user_data["role"],
            "has_face_registered": has_face_registered
        }
    }

@router.get("/me", response_model=UserResponse)
async def read_user_me(
    current_user: UserInDB = Depends(deps.get_current_active_user),
):
    user_dict = current_user.dict()
    user_dict["id"] = user_dict["_id"]
    user_dict["has_face_registered"] = current_user.face_encoding is not None
    return UserResponse(**user_dict)
