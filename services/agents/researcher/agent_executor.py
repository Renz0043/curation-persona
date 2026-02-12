import logging
import uuid

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import DataPart, Part, TextPart

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

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.start_work()

        try:
            artifact_id = str(uuid.uuid4())
            is_first = True
            async for chunk in service.research_stream(validated):
                await updater.add_artifact(
                    parts=[Part(root=TextPart(text=chunk))],
                    artifact_id=artifact_id,
                    append=None if is_first else True,
                )
                is_first = False
            await updater.complete()
        except Exception:
            await updater.failed()
            raise

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise NotImplementedError("cancel not supported")
