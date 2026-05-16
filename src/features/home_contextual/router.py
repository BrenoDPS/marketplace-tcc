from fastapi import APIRouter

from src.features.home_contextual.composer import compose_home
from src.schemas.sdui import ScreenResponse

router = APIRouter(tags=["Home Contextual"])


@router.get("/home", response_model=ScreenResponse)
async def get_home(context: str = "default") -> ScreenResponse:
    return await compose_home(context)
