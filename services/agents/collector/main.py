import uvicorn
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from fastapi import FastAPI

from .agent_executor import CollectorAgentExecutor


def create_app() -> FastAPI:
    skill = AgentSkill(
        id="collect_articles",
        name="記事収集",
        description="ユーザーのソース設定に基づいて記事を収集し、Librarianにスコアリングを依頼",
        tags=["collector", "rss"],
        examples=["記事を収集して"],
    )
    agent_card = AgentCard(
        name="Collector Agent",
        description="RSS/Webサイトから記事を収集し、スコアリングを依頼するエージェント",
        url="http://localhost:8001/",
        version="0.1.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[skill],
    )

    handler = DefaultRequestHandler(
        agent_executor=CollectorAgentExecutor(),
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
    uvicorn.run(app, host="0.0.0.0", port=8001)
