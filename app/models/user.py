from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from enum import Enum

class RoleEnum(str, Enum):
    admin = "admin"
    manager = "manager"
    employee = "employee"

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: RoleEnum = RoleEnum.employee

class UserCreate(UserBase):
    password: str
    image_data: Optional[str] = None

class UserInDB(UserBase):
    id: str = Field(alias="_id")
    hashed_password: str
    face_encoding: Optional[List[float]] = None
    is_active: bool = True

class UserResponse(UserBase):
    id: str
    is_active: bool
    has_face_registered: bool = False
