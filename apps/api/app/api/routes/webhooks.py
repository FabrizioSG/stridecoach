from fastapi import APIRouter, Request

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/strava")
async def strava_webhook(request: Request) -> dict[str, str]:
    # TODO: Validate Strava webhook subscription and enqueue activity sync jobs.
    await request.body()
    return {"status": "received"}
