from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter(prefix="/api/integration", tags=["Team Integration Testing"])

class FrontendSyncPayload(BaseModel):
    user_id: str = Field(..., alias="userId") # Supports both snake_case and camelCase
    action_type: str = Field(..., alias="actionType")
    confidence_score: Optional[float] = Field(0.0, alias="confidenceScore")

    class Config:
        populate_by_name = True

@router.post("/test-sync", status_code=status.HTTP_200_OK)
def test_frontend_business_logic_sync(payload: FrontendSyncPayload):
    """
    Day 9 Integration Test: Validates data format consistency between Frontend (Intern 1) 
    and Business Logic (Intern 4) payloads.
    """
    return {
        "status": "success",
        "message": "Data format compatibility verified successfully.",
        "received_data": {
            "userId": payload.user_id,
            "actionType": payload.action_type,
            "confidenceScore": payload.confidence_score
        }
    }