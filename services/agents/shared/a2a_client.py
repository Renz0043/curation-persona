import logging
import uuid

import httpx
from a2a.client import A2ACardResolver
from a2a.client import A2AClient as BaseA2AClient
from a2a.types import DataPart, Message, MessageSendParams, Part, SendMessageRequest

logger = logging.getLogger(__name__)


class A2AClient:
    """A2Aプロトコルでエージェント間通信を行うクライアント"""

    async def send_message(
        self,
        agent_url: str,
        skill: str,
        params: dict,
    ) -> dict:
        async with httpx.AsyncClient(timeout=300.0) as http_client:
            resolver = A2ACardResolver(
                httpx_client=http_client,
                base_url=agent_url,
            )
            agent_card = await resolver.get_agent_card()
            client = BaseA2AClient(
                httpx_client=http_client,
                agent_card=agent_card,
            )

            message = Message(
                messageId=str(uuid.uuid4()),
                role="user",
                parts=[Part(root=DataPart(data={"skill": skill, **params}))],
            )

            request = SendMessageRequest(
                id=str(uuid.uuid4()),
                params=MessageSendParams(message=message),
            )

            response = await client.send_message(request)

            logger.info(f"A2A message sent to {agent_url} (skill={skill})")
            return response
