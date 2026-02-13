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
    context.message = message
    return context


def _make_event_queue(async_enqueue=False):
    """EventQueue モックを生成。

    Collector/Librarian は enqueue_event を同期呼び出し、
    Researcher は TaskUpdater 経由で await するため使い分ける。
    """
    queue = MagicMock()
    queue.enqueue_event = AsyncMock() if async_enqueue else MagicMock()
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
        # message が None のコンテキスト
        context = MagicMock()
        context.message = None
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

        async def _stub_stream(params):
            for chunk in ["チャンク1", "チャンク2"]:
                yield chunk

        mock_service.research_stream = _stub_stream

        executor = ResearcherAgentExecutor()
        context = _make_context({
            "user_id": "user_1",
            "collection_id": "col_1",
            "article_url": "https://example.com/1",
        })
        context.task_id = "task-1"
        context.context_id = "ctx-1"
        queue = _make_event_queue(async_enqueue=True)

        await executor.execute(context, queue)

        # start_work + 2 add_artifact + complete = 4 イベント
        assert queue.enqueue_event.call_count == 4

    @patch("researcher.agent_executor.service")
    async def test_executeがTaskUpdater経由でストリーミングイベントを発行する(
        self, mock_service
    ):
        from researcher.agent_executor import ResearcherAgentExecutor

        async def _stub_stream(params):
            for chunk in ["A", "B", "C"]:
                yield chunk

        mock_service.research_stream = _stub_stream

        executor = ResearcherAgentExecutor()
        context = _make_context({
            "user_id": "user_1",
            "collection_id": "col_1",
            "article_url": "https://example.com/1",
        })
        context.task_id = "task-2"
        context.context_id = "ctx-2"
        queue = _make_event_queue(async_enqueue=True)

        await executor.execute(context, queue)

        # start_work(1) + add_artifact(3) + complete(1) = 5
        assert queue.enqueue_event.call_count == 5
