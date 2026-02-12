import uvicorn
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from fastapi import FastAPI

from .agent_executor import ResearcherAgentExecutor


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
        url="http://localhost:8003/",
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

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
