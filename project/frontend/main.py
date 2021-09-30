import time

import requests, base64
import streamlit as st
import pandas as pd
import SessionState


def main():
    st.set_page_config(
        page_title="FiPointer Text Summary",
        page_icon="🧊",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://www.extremelycoolapp.com/help',
            'Report a bug': "https://www.extremelycoolapp.com/bug",
            'About': "# Text summarization for news articles using machine learning NLP models"
        }
    )
    # Register your pages
    pages = {
        "Summarizer ": page_first,
        "Bulk Summaries ": page_second,
        "Generate Reports": page_third,
        "Retrieve Reports": page_fourth
    }

    st.sidebar.title("Summary Wizard")

    # Widget to select your page, you can choose between radio buttons or a selectbox
    page = st.sidebar.radio("Go to", tuple(pages.keys()))
    # page = st.sidebar.selectbox("Select your page", tuple(pages.keys()))

    # Display the selected page
    pages[page]()


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
    "FiPointer-Basic",
    # "Newsroom",
    # "CNN/DailyMail",
    # "Gigaword",
    # "Emails",
    # "Scholarly Articles",
    # "Patents",
    # "US Congressional bills",
    # "MultiNews",
    # "Medical publications",
    # "Reddit",
    # "WikiHow",
    # "Exterme Summary"

]

TYPES = {
    "FiPointer-Basic": "facebook/bart-large-cnn",
    # "Newsroom": "google/pegasus-newsroom",
    # "CNN/DailyMail": "feathers",
    # "Gigaword": "la_muse",
    # "Emails": "mosaic",
    # "Scholarly Articles": "starry_night",
    # "Patents": "starry_night",
    # "US Congressional bills": "starry_night",
    # "MultiNews": "starry_night",
    # "Medical publications": "starry_night",
    # "Reddit": "starry_night",
    # "WikiHow": "starry_night",
    # "Exterme Summary": "starry_night"

}

length_options = ['short', 'medium', 'long']


def page_second():
    st.set_option("deprecation.showfileUploaderEncoding", False)
    st.title("Generate summary reports")
    with st.form(key='form1'):
        file = st.file_uploader("Upload an excel file", type="xlsx")
        contentType = st.selectbox("Choose the type", options=content_options)
        length = st.select_slider("Choose  length of the summary", options=length_options)

        username = st.text_input("Enter username")
        password = st.text_input("Enter password", type="password")

        submitted1 = st.form_submit_button('Generate Summaries')
        session_state = SessionState.get(name="", submitted1=False)

        if submitted1:
            session_state.submitted1 = True
        if session_state.submitted1:
            usrPass = username + ":" + password
            b64Val = base64.b64encode(usrPass.encode()).decode()
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
                payload = {"model_name": model, "length": length}
                st.write("Generating summaries...")
                my_bar = st.progress(0)
                print(usrPass)
                print(b64Val)
                headers = {"Authorization": "Basic %s" % b64Val}
                res = requests.post(f"http://web:8000/summaries/bulk", data=payload, files=files,
                                    headers=headers, verify=False)

                task = res.json()
                print(task)
                latest_iteration = st.empty()

                taskId = task.get("uid")
                st.write("Please use this UID to generate reports using the nav menu...")
                st.write(str(taskId))

                # time.sleep(1)
                #
                # res = requests.get(f"http://web:8000/summaries/work/status?uid=" + str(taskId), headers=headers)
                #
                # taskResponse = res.json()
                # processed_urls = taskResponse.get("processed_ids")
                #
                # while taskResponse.get("status") == "in_progress":
                #     for summaryId in processed_urls.keys():
                #         url = processed_urls[summaryId]
                #         if url not in displayed_urls:
                #             res = requests.get(f"http://web:8000/summaries/{summaryId}",
                #                                headers=headers)
                #             summaryResponse = res.json()
                #             st.write(url)
                #             st.write(summaryResponse.get("summary"))
                #             displayed_urls.append(url)
                #             displayed += 1
                #             my_bar.progress(displayed)
                #             latest_iteration.text("Processed : " + str(displayed) + " summaries")
                #
                #     time.sleep(1)
                #
                #     res = requests.get(f"http://web:8000/summaries/work/status?uid=" + str(taskId),
                #                        headers=headers)
                #     taskResponse = res.json()
                #     processed_urls = taskResponse.get("processed_ids")
                # if taskResponse.get("status") == "Completed":
                #     res = requests.get(f"http://web:8000/summaries/generateReports?uid=" + str(taskId),
                #                        headers=headers)
                #     processed_reports = res.json()
                #     for reportId in processed_reports.keys():
                #         report_name = processed_reports[reportId]
                #         st.markdown(get_report_download_link(reportId, report_name), unsafe_allow_html=True)

    with col2:
        with st.form(key='form2'):
            text_input = st.text_input(label='Enter a URL')
            contentType = st.selectbox("Choose the type", options=content_options)
            length = st.select_slider("Choose  length of the summary", options=length_options)
            submitted2 = st.form_submit_button('Summarize')
            session_state = SessionState.get(name="", submitted2=False)

            if submitted2:
                #     session_state.submitted2 = True
                # if session_state.submitted2:
                model = TYPES[contentType]
                payload = {"url": text_input,
                           "model_name": model,
                           "length": length}
                st.write("Generating summary...")

                res = requests.post(f"http://web:8000/summaries/summary", json=payload)
                # time.sleep(10)
                summary_id = res.json().get("id")
                # print (summary_id)
                status = res.json().get("status")
                # print(status)
                taskId = res.json().get("task_id")
                while status == "in_progress":
                    res = requests.get(f"http://web:8000/summaries/task/status?uid=" + str(taskId))
                    taskResponse = res.json()
                    if taskResponse.get("status") == "Completed":
                        res = requests.get(f"http://web:8000/summaries/url_summary/{summary_id}/")
                        summaryResponse = res.json()
                        st.write(summaryResponse.get("url"))
                        # print(summaryResponse)
                        st.write(summaryResponse.get("summary"))
                        break


def page_first():
    st.title("Text Summarizer")
    col1, col2 = st.columns([5, 5])
    summaryResponse = ''
    with col1:
        with st.form(key='summarize'):
            placeholder = st.empty()
            text_input = placeholder.text_area('Enter text to summarize')
            url_input = st.text_input(label='Enter a URL')
            if url_input != '':
                placeholder.empty()

            length = st.select_slider("Choose  length of the summary", options=length_options)
            submitted2 = st.form_submit_button('Summarize')
            if submitted2:
                #     session_state.submitted2 = True
                # if session_state.submitted2:
                model = "facebook/bart-large-cnn"
                if url_input != '':
                    payload = {"url": url_input,
                               "model_name": model,
                               "length": length}
                    st.write("Generating summary...")

                    res = requests.post(f"http://web:8000/summaries/summary", json=payload)
                    # time.sleep(10)
                    summary_id = res.json().get("id")
                    # print (summary_id)
                    status = res.json().get("status")
                    # print(status)
                    taskId = res.json().get("task_id")
                    while status == "in_progress":
                        res = requests.get(f"http://web:8000/summaries/task/status?uid=" + str(taskId))
                        taskResponse = res.json()
                        if taskResponse.get("status") == "Completed":
                            res = requests.get(f"http://web:8000/summaries/url_summary/{summary_id}/")
                            summaryResponse = res.json()
                            # st.write(summaryResponse.get("url"))
                            # print(summaryResponse)
                            # st.write(summaryResponse.get("summary"))
                            break
    with col2:
        placeholder = st.empty()
        if summaryResponse != '':
            placeholder.text_input('', value=summaryResponse.get("url"))
            # print(summaryResponse)
            placeholder.text_area('', value=summaryResponse.get("summary"), height=1000)


def page_third():
    st.title("Generate reports")
    with st.form(key='generate'):
        taskId = st.text_input(label='Enter ID')
        username = st.text_input("Enter username")
        password = st.text_input("Enter password", type="password")
        submitted2 = st.form_submit_button('Generate')
        if submitted2:
            usrPass = username + ":" + password
            b64Val = base64.b64encode(usrPass.encode()).decode()
            headers = {"Authorization": "Basic %s" % b64Val}
            res = requests.get(f"http://web:8000/summaries/generateReports?uid=" + str(taskId),
                               headers=headers)
            processed_reports = res.json()
            for reportId in processed_reports.keys():
                report_name = processed_reports[reportId]
                st.markdown(get_report_download_link(reportId, report_name), unsafe_allow_html=True)


def page_fourth():
    st.title("Retrieve Reports")
    with st.form(key='retrieve'):
        topic = st.text_input(label='Enter Topic')
        username = st.text_input("Enter username")
        password = st.text_input("Enter password", type="password")
        submitted3 = st.form_submit_button('Retrieve')
        if submitted3:
            usrPass = username + ":" + password
            b64Val = base64.b64encode(usrPass.encode()).decode()
            headers = {"Authorization": "Basic %s" % b64Val}
            res = requests.get(f"http://web:8000/summaries/getReports?topic=" + str(topic),
                               headers=headers)
            processed_reports = res.json()
            for reportId in processed_reports.keys():
                report_name = processed_reports[reportId]
                st.markdown(get_report_download_link(reportId, report_name), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
