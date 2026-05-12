import json
import time
import uuid
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.training import (
    StravaActivity,
    StravaConnection,
    TrainingPlan,
    TrainingWeek,
    User,
    Workout,
    WorkoutStatus,
)

STRAVA_AUTHORIZE_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"


class StravaService:
    def build_authorization_url(self, db: Session, user: User) -> str:
        settings = get_settings()
        self._ensure_configured()

        connection = self._get_or_create_connection(db, user)
        connection.oauth_state = uuid.uuid4().hex
        db.add(connection)
        db.commit()

        query = urlencode(
            {
                "client_id": settings.strava_client_id,
                "response_type": "code",
                "redirect_uri": settings.strava_redirect_uri,
                "approval_prompt": "auto",
                "scope": "read,activity:read_all",
                "state": connection.oauth_state,
            }
        )
        return f"{STRAVA_AUTHORIZE_URL}?{query}"

    def complete_oauth_callback(
        self,
        db: Session,
        code: str,
        state: str,
        scope: str | None,
    ) -> StravaConnection:
        self._ensure_configured()
        connection = db.scalar(
            select(StravaConnection).where(StravaConnection.oauth_state == state)
        )
        if connection is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Strava state",
            )

        token_payload = self._post_form(
            STRAVA_TOKEN_URL,
            {
                "client_id": get_settings().strava_client_id,
                "client_secret": get_settings().strava_client_secret,
                "code": code,
                "grant_type": "authorization_code",
            },
        )

        athlete = token_payload.get("athlete") or {}
        connection.athlete_id = athlete.get("id")
        connection.athlete_username = athlete.get("username")
        connection.athlete_firstname = athlete.get("firstname")
        connection.athlete_lastname = athlete.get("lastname")
        connection.scope = scope
        connection.access_token = token_payload.get("access_token")
        connection.refresh_token = token_payload.get("refresh_token")
        connection.expires_at = token_payload.get("expires_at")
        connection.oauth_state = None
        connection.connected_at = datetime.now(UTC)

        db.add(connection)
        db.commit()
        db.refresh(connection)
        return connection

    def get_connection_status(self, db: Session, user: User) -> dict[str, Any]:
        connection = db.scalar(select(StravaConnection).where(StravaConnection.user_id == user.id))
        if connection is None or not connection.refresh_token:
            return {"connected": False}

        return {
            "connected": True,
            "athleteId": connection.athlete_id,
            "athleteName": self._athlete_name(connection),
            "scope": connection.scope,
            "connectedAt": connection.connected_at.isoformat() if connection.connected_at else None,
        }

    def sync_recent_activities(self, db: Session, user: User) -> list[dict[str, Any]]:
        connection = db.scalar(select(StravaConnection).where(StravaConnection.user_id == user.id))
        if connection is None or not connection.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Strava is not connected",
            )

        access_token = self._valid_access_token(db, connection)
        request = Request(
            f"{STRAVA_ACTIVITIES_URL}?per_page=10",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        with urlopen(request, timeout=10) as response:
            activities = json.loads(response.read().decode("utf-8"))

        return [self._upsert_activity(db, connection, activity) for activity in activities]

    def list_link_candidates(
        self,
        db: Session,
        user: User,
        workout_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        workout = self._get_user_workout(db, user, workout_id)
        connection = db.scalar(select(StravaConnection).where(StravaConnection.user_id == user.id))
        if connection is None:
            return []

        activities = db.scalars(
            select(StravaActivity)
            .where(
                StravaActivity.connection_id == connection.id,
                StravaActivity.workout_id.is_(None),
            )
            .order_by(StravaActivity.start_date.desc())
            .limit(25)
        ).all()
        return [self._activity_summary(activity, workout) for activity in activities]

    def link_activity_to_workout(
        self,
        db: Session,
        user: User,
        workout_id: uuid.UUID,
        activity_id: uuid.UUID,
    ) -> Workout:
        workout = self._get_user_workout(db, user, workout_id)
        connection = db.scalar(select(StravaConnection).where(StravaConnection.user_id == user.id))
        if connection is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Strava is not connected",
            )

        activity = db.scalar(
            select(StravaActivity).where(
                StravaActivity.id == activity_id,
                StravaActivity.connection_id == connection.id,
            )
        )
        if activity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strava activity not found",
            )

        activity.workout_id = workout.id
        workout.status = WorkoutStatus.completed
        workout.actual_distance_km = round((activity.distance_m or 0) / 1000, 2) or None
        workout.actual_duration_min = round((activity.moving_time_sec or 0) / 60) or None
        workout.actual_avg_hr = (
            round(activity.average_heartrate) if activity.average_heartrate else None
        )
        workout.actual_avg_cadence = (
            round(activity.average_cadence) if activity.average_cadence else None
        )
        workout.actual_avg_pace = self._pace_from_speed(activity.average_speed_mps)
        if not workout.notes:
            workout.notes = f"Linked manually to Strava activity: {activity.name}"

        db.add_all([activity, workout])
        db.commit()
        db.refresh(workout)
        return workout

    def unlink_activity_from_workout(
        self,
        db: Session,
        user: User,
        workout_id: uuid.UUID,
    ) -> Workout:
        workout = self._get_user_workout(db, user, workout_id)
        activity = workout.strava_activity
        if activity is not None:
            activity.workout_id = None
            db.add(activity)

        workout.actual_distance_km = None
        workout.actual_duration_min = None
        workout.actual_avg_hr = None
        workout.actual_avg_cadence = None
        workout.actual_avg_pace = None
        if workout.status == WorkoutStatus.completed:
            workout.status = WorkoutStatus.planned

        db.add(workout)
        db.commit()
        db.refresh(workout)
        return workout

    def _valid_access_token(self, db: Session, connection: StravaConnection) -> str:
        expires_at = connection.expires_at or 0
        if connection.access_token and expires_at > int(time.time()) + 60:
            return connection.access_token

        token_payload = self._post_form(
            STRAVA_TOKEN_URL,
            {
                "client_id": get_settings().strava_client_id,
                "client_secret": get_settings().strava_client_secret,
                "grant_type": "refresh_token",
                "refresh_token": connection.refresh_token,
            },
        )
        connection.access_token = token_payload.get("access_token")
        connection.refresh_token = token_payload.get("refresh_token")
        connection.expires_at = token_payload.get("expires_at")
        db.add(connection)
        db.commit()
        return connection.access_token or ""

    def _get_or_create_connection(self, db: Session, user: User) -> StravaConnection:
        connection = db.scalar(select(StravaConnection).where(StravaConnection.user_id == user.id))
        if connection is not None:
            return connection
        return StravaConnection(user=user)

    def _upsert_activity(
        self,
        db: Session,
        connection: StravaConnection,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        strava_activity_id = payload.get("id")
        activity = db.scalar(
            select(StravaActivity).where(StravaActivity.strava_activity_id == strava_activity_id)
        )
        if activity is None:
            activity = StravaActivity(
                connection=connection,
                strava_activity_id=strava_activity_id,
                name=payload.get("name") or "Strava Activity",
            )

        activity.name = payload.get("name") or "Strava Activity"
        activity.sport_type = payload.get("sport_type") or payload.get("type")
        activity.start_date = self._parse_strava_datetime(payload.get("start_date"))
        activity.distance_m = payload.get("distance")
        activity.moving_time_sec = payload.get("moving_time")
        activity.elapsed_time_sec = payload.get("elapsed_time")
        activity.average_heartrate = payload.get("average_heartrate")
        activity.average_cadence = payload.get("average_cadence")
        activity.average_speed_mps = payload.get("average_speed")
        activity.raw = json.dumps(payload)

        db.add(activity)
        db.commit()
        db.refresh(activity)
        return self._activity_summary(activity)

    def _get_user_workout(self, db: Session, user: User, workout_id: uuid.UUID) -> Workout:
        workout = db.scalar(
            select(Workout)
            .join(Workout.week)
            .join(TrainingWeek.plan)
            .where(Workout.id == workout_id, TrainingPlan.user_id == user.id)
            .options(selectinload(Workout.strava_activity))
        )
        if workout is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
        return workout

    def _activity_summary(
        self,
        activity: StravaActivity,
        workout: Workout | None = None,
    ) -> dict[str, Any]:
        distance_km = round((activity.distance_m or 0) / 1000, 2) if activity.distance_m else None
        duration_min = (
            round((activity.moving_time_sec or 0) / 60) if activity.moving_time_sec else None
        )
        return {
            "id": str(activity.id),
            "stravaActivityId": activity.strava_activity_id,
            "name": activity.name,
            "sportType": activity.sport_type,
            "startDate": activity.start_date.isoformat() if activity.start_date else None,
            "distanceKm": distance_km,
            "durationMin": duration_min,
            "averageHr": activity.average_heartrate,
            "averageCadence": activity.average_cadence,
            "averagePace": self._pace_from_speed(activity.average_speed_mps),
            "score": self._match_score(activity, workout) if workout else None,
        }

    def _match_score(self, activity: StravaActivity, workout: Workout | None) -> int | None:
        if workout is None or activity.start_date is None:
            return None
        score = 0
        if activity.start_date.date() == workout.scheduled_date:
            score += 70
        else:
            days_apart = abs((activity.start_date.date() - workout.scheduled_date).days)
            score += max(0, 40 - (days_apart * 10))
        if workout.planned_distance_km and activity.distance_m:
            distance_delta = abs((activity.distance_m / 1000) - workout.planned_distance_km)
            score += max(0, 30 - round(distance_delta * 6))
        return min(score, 100)

    def _pace_from_speed(self, speed_mps: float | None) -> str | None:
        if not speed_mps:
            return None
        seconds_per_km = round(1000 / speed_mps)
        minutes, seconds = divmod(seconds_per_km, 60)
        return f"{minutes}:{seconds:02d}/km"

    def _parse_strava_datetime(self, value: str | None) -> datetime | None:
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def _post_form(self, url: str, data: dict[str, Any]) -> dict[str, Any]:
        form_data = {key: value for key, value in data.items() if value is not None}
        encoded = urlencode(form_data).encode("utf-8")
        request = Request(
            url,
            data=encoded,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except OSError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to reach Strava",
            ) from exc

    def _ensure_configured(self) -> None:
        settings = get_settings()
        if not settings.strava_client_id or not settings.strava_client_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Strava client credentials are not configured",
            )

    def _athlete_name(self, connection: StravaConnection) -> str | None:
        name = " ".join(
            part
            for part in [connection.athlete_firstname, connection.athlete_lastname]
            if part
        ).strip()
        return name or connection.athlete_username
