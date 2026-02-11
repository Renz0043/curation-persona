import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import DataPart
from a2a.utils import new_agent_text_message

from shared.firestore_client import FirestoreClient
from shared.gemini_client import GeminiClient
from shared.models import ResearchArticleParams

from .report_generator import ReportGenerator
from .service import ResearcherService

logger = logging.getLogger(__name__)

firestore = FirestoreClient()
gemini_client = GeminiClient("pro")
report_generator = ReportGenerator(gemini_client)
service = ResearcherService(firestore, report_generator)


class ResearcherAgentExecutor(AgentExecutor):
    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        params = {}
        if context.message:
            for part in context.message.parts:
                if hasattr(part, "root") and isinstance(part.root, DataPart):
                    params = part.root.data
                    break

        validated = ResearchArticleParams.model_validate(params)
        logger.info(f"Starting research for article: {validated.article_url}")

        result = await service.research(validated)

        event_queue.enqueue_event(
            new_agent_text_message(
                f"Research completed for: {validated.article_url}"
            )
        )

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise NotImplementedError("cancel not supported")
