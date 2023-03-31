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
import urllib.parse
import requests
import os

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


class KnowledgeGraph:
    def __init__(self, name, imageurl, description, url, detailed_description, wikipedia_url):
        self.name = name
        self.imageurl = imageurl
        self.description = description
        self.url = url
        self.detailed_description = detailed_description
        self.wikipedia_url = wikipedia_url


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
                summary = await crud.get_summary_url(url)
                if bool(summary) is False:
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
    script_dir = os.path.dirname(__file__)
    st_abs_file_path = os.path.join(script_dir, "static/")
    report_ids: Dict[int, str] = {}
    topics = await crud.get_group_of_topics(uid)
    log.info(topics)
    for topic in topics:
        category_counter = 1
        report_exists = False
        topic_name = topic["topic"]
        report = await crud.get_report_for_topic(topic_name)
        if report is not None:
            report_exists = True
            log.info("Inside report exists")
            existing_categories = await crud.get_categories_for_topic(topic_name)
            new_categories = await crud.get_group_of_categories_for_topic(uid, topic_name)
            merged_categories = existing_categories + new_categories
            set_of_tuples = set(tuple(d.items()) for d in merged_categories)
            categories = [dict(t) for t in set_of_tuples]
            log.info(categories)
        else:
            log.info("Inside reports doesnt exist" + str(uid))
            categories = await crud.get_group_of_categories_for_topic(uid, topic_name)
            log.info(categories)
        lines_to_read = 47
        report = ""
        line_count = 0
        with open(st_abs_file_path + 'report.html', "r") as myfile:
            for line in myfile:
                if line_count == lines_to_read:
                    break
                report += line
                line_count += 1

        knowledge_graph = await generate_knowledge_graph(topic)
        log.info(knowledge_graph.name + knowledge_graph.description)
        report += "<aside id=\"menu\"><div id=\"navigation\">"

        report += "<ul class=\"nav\" id=\"side-menu\">"
        log.info(topic_name)
        category_list = []
        for category in categories:
            category_name = category["category"]
            log.info(category_name)
            counter = NUMBERS[str(category_counter)]
            category_list.append(category_name)
            category_name_ref = category_name.replace(" ", "")
            report += "<li><a href=\"#\" class=\"toggle-button\" data-target=" + category_name_ref + "><span " \
                                                                                                     "class=\"nav" \
                                                                                                     "-label\">" + \
                      counter + "&nbsp;" + category_name + "</span></a>"
            category_counter += 1
        report += "</ul></div></aside><div id=\"wrapper\"><div class=\"row\"><div class=\"col-lg-8\"><div " \
                  "class=\"hpanel\"><div class=\"panel-body\"><div class=\"panel-group\" id=\"accordion\" " \
                  "role=\"tablist\" aria-multiselectable=\"true\"> "
        counter_category = 1
        for category_title in category_list:
            category_name_ref = category_title.replace(" ", "")
            # report += "<p>&nbsp;&nbsp;<strong>" + category_name + "</strong></p>"
            summaries = await crud.get_summaries_for_topic_categories(topic_name, category_title)
            month_year_map = {}
            count = NUMBERS[str(counter_category)]

            if count == "&#x2776;":
                report += "<div id=" + "\"" + category_name_ref + "\" class=\"panel " \
                                                                  "panel-default " \
                                                                  "toggle-content\">"
            else:
                report += "<div id=" + "\"" + category_name_ref + "\" style=\"display:none\" class=\"panel " \
                                                                  "panel-default " \
                                                                  "toggle-content\">"
            counter_category += 1
            for summary in summaries:
                if "summary" in summary:
                    ts = summary["timeFrame"]
                    try:
                        dt_object2 = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        dt_object2 = datetime.strptime(ts, '%b-%y')
                    month_name = dt_object2.strftime("%b")
                    year = dt_object2.strftime("%Y")
                    if month_name + "-" + year in month_year_map:
                        month_year_map[month_name + "-" + year].append(
                            "<p>" + summary["summary"] + "<br><strong>" + "<a href=" +
                            summary["url"] + " target=\"_blank\">" +
                            summary["title"] + "</a></strong></p>")
                    else:
                        month_year_map[month_name + "-" + year] = [
                            "<p>" + summary["summary"] + "<br><strong>" + "<a href=" +
                            summary["url"] + " target=\"_blank\">" +
                            summary["title"] + "</a></strong></p>"]
            for month_year, text in month_year_map.items():
                report += "<div class=\"panel-heading\" " \
                          "role=\"tab\" " \
                          "id=" "\"" + "heading" + category_name_ref + month_year + "\" <h4 class=\"panel-title\"><a " \
                                                                                    "data-toggle=\"collapse\" " \
                                                                                    "data-parent=\"#accordion\" href=\"" + "#collapse" + category_name_ref + month_year + "\" " \
                                                                                                                                                                          "aria-expanded=\"true\" " \
                                                                                                                                                                          "aria-controls=\"" + "#collapse" + category_name_ref + month_year + "\">" + month_year + \
                          "</a></h4></div><div id=\"collapse" + category_name_ref + month_year + "\" class=\"panel-collapse collapse\" " \
                                                                                                 "role=\"tabpanel\" " \
                                                                                                 "aria-labelledby=\"" + "heading" + category_name_ref + month_year + "\"><div " \
                                                                                                                                                                     "class=\"panel-body\"><ul> "
                if isinstance(text, list):
                    for item in text:
                        report += f"<li>{item}</li>"

                else:
                    report += "<li>" + text + "</li>"
                report += "</ul>"
                report += "</div></div>"
            report += "</div>"
        report += "</div></div></div></div>"
        report += "<div class=\"col-lg-4\"><div class=\"hpanel-hgreen\"><div class=\"panel-body\">"
        report += "<div class=\"pull-right text-right\"><div class=\"btn-group\"><i class=\"fa fa-linkedin btn btn-default btn-xs\"></i>"
        report += "</div></div><img alt=\"logo\" class=\"img-circle m-b m-t-md\" src=" + knowledge_graph.imageurl + ">"
        report += "<h3><a href=" + knowledge_graph.url + ">" + knowledge_graph.name + "</a></h3>"
        report += "<div class=\"text-muted font-bold m-b-xs\"" + knowledge_graph.description + "</div>"
        report += "<p>" + knowledge_graph.detailed_description + "<a href=" + knowledge_graph.wikipedia_url + "target" \
                                                                                                              "=\"_blank\">" + "Wikipedia" + "</p> "
        report += "</div></div></div>"
        report += "</div></div>"
        with open(st_abs_file_path + 'report.html', mode='r') as myfile:
            myreportfooter = myfile.readlines()[201:]  # Read all lines starting from line 3
            myreport = ''.join(myreportfooter)
        report += myreport
        report_name = topic_name
        if report_exists:
            report_id = await crud.updateReport(report_name, report)
        else:
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


async def generate_knowledge_graph(topic: str):
    google_api_key = "AIzaSyD-NabzmCJqMH6Tylu_amD452Mm_DJkTT0"
    service_url = 'https://kgsearch.googleapis.com/v1/entities:search'
    params = {
        'query': str(topic),
        'limit': 1,
        'indent': True,
        'key': google_api_key,
        'types': 'Organization'
    }
    url = f'{service_url}?{urllib.parse.urlencode(params)}'
    log.info(url)
    response = requests.get(url, verify=None)
    json_response = json.loads(response.text)
    log.info(json.dumps(json_response['itemListElement'][0]['result'], indent=4))

    knowledge_graph = []
    try:
        for element in json_response['itemListElement']:
            knowledge_graph = KnowledgeGraph(element['result']['name'], element['result']['image']['contentUrl'],
                                             element['result']['description'],
                                             element['result']['url'],
                                             element['result']['detailedDescription']['articleBody'],
                                             element['result']['detailedDescription']['url'])
    except KeyError as e:
        log.info('<Error: Key not found>', e)
    return knowledge_graph
