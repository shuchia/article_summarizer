import time

import requests
import streamlit as st
import pandas as pd
import base64


def get_report_download_link(report):
    """Generates a link allowing the html file to be downloaded
        in:  reportName
        out: href string
        """
    with open(report, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{report}">Download {report}</a>'
    return href
    #
    # file_handle = open(report, 'r')
    # href = f'<a href="data:text/html;base64,{file_handle}">Download Report</a>'
    # return href


content_options = [
    "CNN",
    "Newsroom",
    "CNN/DailyMail",
    "Gigaword",
    "Emails",
    "Scholarly Articles",
    "Patents",
    "US Congressional bills",
    "MultiNews",
    "Medical publications",
    "Reddit",
    "WikiHow",
    "Exterme Summary"

]

TYPES = {
    "CNN": "facebook/bart-large-cnn",
    "Newsroom": "google/pegasus-newsroom",
    "CNN/DailyMail": "feathers",
    "Gigaword": "la_muse",
    "Emails": "mosaic",
    "Scholarly Articles": "starry_night",
    "Patents": "starry_night",
    "US Congressional bills": "starry_night",
    "MultiNews": "starry_night",
    "Medical publications": "starry_night",
    "Reddit": "starry_night",
    "WikiHow": "starry_night",
    "Exterme Summary": "starry_night"

}

st.set_option("deprecation.showfileUploaderEncoding", False)

st.title("Text Summarization")

file = st.file_uploader("Upload an excel file", type="xlsx")
contentType = st.selectbox("Choose the type", options=content_options)
taskResponse: {}
if st.button("Summarize"):
    if file is not None and contentType is not None:
        files = {"file": (file.name, file.getvalue(), file.type)}
        # print(file.getvalue())
        df = pd.read_excel(file.read(), index_col=None, header=None)
        df1 = df.iloc[1:]
        total = len(df1)
        print(total)
        displayed = 0
        displayed_urls = []
        model = TYPES[contentType]
        headers = {'Content-type': 'multipart/form-data'}
        payload = {"modelname": model}
        res = requests.post(f"http://web:8000/summaries/bulk", data=payload, files=files, verify=False)
        st.write("Generating summaries...")
        my_bar = st.progress(0)
        task = res.json()
        latest_iteration = st.empty()

        taskId = task.get("uid")

        time.sleep(2)

        res = requests.get(f"http://web:8000/summaries/work/status?uid=" + str(taskId))

        taskResponse = res.json()
        processed_urls = taskResponse.get("processed_ids")

        while taskResponse.get("status") == "in_progress":
            for summaryId in processed_urls.keys():
                url = processed_urls[summaryId]
                if url not in displayed_urls:
                    res = requests.get(f"http://web:8000/summaries/{summaryId}")
                    summaryResponse = res.json()
                    st.write(url)
                    st.write(summaryResponse.get("summary"))
                    displayed_urls.append(url)
                    displayed += 1
                    my_bar.progress(displayed)
                    latest_iteration.text("Processed : " + str(displayed) + " summaries")

            time.sleep(2)

            res = requests.get(f"http://web:8000/summaries/work/status?uid=" + str(taskId))
            taskResponse = res.json()
            processed_urls = taskResponse.get("processed_ids")
if taskResponse.get("status") == "Completed":
    if st.button("Generate Reports"):
        res = requests.get(f"http://web:8000/summaries/generateReports?uid=" + str(taskId))
        processed_reports = res.get("report_ids")
        for reportId in processed_reports.keys():
            report_name = processed_reports[reportId]
            st.markdown(get_report_download_link(report_name), unsafe_allow_html=True)
