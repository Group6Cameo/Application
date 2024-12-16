from fastapi import APIRouter, HTTPException, Depends, Body, Query
from rpi_control.api.services.vast_ai_service import VastAIService

router = APIRouter(prefix="/server", tags=["server"])
vast_service = VastAIService()


@router.post("/start")
async def start_server(
    body: dict = Body(...),
):
    """Start a VastAI instance."""
    if not body.get("instance_id"):
        raise HTTPException(status_code=400, detail="Instance ID is required")
    result = await vast_service.start_instance(body.get("instance_id"))
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@router.post("/stop")
async def stop_server(
    body: dict = Body(...),
):
    """Stop a VastAI instance."""
    if not body.get("instance_id"):
        raise HTTPException(status_code=400, detail="Instance ID is required")
    result = await vast_service.stop_instance(body.get("instance_id"))
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@router.get("/status")
async def server_status(
    instance_id: str = Query(...),
):
    """Get the status of a VastAI instance."""
    if not instance_id:
        raise HTTPException(status_code=400, detail="Instance ID is required")
    result = await vast_service.get_instance_status(instance_id)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@router.post("/create")
async def create_server(
):
    """Create a new VastAI instance."""
    result = await vast_service.create_instance()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result
