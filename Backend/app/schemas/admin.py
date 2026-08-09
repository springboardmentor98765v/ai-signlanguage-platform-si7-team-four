from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

"""
Admin Management response schemas. These give Swagger /docs an accurate
response body for every endpoint in app/routers/admin_router.py.
"""


class UserAdminOut(BaseModel):
    """A single user row returned by GET /api/admin/users."""

    id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None


class StatusMessageResponse(BaseModel):
    """Response body for single-user status/role updates."""

    message: str
    email: str


class DeleteUserResponse(BaseModel):
    """Response body for DELETE /api/admin/users/{user_id}."""

    message: str


class BulkDeleteResponse(BaseModel):
    """Response body for POST /api/admin/users/bulk-delete."""

    message: str
    deleted_count: int
    not_found_ids: List[str]


class BulkCountResponse(BaseModel):
    """Response body for bulk status/role updates."""

    message: str
    updated_count: int


class BulkUserStatusResponse(BaseModel):
    """Response body for POST /api/admin/bulk-user-status."""

    message: str
    is_active: bool
    updated_count: int
    updated_user_ids: List[str]
    not_found: List[str]
    not_found_count: int


class RejectedLessonRow(BaseModel):
    """One rejected CSV row with the validation reason."""

    row: int
    reason: str


class BulkUploadLessonsResponse(BaseModel):
    """Response body for POST /api/admin/bulk-upload-lessons."""

    message: str
    rows_processed: int
    rows_inserted: int
    rows_rejected: int
    rejected_rows: List[RejectedLessonRow]
