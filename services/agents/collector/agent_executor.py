import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import DataPart
from a2a.utils import new_agent_text_message

from shared.a2a_client import A2AClient
from shared.fetchers import fetcher_registry
from shared.firestore_client import FirestoreClient

from .service import CollectorService

logger = logging.getLogger(__name__)

firestore = FirestoreClient()
a2a_client = A2AClient()
service = CollectorService(firestore, a2a_client, fetcher_registry)


class CollectorAgentExecutor(AgentExecutor):
    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        params = {}
        if context.message:
            for part in context.message.parts:
                if hasattr(part, "root") and isinstance(part.root, DataPart):
                    params = part.root.data
                    break

        user_id = params.get("user_id", "")
        logger.info(f"Starting article collection for user: {user_id}")

        result = await service.execute(user_id)

        event_queue.enqueue_event(
            new_agent_text_message(
                f"Collection completed: {result['articles_total']} articles collected "
                f"(collection_id: {result['collection_id']})"
            )
        )

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise NotImplementedError("cancel not supported")
