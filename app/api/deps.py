from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from app.core.config import settings
from app.core import security
from app.db.mongodb import get_database
from app.models.user import UserInDB
from bson.objectid import ObjectId

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_current_user(
    db = Depends(get_database), token: str = Depends(reusable_oauth2)
) -> UserInDB:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    user_data = await db["users"].find_one({"_id": ObjectId(user_id)})
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Map _id to string id for Pydantic model
    user_data["_id"] = str(user_data["_id"])
    return UserInDB(**user_data)

async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_active_admin(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user

async def get_current_active_manager_or_admin(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
