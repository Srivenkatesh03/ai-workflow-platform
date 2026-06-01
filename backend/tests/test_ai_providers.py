import pytest
from uuid import uuid4
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import get_db
from app.integrations.ai.base import (
    estimate_tokens,
    PromptTemplate,
    AIProvider,
    AIResponse,
    FallbackAIProvider,
)
from app.integrations.ai.mock import MockAIProvider
from app.services.ai_service import AIService
from app.models.ai_log import AILog


class FailingAIProvider(AIProvider):
    """Temporary test provider designed to always raise exceptions."""

    @property
    def provider_name(self) -> str:
        return "failing"

    @property
    def default_model(self) -> str:
        return "fail-1.0"

    async def generate(self, prompt, model=None, timeout=30.0, options=None):
        raise ConnectionError("Simulated provider network timeout")

    async def generate_stream(self, prompt, model=None, timeout=30.0, options=None):
        raise ConnectionError("Simulated provider network stream timeout")
        yield ""

    async def chat(self, messages, model=None, timeout=30.0, options=None):
        raise ConnectionError("Simulated provider network timeout during chat")

    async def chat_stream(self, messages, model=None, timeout=30.0, options=None):
        raise ConnectionError("Simulated provider network stream timeout during chat")
        yield ""


def test_token_estimation_and_templates():
    assert estimate_tokens("hello") == 1
    assert estimate_tokens("The quick brown fox jumps over the lazy dog.") == 11

    tpl = PromptTemplate("Translate '{text}' to {language}.")
    assert tpl.render(text="good morning", language="French") == "Translate 'good morning' to French."


@pytest.mark.anyio
async def test_mock_provider_generation():
    mock = MockAIProvider(model="custom-mock-model")
    assert mock.provider_name == "mock"
    assert mock.default_model == "custom-mock-model"

    resp = await mock.generate("summarize this input text")
    assert resp.provider == "mock"
    assert resp.model == "custom-mock-model"
    assert "lazy dog" in resp.output
    assert resp.usage["total_tokens"] > 0
    assert resp.latency_ms >= 0

    chunks = []
    async for chunk in mock.generate_stream("stream me"):
        chunks.append(chunk)
    assert len(chunks) > 0
    assert "".join(chunks) == "This is a mock streaming completion."


@pytest.mark.anyio
async def test_resilient_fallback_chain():
    failing = FailingAIProvider()
    mock = MockAIProvider(model="mock-backup")
    fallback_chain = FallbackAIProvider(primary=failing, fallback=mock)

    # Should transparently catch FailingAIProvider's exception and return mock's response!
    resp = await fallback_chain.generate("Summarize some text")
    assert resp.provider == "mock"
    assert resp.model == "mock-backup"
    assert "lazy dog" in resp.output


def test_ai_service_persistence():
    # Use FastAPI test client database context
    with TestClient(app) as client:
        # Get DB session through dependency injection override
        db_gen = get_db()
        db: Session = next(db_gen)

        # Build service with DB context
        ai_service = AIService(db=db)
        
        execution_id = uuid4()
        source = "workflows/resume-screening"

        # Force mock provider call
        result = client.post(
            "/api/v1/auth/register",
            json={"name": "Tester", "email": f"tester-{uuid4().hex}@example.com", "password": "PassPassword1"},
        )
        assert result.status_code == 201

        # Direct service call with DB session
        import anyio
        async def run_call():
            return await ai_service.summarize(
                "This is a paragraph about an animal in the forest.",
                provider="mock",
                workflow_source=source,
                execution_id=execution_id
            )
        
        sum_result = anyio.run(run_call)
        assert sum_result.provider == "mock"

        # Check DB log persistence
        logs = db.query(AILog).filter(AILog.execution_id == execution_id).all()
        assert len(logs) == 1
        assert logs[0].provider == "mock"
        assert logs[0].workflow_source == source
        assert logs[0].response_time_ms >= 0
        assert logs[0].total_tokens > 0


def test_prompt_template_manager():
    from app.integrations.ai.templates import prompt_templates, PromptTemplate, PromptTemplateError
    
    # Test built-in template retrieval and rendering
    tpl = prompt_templates.get("summarize")
    rendered = tpl.render(text="FastAPI is great")
    assert "FastAPI is great" in rendered

    # Test custom template registration
    custom_tpl = PromptTemplate("test_greet", "Hello {name}!", required_keys={"name"})
    prompt_templates.register(custom_tpl)
    assert prompt_templates.render_template("test_greet", name="Developer") == "Hello Developer!"

    # Test strict validation error
    with pytest.raises(PromptTemplateError):
        custom_tpl.render(wrong_key="Developer")


@pytest.mark.anyio
async def test_mock_chat_generation():
    mock = MockAIProvider(model="chat-mock")
    messages = [{"role": "user", "content": "How are you?"}]
    resp = await mock.chat(messages)
    assert resp.provider == "mock"
    assert "How are you?" in resp.output
    
    chunks = []
    async for chunk in mock.chat_stream(messages):
        chunks.append(chunk)
    assert len(chunks) > 0


def test_ai_service_generate_and_chat_persistence():
    with TestClient(app) as client:
        db_gen = get_db()
        db: Session = next(db_gen)
        ai_service = AIService(db=db)

        # Register/login user first for auth
        email = f"user-{uuid4().hex}@example.com"
        reg_resp = client.post(
            "/api/v1/auth/register",
            json={"name": "Tester", "email": email, "password": "PassPassword1"},
        )
        assert reg_resp.status_code == 201
        
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "PassPassword1"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Test POST /api/generate
        gen_payload = {
            "prompt": "Say hello world",
            "provider": "mock",
            "model": "mock-gpt-4",
        }
        resp = client.post("/api/generate", json=gen_payload, headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["provider"] == "mock"
        assert "hello world" in data["output"].lower()

        # Check DB log for generate
        logs = db.query(AILog).filter(AILog.provider == "mock").order_by(AILog.created_at.desc()).all()
        assert len(logs) >= 1
        assert logs[0].success is True
        assert logs[0].error_message is None
        assert logs[0].total_tokens > 0

        # 2. Test POST /api/chat
        chat_payload = {
            "messages": [{"role": "user", "content": "Ping"}],
            "provider": "mock",
        }
        resp = client.post("/api/chat", json=chat_payload, headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["provider"] == "mock"
        assert "ping" in data["output"].lower()

