from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_api_analyze_mock():
    client = TestClient(app)
    sample_path = Path(__file__).resolve().parents[2] / "examples" / "sample_pitch.txt"

    with sample_path.open("rb") as file:
        response = client.post(
            "/api/analyses",
            files={"file": ("sample_pitch.txt", file, "text/plain")},
            data={"material_type": "питч проекта", "audience_type": "жюри", "title": "Тестовый питч"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis_id"]
    assert payload["status"] == "completed"
    result = payload["result"]
    assert result["persuasiveness_score"] >= 0
    assert result["claims"]
    assert result["audience_questions"]
    categories = {question["category"] for question in result["audience_questions"]}
    assert any(category.startswith("Вся работа") for category in categories)
    assert any(category.startswith("Проблемное место") for category in categories)
    assert result["is_mock"] is True

    list_response = client.get("/api/analyses")
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == payload["analysis_id"]
