import time

import requests
import streamlit as st
import pandas as pd
import json

TYPES = {
    "general": "bart-large-cnn",
    "composition 6": "composition_vii",
    "feathers": "feathers",
    "la_muse": "la_muse",
    "mosaic": "mosaic",
    "starry night": "starry_night",
    "the scream": "the_scream",
    "the wave": "the_wave",
    "udnie": "udnie",
}

st.set_option("deprecation.showfileUploaderEncoding", False)

st.title("Text Summarization")

file = st.file_uploader("Upload an excel file", type="xlsx")

contentType = st.selectbox("Choose the type", [i for i in TYPES.values()])

if st.button("Summarize"):
    if file is not None and contentType is not None:
        files = {"file": file.getvalue()}
        df = pd.read_excel(file.read(), index_col=None, header=None)
        df1 = df.iloc[1:]
        total = len(df1)
        print(total)
        displayed = 0
        displayed_urls = []
        while displayed < total:
            for i in range(len(df1)):
                url = df1.iat[i, 0]
                print(url)
                if url not in displayed_urls:
                    payload = {"url": url}
                    res = requests.post(f"http://web:8000/summaries/", data=json.dumps(payload))
                    summaryId_response = res.json()
                    st.write(summaryId_response.get("url"))
                    time.sleep(10)
                    summaryId = summaryId_response.get("id")
                    res = requests.get(f"http://web:8000/summaries/{summaryId}")
                    summaryResponse = res.json()
                    st.write(summaryResponse.get("summary"))
                    displayed += 1
                    displayed_urls.append(url)
                    print(displayed)
