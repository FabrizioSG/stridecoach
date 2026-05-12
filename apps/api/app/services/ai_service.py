import json
import logging
from typing import Any

from fastapi import HTTPException, status
from openai import OpenAI, OpenAIError

from app.core.config import get_settings
from app.models.training import Workout

logger = logging.getLogger(__name__)


class AIService:
    def analyze_workout(self, workout: Workout) -> str:
        settings = get_settings()
        if not settings.openai_api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OPENAI_API_KEY is not configured",
            )

        client = OpenAI(api_key=settings.openai_api_key)
        prompt = self._build_prompt(workout)
        logger.info(
            "Generating workout analysis",
            extra={
                "workout_id": str(workout.id),
                "model": settings.openai_model,
                "prompt_chars": len(prompt),
            },
        )

        try:
            request_params = {
                "model": settings.openai_model,
                "input": prompt,
                "max_output_tokens": 1200,
            }
            if settings.openai_model.startswith("gpt-5"):
                request_params["reasoning"] = {"effort": "minimal"}
                request_params["text"] = {"verbosity": "low"}

            response = client.responses.create(**request_params)
        except OpenAIError as exc:
            logger.exception(
                "OpenAI workout analysis failed",
                extra={
                    "workout_id": str(workout.id),
                    "model": settings.openai_model,
                    "exception_type": exc.__class__.__name__,
                    "exception_message": str(exc),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    f"Unable to generate workout analysis: {exc.__class__.__name__}: {exc}"
                    if settings.debug
                    else "Unable to generate workout analysis"
                ),
            ) from exc

        analysis = self._extract_text(response)
        logger.info(
            "OpenAI workout analysis response",
            extra={
                "workout_id": str(workout.id),
                "response_id": getattr(response, "id", None),
                "model": getattr(response, "model", None),
                "status": getattr(response, "status", None),
                "incomplete_details": str(getattr(response, "incomplete_details", None)),
                "text_chars": len(analysis),
                "output_items": len(getattr(response, "output", []) or []),
            },
        )
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OpenAI returned an empty analysis",
            )
        return analysis

    def _extract_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        chunks: list[str] = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                text = getattr(content, "text", None)
                if isinstance(text, str) and text.strip():
                    chunks.append(text.strip())
        return "\n\n".join(chunks).strip()

    def _build_prompt(self, workout: Workout) -> str:
        return f"""
You are StrideCoach, a thoughtful running coach speaking directly to the runner.
Use "you" and "your"; never say "the athlete." Be warm, specific, and practical,
like a coach reviewing the run with them after training.

Avoid medical claims and avoid overconfidence. If data is missing or a workout was
shorter/slower than planned, mention a few possible explanations without assuming
the runner failed. Do not scold. Focus on what the workout likely means and what to
do next.

Return 4 short sections:
1. Summary
2. Planned vs actual
3. Coaching read
4. Next step

Format the response as clean Markdown using level-3 headings like "### Summary".
Do not bold section headings. Keep paragraphs short and use bullets only when useful.

Keep it concise. Use direct language. Example tone: "You got some aerobic work in,
but this did not fully hit the threshold stimulus we planned."

Workout:
- Title: {workout.title}
- Description: {workout.description or "None"}
- Scheduled date: {workout.scheduled_date}
- Status: {workout.status.value}
- Planned distance km: {workout.planned_distance_km}
- Planned duration min: {workout.planned_duration_min}
- Planned pace: {workout.planned_pace}
- Planned HR zone: {workout.planned_hr_zone}
- Actual distance km: {workout.actual_distance_km}
- Actual duration min: {workout.actual_duration_min}
- Actual average HR: {workout.actual_avg_hr}
- Actual average cadence: {workout.actual_avg_cadence}
- Actual average pace: {workout.actual_avg_pace}
- Athlete notes: {workout.notes or "None"}
- Garmin screenshot metrics: {self._format_garmin_metrics(workout)}
""".strip()

    def _format_garmin_metrics(self, workout: Workout) -> str:
        if not workout.garmin_screenshot_metrics:
            return "None"
        try:
            metrics = json.loads(workout.garmin_screenshot_metrics)
        except json.JSONDecodeError:
            return workout.garmin_screenshot_metrics
        return json.dumps(metrics, indent=2, ensure_ascii=False)
