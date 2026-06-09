from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.slack_events import router as slack_router

app = FastAPI(title="AI-Powered BizOps Automation Assistant")

app.include_router(health_router)
app.include_router(slack_router)
