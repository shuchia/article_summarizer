# project/app/summarizer.py


import asyncio
import sys
from typing import Dict
import logging
from app.summarypro import SummarizerProcessor
from app.send_email import send_email
from fastapi import File, UploadFile, Request

from app.models.tortoise import TextSummary, Summary
from app.models.pydantic import Job
import pandas as pd

from uuid import UUID
from datetime import date, datetime
from starlette.routing import Match
from app.api import crud
import json

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
STATIC_HTML = """
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* {
  box-sizing: border-box;
}

/* Add a gray background color with some padding */
body {
  font-family: Arial;
  padding: 20px;
  background: #f1f1f1;
}

/* Header/Blog Title */
.header {
  padding: 30px;
  font-size: 40px;
  text-align: center;
  background: white;
}

/* Create two unequal columns that floats next to each other */
/* Left column */
.leftcolumn {   
  float: left;
  width: 75%;
}

/* Right column */
.rightcolumn {
  float: left;
  width: 25%;
  padding-left: 20px;
}

/* Fake image */
.fakeimg {
  background-color: #aaa;
  width: 100%;
  padding: 20px;
}

/* Add a card effect for articles */
.card {
   background-color: white;
   padding: 20px;
   margin-top: 20px;
}

/* Clear floats after the columns */
.row:after {
  content: "";
  display: table;
  clear: both;
}

/* Footer */
.footer {
  padding: 20px;
  text-align: center;
  background: #ddd;
  margin-top: 20px;
}

/* Responsive layout - when the screen is less than 800px wide, make the two columns stack on top of each other instead of next to each other */
@media screen and (max-width: 800px) {
  .leftcolumn, .rightcolumn {   
    width: 100%;
    padding: 0;
  }
}
</style>
</head>
"""


def isNaN(string):
    return string != string or string == 'nan'


async def generate_summary(task: Job, summary_id: int, url: str, text: str, model_name: str, length: str) -> None:
    summary_process = SummarizerProcessor(model=model_name)

    summary = await summary_process.inference(
        input_url=url, input_text=text, length=length
    )
    log.info(summary_id)
    await asyncio.sleep(1)
    log.info(summary)
    try:
        await Summary.filter(id=summary_id).update(summary=summary)
    except:
        log.exception("summary_id " + str(summary_id))
    if url is not None:
        task.processed_ids[summary_id] = url
    elif text != "":
        task.processed_ids[summary_id] = text
    task.status = "Completed"


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

                summary = await summary_process.inference(input_url=url, input_text='', length=length)
                title = await summary_process.get_title(input_url=url, input_text='', length=length)

                await asyncio.sleep(1)

                await TextSummary.filter(id=summary_id).update(summary=summary, title=title)
                task.processed_ids[summary_id] = url
            except:
                log.exception("url errored " + url)
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
        report = await crud.get_report_for_topic(topic)
        if report:
            categories = await crud.get_group_of_categories_for_topic(uid, topic_name)
            category_added = False
            for category in categories:
                category_name = category["category"]
                position = report.find(category_name)
                if position != -1 or category_added:
                    category_added = True
                    start_index = position + len(category_name)
                    remaining_report = report[start_index:]
                    summaries = await crud.get_summaries_for_topic_categories(uid, topic_name, category_name)
                    month_year_added = False
                    for summary in summaries:
                        if "summary" in summary:
                            ts = summary["timeFrame"]
                            dt_object2 = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                            month_name = dt_object2.strftime("%b")
                            year = dt_object2.strftime("%Y")
                            month_year_found = remaining_report.find(month_name + "-" + year)
                            if month_year_found != -1 or month_year_added:
                                report = report[:month_year_found + len(month_name + "-" + year)] + "<p><strong>" + \
                                         summary[
                                             "summary"] + "<br>" + "<a href=" + summary[
                                             "url"] + " target=\"_blank>\">" + summary["title"] + "</a></strong></p>" + \
                                         report[month_year_found + len(month_name + "-" + year):]
                            else:
                                report = report[:position + len(
                                    category_name)] + "<p><strong>" + month_name + "-" + year + "</strong></p>" \
                                                                                                "<p><strong>" + summary[
                                             "summary"] + "<br>" + "<a href=" + summary[
                                             "url"] + " target=\"_blank>\">" + summary["title"] + "</a></strong></p>" + \
                                         report[position + len(category_name):]
                                month_year_added = True
                else:
                    counter = NUMBERS[str(category_counter)]
                    report += "<p><strong>" + counter + "&nbsp;</strong>"
                    report += "<p>&nbsp;&nbsp;<strong>" + category_name + "</strong></p>"
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
        else:
            report = STATIC_HTML
            topic_name = topic["topic"]
            report += "<div class=\"header\"><h2>" + topic_name + "</h2></div><div class=\"row\"><div " \
                                                                  "class=\"leftcolumn\"> "
            categories = await crud.get_group_of_categories_for_topic(uid, topic_name)
            for category in categories:
                category_name = category["category"]
                counter = NUMBERS[str(category_counter)]
                report += "<div class =\"card\"><h2>"
                report += counter + category_name + "</h2>"
                # report += "<p>&nbsp;&nbsp;<strong>" + category_name + "</strong></p>"
                category_counter += 1
                summaries = await crud.get_summaries_for_topic_categories(uid, topic_name, category_name)
                month_year_map = {}
                for summary in summaries:
                    if "summary" in summary:
                        ts = summary["timeFrame"]
                        dt_object2 = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                        month_name = dt_object2.strftime("%b")
                        year = dt_object2.strftime("%Y")
                        if month_name + "-" + year in month_year_map:
                            month_year_map[month_name + "-" + year].append(summary["summary"] + "<br>" + "<a href=" +
                                                                           summary["url"] + " target=\"_blank>\">" +
                                                                           summary["title"] + "</a>")
                        else:
                            month_year_map[month_name + "-" + year] = [summary["summary"] + "<br>" + "<a href=" +
                                                                       summary["url"] + " target=\"_blank>\">" +
                                                                       summary["title"] + "</a>"]
                for month_year, text in month_year_map.items():
                    report += "<h5>" + month_year + "</h5>"
                    if isinstance(text, list):
                        report += "<p>" + '<br>'.join(text) + "</p>"
                    else:
                        report += "<p>" + text + "</p>"
            report += "</body></html>"
            report_name = topic_name
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


async def log_requests(request: Request):
    log.info(f"{request.method} {request.url}")
    routes = request.app.router.routes
    params = json.dumps(dict(request.path_params))
    log.info(params)
    log.info("Params:")
    for route in routes:
        match, scope = route.matches(request)
        if match == Match.FULL:
            for name, value in scope["path_params"].items():
                log.info(f"\t{name}: {value}")

    log.info("Headers:")
    for name, value in request.headers.items():
        log.info(f"\t{name}: {value}")
    headers = json.dumps(dict(request.headers))
    log.info(headers)
    log.info("Body:")
    body = await request.json()
    log.info(body)
    log.info("client_host: " + request.client.host)
    log.info("client_port: " + str(request.client.port))
    await crud.create_usage_record(params, headers, body, request.client.host, request.client.port, request.method,
                                   request.url)
