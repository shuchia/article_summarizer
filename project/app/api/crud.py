# project/app/api/crud.py


from typing import Union, List
import logging
from app.models.pydantic import SummaryPayloadSchema
from app.models.tortoise import TextSummary, Report, Summary, Usage, Subject
from uuid import UUID

from pydantic import ValidationError
from tortoise.contrib.pydantic import pydantic_model_creator
import json

log = logging.getLogger(__name__)


async def create_usage_record(params: str, headers: str, body: str, host: str, port: int, method: str, url: str) -> int:
    record = Usage(method=method, URL=url, client_host=host,
                   client_port=port, path_params=params, request_headers=headers,
                   request_body=body)

    await record.save()
    return record.id


async def get_all_usage() -> List:
    records = await Usage.all().values()
    return records


async def post(payload: SummaryPayloadSchema) -> int:
    summary = Summary(url=payload.url, summary="", text=payload.text)
    await summary.save()
    return summary.id


async def create(url: str, timeframe: str, topic: str, category: str, uid: UUID) -> int:
    summary = TextSummary(url=url, title="", timeFrame=timeframe, topic=topic, category=category, uid=uid, summary="")
    await summary.save()
    return summary.id


async def createReport(name: str, content: str) -> int:
    report = Report(name=name, report=content)
    await report.save()
    return report.id


async def updateReport(name: str, content: str) -> int:
    updated_report = await Report.filter(name__icontains=name).update(name=name, report=content)
    return updated_report


async def get(id: int) -> Union[dict, None]:
    summary = await TextSummary.filter(id=id).first().values()
    if summary:
        return summary[0]
    return None


async def get_summary_url(url: str) -> Union[dict, None]:
    summary = await TextSummary.filter(url__icontains=url).first().values()
    # log.info(summary)
    if summary:
        return summary
    return None


async def get_url_summary(id: int) -> Union[dict, None]:
    summary = await Summary.filter(id=id).first().values()
    # log.info(summary)
    if summary:
        return summary
    return None


async def getReport(id: int) -> Union[dict, None]:
    report = await Report.filter(id=id).first().values()
    if report:
        return report
    return None


async def delete_reports_for_topic(topic: str) -> Union[dict, None]:
    model_class = pydantic_model_creator(Report)
    objects = await model_class.filter(name__icontains=topic).all().values()
    deleted_objects = [obj['name'] for obj in objects]
    await model_class.all().delete()
    return deleted_objects


async def delete_all_reports() -> List:
    model_class = pydantic_model_creator(Report)
    objects = await Report.all().delete()
    return [model_class(**item.__dict__) for item in range(objects)]


async def delete_all_summaries() -> List:
    model_class = pydantic_model_creator(TextSummary)
    objects = await TextSummary.all().delete()
    return [model_class(**item.__dict__) for item in range(objects)]


async def get_report_for_topic(topic: str) -> Union[dict, None]:
    report = await Report.filter(name__icontains=topic).first().values()
    if report:
        return report
    return None


async def get_all() -> List:
    summaries = await TextSummary.all().values()
    return summaries


async def get_all_usage() -> List:
    usage = await Usage.all().values()
    return usage


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


async def get_unique_list_of_topics() -> List:
    topics = await TextSummary.filter().distinct('topic').values_list('topic', flat=True)
    return topics


async def get_unique_list_of_subjects() -> List:
    subjects = await Subject.all().distinct('name').values_list('name', flat=True)
    return subjects


async def get_topics_for_subject(subject: str) -> List:
    subject = await Subject.filter(name=subject).first()
    if subject:
        topics = subject.topics
    return topics


async def get_group_of_categories_for_topic(uid: UUID, topic: str) -> List:
    categories = await TextSummary.filter(uid=uid).all().filter(topic=topic).all().group_by("category"). \
        values("category")
    return categories


async def get_categories_for_topic(topic: str) -> List:
    try:
        categories = await TextSummary.filter(topic=topic).all().group_by("category"). \
            values("category")

    except ValidationError as e:
        log.info(e.errors())
    return categories


async def get_summaries_for_topic_categories(topic: str, category: str) -> List:
    summaries = await TextSummary.filter(topic=topic).filter(category=category).all().values()
    return summaries
