import pytest
import httpx

from shared.retry import is_retryable, with_retry


class Test_リトライ判定:
    def test_タイムアウトはリトライ対象(self):
        assert is_retryable(httpx.ReadTimeout("timeout")) is True

    def test_ネットワークエラーはリトライ対象(self):
        assert is_retryable(httpx.NetworkError("network")) is True

    def test_429はリトライ対象(self):
        response = httpx.Response(429)
        err = httpx.HTTPStatusError("rate limit", request=httpx.Request("GET", "http://x"), response=response)
        assert is_retryable(err) is True

    def test_503はリトライ対象(self):
        response = httpx.Response(503)
        err = httpx.HTTPStatusError("unavailable", request=httpx.Request("GET", "http://x"), response=response)
        assert is_retryable(err) is True

    def test_400はリトライ対象外(self):
        response = httpx.Response(400)
        err = httpx.HTTPStatusError("bad request", request=httpx.Request("GET", "http://x"), response=response)
        assert is_retryable(err) is False

    def test_ValueErrorはリトライ対象外(self):
        assert is_retryable(ValueError("bad value")) is False


class Test_リトライデコレータ:
    async def test_成功時はそのまま返る(self):
        @with_retry
        async def success():
            return "ok"

        assert await success() == "ok"

    async def test_リトライ後に成功する(self):
        call_count = 0

        @with_retry
        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.NetworkError("network error")
            return "recovered"

        result = await fail_then_succeed()
        assert result == "recovered"
        assert call_count == 3

    async def test_リトライ不可能なエラーは即座に送出(self):
        call_count = 0

        @with_retry
        async def non_retryable():
            nonlocal call_count
            call_count += 1
            raise ValueError("bad")

        with pytest.raises(ValueError):
            await non_retryable()
        assert call_count == 1

    async def test_全リトライ失敗で最後の例外を送出(self):
        @with_retry
        async def always_fail():
            raise httpx.NetworkError("always fails")

        with pytest.raises(httpx.NetworkError):
            await always_fail()
