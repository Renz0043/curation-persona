from unittest.mock import AsyncMock, MagicMock, patch

from a2a.types import DataPart, Message, Part

from shared.models import ResearchArticleParams


def _make_context(params: dict):
    """DataPart を含む RequestContext モックを生成"""
    context = MagicMock()
    message = Message(
        messageId="test-msg-1",
        role="user",
        parts=[Part(root=DataPart(data=params))],
    )
    context.request.message = message
    return context


def _make_event_queue():
    queue = MagicMock()
    queue.enqueue_event = MagicMock()
    return queue


class Test_CollectorAgentExecutor:
    @patch("collector.agent_executor.service")
    async def test_executeがDataPartからuser_idを抽出してserviceを呼ぶ(self, mock_service):
        from collector.agent_executor import CollectorAgentExecutor

        mock_service.execute = AsyncMock(
            return_value={"status": "success", "articles_total": 5, "collection_id": "col_1"}
        )

        executor = CollectorAgentExecutor()
        context = _make_context({"user_id": "user_1"})
        queue = _make_event_queue()

        await executor.execute(context, queue)

        mock_service.execute.assert_called_once_with("user_1")
        queue.enqueue_event.assert_called_once()

    @patch("collector.agent_executor.service")
    async def test_パラメータなしでも空文字で呼ばれる(self, mock_service):
        from collector.agent_executor import CollectorAgentExecutor

        mock_service.execute = AsyncMock(
            return_value={"status": "success", "articles_total": 0, "collection_id": ""}
        )

        executor = CollectorAgentExecutor()
        # DataPart なしのメッセージ
        context = MagicMock()
        context.request.message.parts = []
        queue = _make_event_queue()

        await executor.execute(context, queue)

        mock_service.execute.assert_called_once_with("")


class Test_LibrarianAgentExecutor:
    @patch("librarian.agent_executor.service")
    async def test_executeがcollection_idとuser_idを抽出してserviceを呼ぶ(self, mock_service):
        from librarian.agent_executor import LibrarianAgentExecutor

        mock_service.score_collection = AsyncMock(
            return_value={"status": "success", "scored_count": 3, "collection_id": "col_1", "pickup_count": 2}
        )

        executor = LibrarianAgentExecutor()
        context = _make_context({"user_id": "user_1", "collection_id": "col_1"})
        queue = _make_event_queue()

        await executor.execute(context, queue)

        mock_service.score_collection.assert_called_once_with("user_1", "col_1")
        queue.enqueue_event.assert_called_once()


class Test_ResearcherAgentExecutor:
    @patch("researcher.agent_executor.service")
    async def test_executeがResearchArticleParamsを構築してserviceを呼ぶ(self, mock_service):
        from researcher.agent_executor import ResearcherAgentExecutor

        mock_service.research = AsyncMock(
            return_value={"status": "success", "article_url": "https://example.com/1"}
        )

        executor = ResearcherAgentExecutor()
        context = _make_context({
            "user_id": "user_1",
            "collection_id": "col_1",
            "article_url": "https://example.com/1",
        })
        queue = _make_event_queue()

        await executor.execute(context, queue)

        mock_service.research.assert_called_once()
        call_arg = mock_service.research.call_args[0][0]
        assert isinstance(call_arg, ResearchArticleParams)
        assert call_arg.user_id == "user_1"
        assert call_arg.collection_id == "col_1"
        assert call_arg.article_url == "https://example.com/1"
        queue.enqueue_event.assert_called_once()
