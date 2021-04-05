# project/app/summarizer.py


import asyncio
from app.summarypro import SummarizerProcessor

from app.models.tortoise import TextSummary


async def generate_summary(summary_id: int, url: str) -> None:
    summary_process = SummarizerProcessor(model="google/pegasus-newsroom")

    summary = summary_process.inference(
            input_url=url
        )

    await asyncio.sleep(10)

    await TextSummary.filter(id=summary_id).update(summary=summary)
