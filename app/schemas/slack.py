from pydantic import BaseModel, Field

from app.schemas.task import BizOpsTask


class DemoParseRequest(BaseModel):
    message: str = Field(..., min_length=1)


class DemoCreateTaskResponse(BaseModel):
    task: BizOpsTask
    notion_url: str


class SlackThreadMessage(BaseModel):
    channel: str
    thread_ts: str
    text: str
