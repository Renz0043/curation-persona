from fastapi.testclient import TestClient


class Test_CollectorAgent:
    def test_ヘルスチェックが返る(self):
        from collector.main import app

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_AgentCardが正しい(self):
        from collector.main import app

        client = TestClient(app)
        response = client.get("/.well-known/agent-card.json")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Collector Agent"
        assert len(data["skills"]) == 1
        assert data["skills"][0]["id"] == "collect_articles"


class Test_LibrarianAgent:
    def test_ヘルスチェックが返る(self):
        from librarian.main import app

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_AgentCardが正しい(self):
        from librarian.main import app

        client = TestClient(app)
        response = client.get("/.well-known/agent-card.json")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Librarian Agent"
        assert data["skills"][0]["id"] == "score_articles"


class Test_ResearcherAgent:
    def test_ヘルスチェックが返る(self):
        from researcher.main import app

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_AgentCardが正しい(self):
        from researcher.main import app

        client = TestClient(app)
        response = client.get("/.well-known/agent-card.json")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Researcher Agent"
        assert data["skills"][0]["id"] == "research_article"
