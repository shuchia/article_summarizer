# project/app/api/crud.py


from typing import Union, List

from app.models.pydantic import SummaryPayloadSchema
from app.models.tortoise import TextSummary, Report, URLSummary
from uuid import UUID


async def post(payload: SummaryPayloadSchema) -> int:
    summary = URLSummary(url=payload.url, summary="")
    await summary.save()
    return summary.id


async def create(url: str, timeframe: str, topic: str, category: str, uid: UUID) -> int:
    summary = TextSummary(url=url, timeFrame=timeframe, topic=topic, category=category, uid=uid, summary="")
    await summary.save()
    return summary.id


async def createReport(name: str, content: str) -> int:
    report = Report(name=name, report=content)
    await report.save()
    return report.id


async def get(id: int) -> Union[dict, None]:
    summary = await TextSummary.filter(id=id).first().values()
    if summary:
        return summary[0]
    return None


async def get_url_summary(id: int) -> Union[dict, None]:
    summary = await URLSummary.filter(id=id).first().values()
    if summary:
        return summary[0]
    return None


async def getReport(id: int) -> Union[dict, None]:
    report = await Report.filter(id=id).first().values()
    if report:
        return report[0]
    return None


async def get_reports_for_topic(topic: str) -> Union[dict, None]:
    report = await Report.filter(id=id).all().filter(topic__icontains=topic).all().values()
    if report:
        return report[0]
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


async def get_group_of_topics(uid: UUID) -> List:
    topics = await TextSummary.filter(uid=uid).all().group_by("topic").values("topic")
    return topics


async def get_group_of_categories_for_topic(uid: UUID, topic: str) -> List:
    categories = await TextSummary.filter(uid=uid).all().filter(topic=topic).all().group_by("category"). \
        values("category")
    return categories


async def get_summaries_for_topic_categories(uid: UUID, topic: str, category: str) -> List:
    summaries = await TextSummary.filter(uid=uid).all().filter(topic=topic).filter(category=category).all().values()
    return summaries
