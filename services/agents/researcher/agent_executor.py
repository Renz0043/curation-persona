import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import DataPart
from a2a.utils import new_agent_text_message

from .service import ResearcherService

logger = logging.getLogger(__name__)
service = ResearcherService()


class ResearcherAgentExecutor(AgentExecutor):
    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        params = {}
        if context.request and context.request.message:
            for part in context.request.message.parts:
                if hasattr(part, "root") and isinstance(part.root, DataPart):
                    params = part.root.data
                    break

        article_url = params.get("article_url", "")
        logger.info(f"Starting research for article: {article_url}")

        result = await service.research(params)

        event_queue.enqueue_event(
            new_agent_text_message(
                f"Research completed for: {article_url}"
            )
        )

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise NotImplementedError("cancel not supported")
