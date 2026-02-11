import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import DataPart
from a2a.utils import new_agent_text_message

from shared.firestore_client import FirestoreClient
from shared.gemini_client import GeminiClient

from .scorer import ArticleScorer
from .service import LibrarianService

logger = logging.getLogger(__name__)

firestore = FirestoreClient()
gemini_client = GeminiClient("flash")
scorer = ArticleScorer(gemini_client)
service = LibrarianService(firestore, gemini_client, scorer)


class LibrarianAgentExecutor(AgentExecutor):
    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        params = {}
        if context.request and context.request.message:
            for part in context.request.message.parts:
                if hasattr(part, "root") and isinstance(part.root, DataPart):
                    params = part.root.data
                    break

        user_id = params.get("user_id", "")
        collection_id = params.get("collection_id", "")
        logger.info(f"Starting scoring for collection: {collection_id}")

        result = await service.score_collection(user_id, collection_id)

        event_queue.enqueue_event(
            new_agent_text_message(
                f"Scoring completed for collection: {collection_id} "
                f"({result['scored_count']} articles scored)"
            )
        )

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise NotImplementedError("cancel not supported")
