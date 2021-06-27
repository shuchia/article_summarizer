import time

import requests, base64
import streamlit as st
import pandas as pd
import SessionState


def get_report_download_link(report_id, name):
    """Generates a link allowing the html file to be downloaded
        in:  reportName
        out: href string
        """

    href = f'<a href="http://ec2-54-152-94-32.compute-1.amazonaws.com:8002/summaries/report/{report_id}" target="_blank">Download {name}</a>'
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
col1, col2 = st.beta_columns(2)
with col1:
    with st.form(key='form1'):
        file = st.file_uploader("Upload an excel file", type="xlsx")
        contentType = st.selectbox("Choose the type", options=content_options)

        username = st.text_input("Enter username")
        password = st.text_input("Enter password", type="password")

        submitted1 = st.form_submit_button('Generate Summaries')
        session_state = SessionState.get(name="", submitted1=False)

        if submitted1:
            session_state.submitted1 = True
        if session_state.submitted1:
            usrPass = username + ":" + password
            b64Val = base64.b64encode(usrPass)
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
                st.write("Generating summaries...")
                my_bar = st.progress(0)
                res = requests.post(f"http://web:8000/summaries/bulk", headers={"Authorization": "Basic %s" % b64Val},
                                    data=payload, files=files, verify=False)

                task = res.json()
                latest_iteration = st.empty()

                taskId = task.get("uid")
                st.write("Please use this URL to generate reports...")
                st.write(
                    "http://ec2-54-152-94-32.compute-1.amazonaws.com:8002/summaries/generateReports?uid=" + str(taskId))

                time.sleep(1)

                res = requests.get(f"http://web:8000/summaries/work/status?uid=" + str(taskId),
                                   headers={"Authorization": "Basic %s" % b64Val})

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

                    time.sleep(1)

                    res = requests.get(f"http://web:8000/summaries/work/status?uid=" + str(taskId),
                                       headers={"Authorization": "Basic %s" % b64Val})
                    taskResponse = res.json()
                    processed_urls = taskResponse.get("processed_ids")
                if taskResponse.get("status") == "Completed":
                    res = requests.get(f"http://web:8000/summaries/generateReports?uid=" + str(taskId),
                                       headers={"Authorization": "Basic %s" % b64Val})
                    processed_reports = res.json()
                    for reportId in processed_reports.keys():
                        report_name = processed_reports[reportId]
                        st.markdown(get_report_download_link(reportId, report_name), unsafe_allow_html=True)

with col2:
    with st.form(key='form2'):
        text_input = st.text_input(label='Enter a URL')
        contentType = st.selectbox("Choose the type", options=content_options)
        submitted2 = st.form_submit_button('Summarize')
        session_state = SessionState.get(name="", submitted2=False)

        if submitted2:
            session_state.submitted2 = True
        if session_state.submitted2:
            payload = {"url": text_input}
            st.write("Generating summary...")

            res = requests.post(f"http://web:8000/summaries/summary", json=payload)
            summary_id = res.json().get("id")
            time.sleep(1)
            res = requests.get(f"http://web:8000/summaries/url_summary/{summary_id}")
            summaryResponse = res.json()
            st.write(summaryResponse.get("url"))
            st.write(summaryResponse.get("summary"))
