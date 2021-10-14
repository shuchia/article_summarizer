# project/app/models/tortoise.py


from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator


class Summary(models.Model):
    url = fields.TextField()
    summary = fields.TextField()
    text = fields.TextField()


def __str__(self):
    return self.url


class TextSummary(models.Model):
    url = fields.TextField(null=True)
    summary = fields.TextField()
    timeFrame = fields.TextField()
    topic = fields.TextField()
    category = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)
    uid = fields.UUIDField()

    def __str__(self):
        return self.url


class Report(models.Model):
    name = fields.TextField()
    report = fields.TextField()

    def __str__(self):
        return self.name


SummarySchema = pydantic_model_creator(TextSummary)
URLSummarySchema = pydantic_model_creator(Summary)
ReportSchema = pydantic_model_creator(Report)
