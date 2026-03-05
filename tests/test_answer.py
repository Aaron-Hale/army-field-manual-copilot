from fastapi.testclient import TestClient

import app.routers.answer as answer_router
from app.main import app


client = TestClient(app)


def test_empty_retrieval_refuses(monkeypatch):
    # retrieval returns nothing
    def fake_retrieve_top_k(*, question: str, top_k: int):
        return []

    monkeypatch.setattr(answer_router, "retrieve_top_k", fake_retrieve_top_k)

    r = client.post("/answer", json={"question": "anything", "top_k": 3})
    assert r.status_code == 200
    body = r.json()
    assert body["refusal"] is True
    assert body["citations"] == []
    assert isinstance(body["needs_clarification"], list)
    assert len(body["needs_clarification"]) > 0


def test_nonrefusal_requires_citations(monkeypatch):
    # retrieval returns one chunk
    def fake_retrieve_top_k(*, question: str, top_k: int):
        return [
            {
                "content": {"text": "MDMP consists of seven steps..."},
                "score": 0.9,
                "location": {"type": "s3Location", "s3Location": {"uri": "s3://bucket/FM_5-0.pdf"}},
                "metadata": {"document_title": "FM_5-0.pdf"},
            }
        ]

    # LLM tries to return non-refusal without citations -> API should force refusal
    def fake_converse_json(*, system_text: str, user_text: str):
        return (
            '{"answer":"Here are the steps...","citation_ids":[],"refusal":false,"needs_clarification":[]}',
            {"usage": {"inputTokens": 10, "outputTokens": 5}},
        )

    monkeypatch.setattr(answer_router, "retrieve_top_k", fake_retrieve_top_k)
    monkeypatch.setattr(answer_router, "converse_json", fake_converse_json)

    r = client.post("/answer", json={"question": "What are the steps of MDMP?", "top_k": 3})
    assert r.status_code == 200
    body = r.json()
    assert body["refusal"] is True
    assert body["citations"] == []
    assert len(body["needs_clarification"]) > 0


def test_json_schema_always_valid(monkeypatch):
    # retrieval returns one chunk
    def fake_retrieve_top_k(*, question: str, top_k: int):
        return [
            {
                "content": {"text": "Some doctrinal excerpt."},
                "score": 0.9,
                "location": {"type": "s3Location", "s3Location": {"uri": "s3://bucket/doc.pdf"}},
                "metadata": {"document_title": "doc.pdf"},
            }
        ]

    # LLM returns valid JSON with one citation id
    def fake_converse_json(*, system_text: str, user_text: str):
        return (
            '{"answer":"Grounded answer.","citation_ids":[1],"refusal":false,"needs_clarification":[]}',
            {"usage": {"inputTokens": 12, "outputTokens": 7}},
        )

    monkeypatch.setattr(answer_router, "retrieve_top_k", fake_retrieve_top_k)
    monkeypatch.setattr(answer_router, "converse_json", fake_converse_json)

    r = client.post("/answer", json={"question": "test", "top_k": 3})
    assert r.status_code == 200
    body = r.json()

    # required keys exist with correct types
    assert isinstance(body["answer"], str)
    assert isinstance(body["citations"], list)
    assert isinstance(body["refusal"], bool)
    assert isinstance(body["needs_clarification"], list)

    # citations are normalized
    assert len(body["citations"]) == 1
    c = body["citations"][0]
    assert "doc" in c and "location" in c and "snippet" in c
    assert isinstance(c["doc"], str) and c["doc"]
    assert isinstance(c["location"], str) and c["location"]
    assert isinstance(c["snippet"], str) and c["snippet"]
