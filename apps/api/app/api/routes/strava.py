from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.training import User
from app.services.strava_service import StravaService

router = APIRouter(prefix="/strava", tags=["strava"])


class LinkActivityRequest(BaseModel):
    activity_id: UUID


@router.get("/status")
def get_strava_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return StravaService().get_connection_status(db, current_user)


@router.get("/connect")
def connect_strava(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    url = StravaService().build_authorization_url(db, current_user)
    return {"authorizationUrl": url}


@router.get("/callback")
def strava_callback(
    code: str = Query(...),
    state: str = Query(...),
    scope: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    StravaService().complete_oauth_callback(db=db, code=code, state=state, scope=scope)
    redirect_url = f"{get_settings().frontend_app_url.rstrip('/')}/settings?strava=connected"
    return RedirectResponse(redirect_url)


@router.post("/sync")
def sync_strava(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, list[dict]]:
    activities = StravaService().sync_recent_activities(db, current_user)
    return {"activities": activities}


@router.get("/workouts/{workout_id}/candidates")
def list_workout_link_candidates(
    workout_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, list[dict]]:
    activities = StravaService().list_link_candidates(db, current_user, workout_id)
    return {"activities": activities}


@router.post("/workouts/{workout_id}/link")
def link_activity_to_workout(
    workout_id: UUID,
    payload: LinkActivityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workout = StravaService().link_activity_to_workout(
        db=db,
        user=current_user,
        workout_id=workout_id,
        activity_id=payload.activity_id,
    )
    return workout


@router.delete("/workouts/{workout_id}/link")
def unlink_activity_from_workout(
    workout_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return StravaService().unlink_activity_from_workout(db, current_user, workout_id)
