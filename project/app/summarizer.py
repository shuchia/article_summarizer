# project/app/summarizer.py


import asyncio
from app.summarypro import SummarizerProcessor
from fastapi import File, UploadFile
from uuid import UUID, uuid4
from app.models.tortoise import TextSummary
from app.models.pydantic import Job
import pandas as pd
from app.api import crud


async def generate_summary(summary_id: int, url: str) -> None:
    summary_process = SummarizerProcessor(model="google/pegasus-newsroom")

    summary = summary_process.inference(
        input_url=url
    )

    await asyncio.sleep(10)

    await TextSummary.filter(id=summary_id).update(summary=summary)


async def generate_bulk_summary(task: Job, modelname: str, file: UploadFile) -> None:
    summary_process = SummarizerProcessor(model=modelname)

    df = pd.read_excel(file.file.read(), index_col=None, header=None)
    df1 = df.iloc[1:]
    # logger.info(len(df))
    for ind in range(len(df1)):
        url = df1.iat[ind, 0]
        summary_id = await crud.create(url)

        summary = summary_process.inference(input_url=url)

        await asyncio.sleep(10)

        await TextSummary.filter(id=summary_id).update(summary=summary)
        task.processed_ids.append(summary_id)
    task.status = "Completed"
