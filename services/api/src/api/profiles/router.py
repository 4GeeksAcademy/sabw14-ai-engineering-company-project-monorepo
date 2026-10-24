from fastapi import APIRouter, HTTPException, status

from api.auth.dependencies import CurrentUser
from api.profiles import service
from api.profiles.schemas import ProfileOut, ProfileUpdate

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=ProfileOut)
def get_my_profile(current_user: CurrentUser):
    profile = service.get_profile_by_user_id(current_user["id"])
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.put("/me", response_model=ProfileOut)
def update_my_profile(data: ProfileUpdate, current_user: CurrentUser):
    profile = service.update_profile(current_user["id"], data)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile
