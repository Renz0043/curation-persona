import os

import uvicorn
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from fastapi import FastAPI

from .agent_executor import LibrarianAgentExecutor


def create_app() -> FastAPI:
    skill = AgentSkill(
        id="score_articles",
        name="記事スコアリング",
        description="コレクション内の全記事にユーザー評価ベースの関連性スコアを付与",
        tags=["librarian", "scoring"],
        examples=["記事をスコアリングして"],
    )
    agent_card = AgentCard(
        name="Librarian Agent",
        description="ユーザー評価ベースのLLMスコアリングで記事に関連性スコアを付与するエージェント",
        url=os.environ.get("AGENT_BASE_URL", "http://localhost:8002") + "/",
        version="0.1.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[skill],
    )

    handler = DefaultRequestHandler(
        agent_executor=LibrarianAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    a2a_app = A2AFastAPIApplication(
        agent_card=agent_card,
        http_handler=handler,
    )
    app: FastAPI = a2a_app.build()

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
