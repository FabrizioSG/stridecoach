import sys
from pathlib import Path

from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import Base, SessionLocal, engine
from app.models.training import TrainingPlan, User
from app.services.starter_plan_service import build_starter_plan


def seed() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.supabase_user_id == "local-demo-user"))
        if user is None:
            user = User(
                supabase_user_id="local-demo-user",
                email="runner@example.com",
                display_name="Demo Runner",
                avatar_url=None,
            )
            db.add(user)
            db.flush()
        else:
            for plan in db.scalars(
                select(TrainingPlan).where(TrainingPlan.user_id == user.id)
            ).all():
                db.delete(plan)

        plan = build_starter_plan(user)
        db.add(plan)
        db.commit()
        print(
            "Seeded StrideCoach sample training plan for the local demo user. "
            "Authenticated Supabase users are not modified."
        )


if __name__ == "__main__":
    seed()
