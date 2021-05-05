# project/app/summarizer.py


import asyncio
from app.summarypro import SummarizerProcessor
from fastapi import File, UploadFile

from app.models.tortoise import TextSummary
from app.models.pydantic import Job
import pandas as pd
from app.api import crud
import logging
import math

log = logging.getLogger(__name__)


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
        timeframe = {row['MM/YY']}
        topic = {row['Topic']}
        category = {row['Category']}
        # url = df1.iat[ind, 0]
        log.info(url)
        if url != url is False:
            summary_id = await crud.create(url, timeframe, topic, category, task.uid)

            summary = summary_process.inference(input_url=url)

            await asyncio.sleep(5)

            await TextSummary.filter(id=summary_id).update(summary=summary)
            task.processed_ids[summary_id] = url
    task.status = "Completed"
