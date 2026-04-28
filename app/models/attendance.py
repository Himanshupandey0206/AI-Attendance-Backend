from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Location(BaseModel):
    latitude: float
    longitude: float

class PunchDetails(BaseModel):
    time: datetime
    location: Optional[Location] = None
    selfie_url: Optional[str] = None

class AttendanceBase(BaseModel):
    user_id: str
    date: str # YYYY-MM-DD format

class AttendanceInDB(AttendanceBase):
    id: str = Field(alias="_id")
    punch_in: Optional[PunchDetails] = None
    punch_out: Optional[PunchDetails] = None
    status: str = "Pending" # Present, Incomplete, Pending
    total_hours: float = 0.0
    is_valid: bool = True

class AttendanceResponse(AttendanceInDB):
    id: str

class OvertimeRequestBase(BaseModel):
    user_id: str
    date: str
    hours: float
    reason: Optional[str] = None

class OvertimeRequestInDB(OvertimeRequestBase):
    id: str = Field(alias="_id")
    status: str = "Pending" # Pending, Approved, Rejected

class OvertimeRequestResponse(OvertimeRequestInDB):
    id: str
