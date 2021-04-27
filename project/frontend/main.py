import time

import requests
import streamlit as st
import pandas as pd
import json

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

if st.button("Summarize"):
    if file is not None and contentType is not None:
        files = {"file": file.getvalue()}
        df = pd.read_excel(file.read(), index_col=None, header=None)
        df1 = df.iloc[1:]
        total = len(df1)
        print(total)
        displayed = 0
        displayed_urls = []
        model = TYPES[contentType]
        payload = {'modelName': model}
        res = requests.post(f"http://web:8000/summaries/bulk", json=payload, files=files)
        my_bar = st.progress(0)
        task = res.json()
        latest_iteration = st.empty()

        taskId = task.get("uid")

        time.sleep(10)
        payload = {"uid": taskId}
        res = requests.post(f"http://web:8000/summaries/work/status", json=payload)
        st.write("Generating summaries...")
        taskResponse = res.json()
        processed_urls = taskResponse.get("processed_ids")

        while taskResponse.get("status") == "in_progress":
            for summaryId in processed_urls.keys():
                url = processed_urls[summaryId]
                if url not in displayed_urls:
                    res = requests.post(f"http://web:8000/summaries/{summaryId}")
                    summaryResponse = res.json()
                    st.write(summaryResponse.get("summary"))
                    displayed_urls.append(url)
                    displayed += 1
                    my_bar.progress(displayed)
                    latest_iteration.text("Processed : " + displayed)

            time.sleep(10)
            payload = {"uid": taskId}
            res = requests.post(f"http://web:8000/summaries/work/status", json=payload)
            taskResponse = res.json()
            processed_urls = taskResponse.get("processed_ids")
