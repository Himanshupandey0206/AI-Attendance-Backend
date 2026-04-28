from fastapi import APIRouter, Depends, Body
from app.api import deps
from app.models.user import UserInDB
from app.services.ai_service import process_ai_query

router = APIRouter()

@router.post("/query")
async def ask_ai(
    query: str = Body(..., embed=True),
    current_user: UserInDB = Depends(deps.get_current_active_manager_or_admin)
):
    response_text = await process_ai_query(query, current_user.role)
    return {"response": response_text}
