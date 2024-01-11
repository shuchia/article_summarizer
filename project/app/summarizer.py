# project/app/summarizer.py


import asyncio
import sys
from typing import Dict
import logging
from app.summarypro import SummarizerProcessor
from app.send_email import send_email
from fastapi import File, UploadFile, Request
from fastapi.responses import HTMLResponse

from app.models.tortoise import TextSummary, Summary, Topic, Subject
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
from PIL import Image
import io
import more_itertools

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


async def get_reports_landing() -> None:
    script_dir = os.path.dirname(__file__)
    st_abs_file_path = os.path.join(script_dir, "static/")
    subjects = await crud.get_unique_list_of_subjects()
    lines_to_read = 53
    report = ""
    line_count = 0
    with open(st_abs_file_path + 'report.html', "r") as myfile:
        for line in myfile:
            if line_count == lines_to_read:
                break
            report += line
            line_count += 1
    report += "<aside id=\"menu\"><div id=\"navigation\">"
    report += "<ul class=\"nav\" id=\"side-menu\">"
    subject_list = []
    subject_meta = ""
    for subject in subjects:
        subject_name = subject["name"]

        subject_list.append(subject_name)
        subject_name_replaced = subject_name.replace(" ", "")
        # Escape the characters "&" and "-"
        subject_name_ref = subject_name_replaced.replace("&", "\\&").replace("-", "\\-")
        report += "<li><a href=\"#\" class=\"toggle-button\" data-target=" + subject_name_ref + "><span " \
                                                                                                "class=\"nav" \
                                                                                                "-label\">" + \
                  "&nbsp;" + subject_name + "</span></a>"

        subject_meta += subject_name + " "
    report += "</ul></div></aside><div id=\"wrapper\"> "
    counter_subject = 1
    for subject_title in subject_list:
        log.info(subject_title)
        subject_name_replaced = subject_title.replace(" ", "")
        subject_name_ref = subject_name_replaced.replace("&", "\\&").replace("-", "\\-")
        subject = await Subject.get(name=subject_title)
        topics = await subject.topics
        # log.info(topics)
        count = NUMBERS[str(counter_subject)]

        if count == "&#x2776;":
            report += "<div class=\"row\" id=" + "\"" + subject_name_ref + "\" class=\"toggle-content\">"
        else:
            report += "<div class=\"row\" id=" + "\"" + subject_name_ref + "\" style=\"display:none\" class=\"toggle-content\">"
        counter_subject += 1
        groups = {}
        for topic in topics:
            topic_name = topic.name
            first_letter = topic_name[0].upper()
            if first_letter in groups:
                groups[first_letter].append(topic_name)
            else:
                groups[first_letter] = [topic_name]

        collated_groups = {}
        for first_letter, group in groups.items():
            group_key = len(group)
            if group_key in collated_groups:
                if first_letter in collated_groups[group_key]:
                    collated_groups[group_key][first_letter] += group
                else:
                    collated_groups[group_key][first_letter] = group
            else:
                collated_groups[group_key] = {first_letter: group}

        num_groups = 1  # we only want one group
        subgroup_size = len(collated_groups) // num_groups  # size of each subgroup

        # divide the collated groups into multiple equal-sized subgroups
        subgroups = list(more_itertools.chunked(collated_groups.items(), subgroup_size))

        # combine all the groups into one
        combined_groups = {}
        for subgroup in subgroups:
            for group_size, group_dict in subgroup:
                for first_letter, group in group_dict.items():
                    combined_groups[first_letter] = group

        # print the combined groups
        # for first_letter, group in combined_groups.items():
        # log.info(f"{first_letter}: {group}")
        # Divide the subjects into 3 subgroups
        num_subgroups = 3
        subgroup_size = (len(combined_groups) + num_subgroups - 1) // num_subgroups
        subgroups = [dict(list(combined_groups.items())[i:i + subgroup_size]) for i in
                     range(0, len(combined_groups), subgroup_size)]

        # Sort each subgroup by key
        for subgroup_index, subgroup in enumerate(subgroups):
            sorted_subgroup = dict(sorted(subgroup.items()))
            log.info(sorted_subgroup)
            report += "<div class=\"col-lg-4\"><div class=\"hpanel\"><div class=\"panel-body\">" \

            for key_index, (key, value_list) in enumerate(sorted_subgroup.items()):
                list_header_id = f"list-header-{subgroup_index}-{key_index}"
                list_items_id = f"list-items-{subgroup_index}-{key_index}"

                # Add data-toggle and data-target attributes for Bootstrap Collapse
                report += f"<div class=\"dd\" id=\"nestable2\">" \
                          f"<ol class=\"dd-list\">" \
                          f"<li class=\"dd-item\" data-id=\"{subgroup_index + 1}\" data-toggle=\"collapse\" " \
                          f"data-target=\"#nested-list-{list_items_id}\" aria-expanded=\"false\">" \
                          f"<div class=\"dd-handle\">" \
                          f"<span class=\"label h-bg-navy-blue\"><i class=\"fa fa-users\"></i></span>{key}" \
                          f"</div>" \
                          f"<ol id=\"nested-list-{list_items_id}\" class=\"collapse dd-list\">"

                for value_index, value in enumerate(value_list):
                    report += f"<li class=\"dd-item\" data-id=\"{subgroup_index + 1}-{key_index + 1}-{value_index + 1}\">" \
                              f"<div class=\"dd-handle\">" \
                              f"<a href=\"getReport?topic={value}\" target=\"_blank\">" \
                              f"<span class=\"label h-bg-navy-blue\"><i class=\"fa fa-cog\"></i></span>{value}</a>" \
                              f"</div>" \
                              f"</li>"

                report += "</ol></li></ol></div>"
            report += "</div></div>"
        report += "</div></div></div>"
        report += """
        <script>
            document.addEventListener("DOMContentLoaded", function () {
                var nestedLists = document.querySelectorAll('.dd');
                nestedLists.forEach(function (nestedList) {
                    nestedList.addEventListener('show.bs.collapse', function () {
                        // Handle expand event
                    });
                    nestedList.addEventListener('hide.bs.collapse', function () {
                        // Handle collapse event
                    });
                });
            });
        </script>
        """
        with open(st_abs_file_path + 'report.html', mode='r') as myfile:
            myreportfooter = myfile.readlines()[210:]  # Read all lines starting from line 201
            myreport = ''.join(myreportfooter)
        report += myreport
    return HTMLResponse(content=report, status_code=200)


async def generate_report(uid: UUID) -> None:
    script_dir = os.path.dirname(__file__)
    st_abs_file_path = os.path.join(script_dir, "static/")
    log.info(st_abs_file_path)
    report_ids: Dict[int, str] = {}
    topics = await crud.get_group_of_topics(uid)
    log.info(topics)
    subject = await Subject.create(name="Companies")
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
        lines_to_read = 53
        report = ""
        line_count = 0
        with open(st_abs_file_path + 'report.html', "r") as myfile:
            for line in myfile:
                if line_count == lines_to_read:
                    break
                report += line
                line_count += 1

        try:
            knowledge_graph = await generate_knowledge_graph(topic_name)
            log.info(knowledge_graph.name + knowledge_graph.description)
        # Catch any exceptions that may arise
        except Exception as e:
            log.info("An error occurred:", e)
            knowledge_graph = None

        report += "<aside id=\"menu\"><div id=\"navigation\">"

        report += "<ul class=\"nav\" id=\"side-menu\">"
        log.info(topic_name)
        category_list = []
        category_meta = ""
        for category in categories:
            category_name = category["category"]
            log.info(category_name)
            counter = NUMBERS[str(category_counter)]
            category_list.append(category_name)
            category_name_replaced = category_name.replace(" ", "")
            # Escape the characters "&" and "-"
            category_name_ref = category_name_replaced.replace("&", "\\&").replace("-", "\\-")
            report += "<li><a href=\"#\" class=\"toggle-button\" data-target=" + category_name_ref + "><span " \
                                                                                                     "class=\"nav" \
                                                                                                     "-label\">" + \
                      counter + "&nbsp;" + category_name + "</span></a>"
            category_counter += 1
            category_meta += category_name + " "
        report += "</ul></div></aside><div id=\"wrapper\"><div class=\"row\"><div class=\"col-lg-8\"><div " \
                  "class=\"hpanel\"><div class=\"panel-body\"><div class=\"panel-group\" id=\"accordion\" " \
                  "role=\"tablist\" aria-multiselectable=\"true\"> "

        counter_category = 1
        for category_title in category_list:
            category_name_replaced = category_title.replace(" ", "")
            category_name_ref = category_name_replaced.replace("&", "\\&").replace("-", "\\-")
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
                    http_index = summary["url"].find("http")
                    if http_index != -1:
                        url_string = summary["url"][http_index:]
                    if month_name + "-" + year in month_year_map:
                        month_year_map[month_name + "-" + year].append(
                            "<p>" + summary["summary"] + "<br><strong>" + "<a href=" +
                            url_string + " target=\"_blank\">" +
                            summary["title"] + "</a></strong></p>")
                    else:
                        month_year_map[month_name + "-" + year] = [
                            "<p>" + summary["summary"] + "<br><strong>" + "<a href=" +
                            url_string + " target=\"_blank\">" +
                            summary["title"] + "</a></strong></p>"]
            for month_year, text in month_year_map.items():
                report += "<div class=\"panel-heading\" " \
                          "role=\"tab\" " \
                          "id=" "\"" + "heading" + category_name_ref + month_year + "\" <h4 class=\"panel-title\"><a " \
                                                                                    "data-toggle=\"collapse\" " \
                                                                                    "data-parent=\"#accordion\" href=\"" + "#collapse" + category_name_ref + month_year + "\" " \
                                                                                                                                                                          "aria-expanded=\"true\" " \
                                                                                                                                                                          "aria-controls=\"" + "#collapse" + category_name_ref + month_year + "\">" + month_year + \
                          "</a></h4></div><div id=\"collapse" \
                          + category_name_ref + month_year + "\" class=\"panel-collapse collapse\" " \
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

        if knowledge_graph is not None:
            if knowledge_graph.imageurl != "":
                thumbnail_file = st_abs_file_path + "thumbnails/thumbnail" + topic_name.replace(" ", "") + '.png'
                # Download the image from the URL
                log.info(thumbnail_file)
                with urllib.request.urlopen(knowledge_graph.imageurl) as url:
                    image_bytes = url.read()
                    with Image.open(io.BytesIO(image_bytes)) as image:
                        # Generate a thumbnail image
                        thumbnail_size = (100, 100)
                        image.thumbnail(thumbnail_size)
                        image.convert("RGB")
                        image.save(thumbnail_file, "PNG")

            report += "<div class=\"col-lg-4\"><div class=\"hpanel hgreen\"><div class=\"panel-body\"><div class=\"panel-group\">"
            report += "<div class=\"pull-right text-right\"><div class=\"btn-group\"><i class=\"fa fa-linkedin btn btn-default btn-xs\"></i>"
            report += "</div></div><img alt=\"logo\" class=\"img-circle m-b m-t-md\" src=" + "/static/thumbnails/thumbnail" + topic_name.replace(
                " ", "") + ".png" + ">"
            report += "<h3><a href=" + knowledge_graph.url + " target=_blank\">" + knowledge_graph.name + "</a></h3>"
            report += "<div class=\"text-muted font-bold m-b-xs\">" + knowledge_graph.description + "</div>"
            report += "<p>" + knowledge_graph.detailed_description + "<a href=" + knowledge_graph.wikipedia_url + " target" \
                                                                                                                  "=\"_blank\">" + "Wikipedia" + "</a></p> "
            report += "</div></div></div></div>"
        report += "</div></div>"
        with open(st_abs_file_path + 'report.html', mode='r') as myfile:
            myreportfooter = myfile.readlines()[208:]  # Read all lines starting from line 201
            myreport = ''.join(myreportfooter)
            myreport += "window.addEventListener(\'DOMContentLoaded\', function()  {" \
                        "document.title = \"" + topic_name + "\" ;" \
                                                             "var meta = document.createElement(\"meta\");" \
                                                             "meta.setAttribute(\"name\",\"description\");" \
                                                             "meta.setAttribute(\"content\",\"" + topic_name + " " + category_meta + "\" );" \
                                                                                                                                     "document.head.appendChild(meta);" \
                                                                                                                                     "}); </script></body></html>"
        if knowledge_graph is not None:
            await Topic.create(name=topic_name, description=knowledge_graph.description, subject=subject)
        else:
            await Topic.create(name=topic_name, description="", subject=subject)
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
        imageurl = ""
        name = ""
        detailed_description = ""
        url = ""
        description = ""
        wikipedia_url = ""
        for element in json_response['itemListElement']:
            # check if the "description" property exists for the top search result
            if 'image' in element['result']:
                imageurl = element['result']['image']['contentUrl']
            if 'name' in element['result']:
                name = element['result']['name']
            if 'description' in element['result']:
                description = element['result']['description']
            if 'url' in element['result']:
                url = element['result']['url']
            if 'detailedDescription' in element['result']:
                detailed_description = element['result']['detailedDescription']['articleBody']
                wikipedia_url = element['result']['detailedDescription']['url']
            knowledge_graph = KnowledgeGraph(name, imageurl, description, url, detailed_description, wikipedia_url)

    except KeyError as e:
        log.info('<Error: Key not found>', e)
    return knowledge_graph
