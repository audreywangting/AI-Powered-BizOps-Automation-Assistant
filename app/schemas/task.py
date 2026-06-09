from typing import Literal, Optional

from pydantic import BaseModel, Field


Priority = Literal["Low", "Medium", "High", "Urgent"]
Category = Literal[
    "Frontend Bug",
    "Backend Bug",
    "Customer Complaint",
    "Billing",
    "Data Request",
    "Access Issue",
    "Integration Issue",
    "Device Issue",
    "Other",
]


class BizOpsTask(BaseModel):
    title: str = Field(..., min_length=3)
    priority: Priority
    category: Category
    assignee: Optional[str] = None
    customer: Optional[str] = None
    summary: str = Field(..., min_length=10)
    recommended_action: str = Field(..., min_length=10)
