# project/app/summarizer.py


import asyncio
import sys
from typing import Dict
import logging
from app.summarypro import SummarizerProcessor
from app.send_email import send_email
from fastapi import File, UploadFile

from app.models.tortoise import TextSummary, URLSummary
from app.models.pydantic import Job
import pandas as pd
from app.api import crud

from uuid import UUID
from datetime import date, datetime

log = logging.getLogger(__name__)

NUMBERS = {"1": "&#x2776;",
           "2": '&#x2777;',
           "3": '&#x2778;',
           "4": '&#x2779;',
           "5": '&#x277A;',
           "6": '&#x277B;',
           "7": '&#x277C;',
           "8": '&#x277D;',
           "9": '&#x277E;',
           "10": '&#x277F;'
           }


def isNaN(string):
    return string != string or string == 'nan'


async def generate_summary(summary_id: int, url: str, model_name: str, length: str) -> None:
    summary_process = SummarizerProcessor(model=model_name)
    try:
        summary = await summary_process.inference(
            input_url=url, length=length
        )

        await asyncio.sleep(1)

        await URLSummary.filter(id=summary_id).update(summary=summary)
    except:
        log.error("url errored " + url + sys.exc_info()[0])


async def generate_bulk_summary(task: Job, modelname: str, file: UploadFile, email: str, full_name: str,
                                length: str) -> None:
    summary_process = SummarizerProcessor(model=modelname)

    df = pd.read_excel(file.file.read(), index_col=None, header=0)

    # df1 = df.iloc[1:]
    # logger.info(len(df))
    for index, row in df.iterrows():
        url = str(row['URL'])
        timeframe = str(row['MM/YY'])
        topic = str(row['Topic'])
        category = str(row['Category'])
        # url = df1.iat[ind, 0]
        # log.info(url)
        if isNaN(url) is False:
            log.info(url)
            try:
                summary_id = await crud.create(url, timeframe, topic, category, task.uid)

                summary = await summary_process.inference(input_url=url, length=length)

                await asyncio.sleep(1)

                await TextSummary.filter(id=summary_id).update(summary=summary)
                task.processed_ids[summary_id] = url
            except:
                log.error("url errored " + url + sys.exc_info()[0])
                pass
            finally:
                pass
    log.info(await(send_email(email, str(task.uid), full_name)))
    task.status = "Completed"


async def generate_report(uid: UUID) -> None:
    report_ids: Dict[int, str] = {}
    topics = await crud.get_group_of_topics(uid)
    for topic in topics:
        category_counter = 1
        report = "<!DOCTYPE html><html><head><title></title></head><body><blockquote><p><strong> "
        topic_name = topic["topic"]
        report += topic_name + "</strong></p>"
        categories = await crud.get_group_of_categories_for_topic(uid, topic_name)
        for category in categories:
            category_name = category["category"]
            counter = NUMBERS[str(category_counter)]
            report += "<p><strong>" + counter + "&nbsp;</strong><strong>" + category_name + "</strong></p>"
            category_counter += 1
            summaries = await crud.get_summaries_for_topic_categories(uid, topic_name, category_name)
            for summary in summaries:
                if "summary" in summary:
                    ts = summary["timeFrame"]
                    dt_object2 = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                    month_name = dt_object2.strftime("%b")
                    year = dt_object2.strftime("%Y")
                    report += "<p><strong>" + month_name + "-" + year + "</strong></p>"
                    report += "<p><strong>" + summary["summary"] + "<br>" + "<a href=" + summary[
                        "url"] + " target=\"_blank>\">" + summary["url"] + "</a></strong></p> "
        report += "</body></html>"
        report_name = topic_name + date.today().strftime('%Y%m%d')
        report_id = await crud.createReport(report_name, report)
        report_ids[report_id] = report_name + ".html"
        # with open(report_name + ".html", 'w+') as file1:
        # file1.write(report)
    return report_ids


async def get_reports(uid: UUID) -> None:
    report_ids: Dict[int, str] = {}
    topics = await crud.get_group_of_topics(uid)
    for topic in topics:
        report = await crud.get_reports_for_topic(topic)

        report_ids[report["id"]] = report["name"]
        # with open(report_name + ".html", 'w+') as file1:
        # file1.write(report)
    return report_ids


async def get_reports_for_topic(topic: str) -> None:
    report_ids: Dict[int, str] = {}
    reports = await crud.get_reports_for_topic(topic)
    for report in reports:
        report_ids[report["id"]] = report["name"]
        # with open(report_name + ".html", 'w+') as file1:
        # file1.write(report)
    return report_ids
