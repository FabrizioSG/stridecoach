import base64
import json
import logging
import re
from typing import Any

from fastapi import HTTPException, UploadFile, status
from openai import OpenAI, OpenAIError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

MAX_SCREENSHOTS = 3
MAX_SCREENSHOT_BYTES = 6 * 1024 * 1024


class GarminScreenshotService:
    async def extract_metrics(self, files: list[UploadFile]) -> dict[str, Any]:
        settings = get_settings()
        if not settings.openai_api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OPENAI_API_KEY is not configured",
            )
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Upload at least one Garmin screenshot.",
            )
        if len(files) > MAX_SCREENSHOTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Upload up to {MAX_SCREENSHOTS} screenshots.",
            )

        image_inputs = []
        for file in files:
            content_type = file.content_type or ""
            if not content_type.startswith("image/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{file.filename or 'File'} is not an image.",
                )
            content = await file.read()
            if len(content) > MAX_SCREENSHOT_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{file.filename or 'Screenshot'} is larger than 6 MB.",
                )
            encoded = base64.b64encode(content).decode("ascii")
            image_inputs.append(
                {
                    "type": "input_image",
                    "image_url": f"data:{content_type};base64,{encoded}",
                }
            )

        client = OpenAI(api_key=settings.openai_api_key)
        prompt = self._build_prompt()
        logger.info(
            "Extracting Garmin screenshot metrics",
            extra={"model": settings.openai_vision_model, "screenshots": len(files)},
        )

        try:
            response = client.responses.create(
                model=settings.openai_vision_model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            *image_inputs,
                        ],
                    }
                ],
                max_output_tokens=2500,
            )
        except OpenAIError as exc:
            logger.exception(
                "OpenAI Garmin screenshot extraction failed",
                extra={
                    "model": settings.openai_vision_model,
                    "exception_type": exc.__class__.__name__,
                    "exception_message": str(exc),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    f"Unable to read Garmin screenshots: {exc.__class__.__name__}: {exc}"
                    if settings.debug
                    else "Unable to read Garmin screenshots"
                ),
            ) from exc

        text = self._extract_text(response)
        metrics = self._parse_json(text)
        metrics["source"] = "garmin_screenshots"
        metrics["screenshotCount"] = len(files)
        return metrics

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
        return "\n".join(chunks).strip()

    def _parse_json(self, text: str) -> dict[str, Any]:
        cleaned = text.strip()
        fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.DOTALL)
        if fenced:
            cleaned = fenced.group(1).strip()
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.warning(
                "Garmin screenshot extraction returned invalid JSON",
                extra={"text": text[:500]},
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Garmin screenshot extraction returned invalid data.",
            ) from exc
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Garmin screenshot extraction returned an unexpected shape.",
            )
        return payload

    def _build_prompt(self) -> str:
        return """
You extract workout data from Garmin Connect mobile screenshots.
Return ONLY valid JSON. Do not wrap it in Markdown.

The screenshots are expected to contain stable Garmin fields from tabs like Stats
and Workout Intervals. Extract every visible metric you can read. Preserve display
values with units exactly enough to be useful, and also provide normalized numeric
values when obvious.

Use this JSON shape:
{
  "summary": {
    "activityType": "Running",
    "distanceKm": number | null,
    "durationMin": number | null,
    "avgPace": string | null,
    "avgHeartRate": number | null,
    "avgCadence": number | null
  },
  "sections": {
    "pace": {},
    "speed": {},
    "timing": {},
    "runWalkDetection": {},
    "heartRate": {},
    "trainingEffect": {},
    "power": {},
    "runningDynamics": {},
    "elevation": {},
    "workoutIntervals": {},
    "nutritionHydration": {},
    "intensityMinutes": {},
    "bodyBattery": {}
  },
  "rawMetrics": [
    {"section": "Pace", "label": "Avg Pace", "value": "7:19 /km"}
  ],
  "notes": ["Any uncertainty or unreadable field."]
}

For comma decimals like 2,4, normalize numeric values internally when possible,
but keep visible strings in rawMetrics. For duration, convert HH:MM:SS or MM:SS
to minutes in summary.durationMin when total/moving/elapsed time is visible.
For cadence, Garmin may show spm. For run cadence, use Avg Run Cadence.
""".strip()
