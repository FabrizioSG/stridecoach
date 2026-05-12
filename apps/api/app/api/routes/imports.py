from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.training import User
from app.schemas.training import TrainingPlanRead
from app.services.import_service import PlanImportError, TrainingPlanImportService

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/training-plan", response_model=TrainingPlanRead, status_code=status.HTTP_201_CREATED)
async def import_training_plan(
    file: UploadFile = File(...),
    replace_existing: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contents = await file.read()
    try:
        return TrainingPlanImportService().import_plan_file(
            db=db,
            user=current_user,
            file_bytes=contents,
            filename=file.filename or "plan",
            replace_existing=replace_existing,
        )
    except PlanImportError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
