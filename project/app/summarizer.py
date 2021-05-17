# project/app/summarizer.py


import asyncio
from typing import Dict

from app.summarypro import SummarizerProcessor
from fastapi import File, UploadFile

from app.models.tortoise import TextSummary
from app.models.pydantic import Job
import pandas as pd
from app.api import crud
import logging
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


async def generate_summary(summary_id: int, url: str) -> None:
    summary_process = SummarizerProcessor(model="google/pegasus-newsroom")

    summary = summary_process.inference(
        input_url=url
    )

    await asyncio.sleep(10)

    await TextSummary.filter(id=summary_id).update(summary=summary)


async def generate_bulk_summary(task: Job, modelname: str, file: UploadFile) -> None:
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
            summary_id = await crud.create(url, timeframe, topic, category, task.uid)

            summary = summary_process.inference(input_url=url)

            await asyncio.sleep(5)

            await TextSummary.filter(id=summary_id).update(summary=summary)
            task.processed_ids[summary_id] = url
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
            report += "<p><strong>" + counter + "</strong><strong>" + category_name + "</strong></p>"
            category_counter += 1
            summaries = await crud.get_summaries_for_topic_categories(uid, topic_name, category_name)
            for summary in summaries:
                if "summary" in summary:
                    ts = summary["timeFrame"]
                    dt_object2 = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                    month_name = dt_object2.strftime("%b")
                    year = dt_object2.strftime("%Y")
                    report += "<p><strong>" + month_name + "-" + year + "</strong></p>"
                    report += "<p><strong>" + summary["summary"] + "<br>" + summary["url"] + "</strong></p>"
        report += "</body></html>"
        report_name = topic_name + date.today().strftime('%Y%m%d')
        report_id = await crud.createReport(report_name, report)
        report_ids[report_id] = report_name + ".html"
        with open(report_name + ".html", 'w+') as file1:
            file1.write(report)
    return report_ids
