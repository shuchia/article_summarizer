# project/app/api/crud.py


from typing import Union, List

from app.models.pydantic import SummaryPayloadSchema
from app.models.tortoise import TextSummary
from uuid import UUID


async def post(payload: SummaryPayloadSchema) -> int:
    summary = TextSummary(url=payload.url, summary="")
    await summary.save()
    return summary.id


async def create(url: str, timeframe: str, topic: str, category: str, uid: UUID) -> int:
    summary = TextSummary(url=url, timeFrame=timeframe, topic=topic, category=category, uid=uid, summary="")
    await summary.save()
    return summary.id


async def get(id: int) -> Union[dict, None]:
    summary = await TextSummary.filter(id=id).first().values()
    if summary:
        return summary[0]
    return None


async def get_all() -> List:
    summaries = await TextSummary.all().values()
    return summaries


async def delete(id: int) -> int:
    summary = await TextSummary.filter(id=id).first().delete()
    return summary


async def put(id: int, payload: SummaryPayloadSchema) -> Union[dict, None]:
    summary = await TextSummary.filter(id=id).update(
        url=payload.url, summary=payload.summary
    )
    if summary:
        updated_summary = await TextSummary.filter(id=id).first().values()
        return updated_summary[0]
    return None


async def get_all_for_a_task(uid: UUID) -> List:
    summaries = await TextSummary.filter(uid=uid).all().values()

    return summaries
