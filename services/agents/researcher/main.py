import logging
import os

import uvicorn
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from shared.models import BookmarkRequest, ResearchArticleParams

from .agent_executor import ResearcherAgentExecutor, firestore, service

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    skill = AgentSkill(
        id="research_article",
        name="記事詳細調査",
        description="記事の深掘りレポートをGemini Proで生成",
        tags=["researcher", "deep-dive"],
        examples=["この記事を深掘りして"],
    )
    agent_card = AgentCard(
        name="Researcher Agent",
        description="ピックアップ記事の詳細調査レポートを生成するエージェント",
        url=os.environ.get("AGENT_BASE_URL", "http://localhost:8003") + "/",
        version="0.1.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )

    handler = DefaultRequestHandler(
        agent_executor=ResearcherAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    a2a_app = A2AFastAPIApplication(
        agent_card=agent_card,
        http_handler=handler,
    )
    app: FastAPI = a2a_app.build()

    cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
    origins = [o.strip() for o in cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    @app.post("/api/bookmarks")
    async def create_bookmark(
        request: BookmarkRequest, background_tasks: BackgroundTasks
    ):
        # API キー検証
        user = await firestore.get_user_by_api_key(request.api_key)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid API key")

        user_id = user["user_id"]
        logger.info(f"Bookmark request: user_id={user_id}, url={request.url}")

        # バックグラウンドで深掘り実行
        background_tasks.add_task(service.create_bookmark, user_id, request.url)

        return {"status": "accepted", "url": request.url}

    @app.post("/api/research")
    async def create_research(
        request: ResearchArticleParams, background_tasks: BackgroundTasks
    ):
        logger.info(
            f"Research request: user_id={request.user_id}, "
            f"collection_id={request.collection_id}, "
            f"article_url={request.article_url}"
        )

        # バックグラウンドで深掘り実行
        background_tasks.add_task(service.research, request)

        return {"status": "accepted"}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
