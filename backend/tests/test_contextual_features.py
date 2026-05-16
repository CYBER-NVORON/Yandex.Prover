from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.analysis_pipeline import analyze_text
from app.services.contextual_analysis import build_overthinking_guard
from app.services.llm.mock_provider import MockLLMProvider
from app.services.prompt_service import PromptService


MATERIAL_TEXT = """
Цель проекта: помочь школьникам готовиться к защите исследовательской работы.
Задачи: выделить слабые утверждения, подготовить вопросы аудитории и собрать план улучшения.
В материале есть пример анализа доклада и вывод о том, что автору нужно закрыть самые рискованные тезисы.
Вывод: сервис полезен как инструмент предзащиты, если автор проверяет доказательства и готовит ответы.
""".strip()


REGULATION_TEXT = """
Положение конкурса исследовательских работ.
Работа должна содержать цель, задачи, методы и вывод.
Критерии оценки: соответствие теме, доказательность, самостоятельность, ясность выступления.
Объём доклада: до 7 минут.
Жюри оценивает структуру, методы, результаты и готовность отвечать на вопросы.
""".strip()


BENCHMARK_TEXT = """
Цель работы: показать, как подготовка к вопросам повышает качество защиты.
Задачи: описать аудиторию, выбрать методы, сравнить результаты и сформулировать вывод.
Методы: анализ источников, сравнение примеров, мини-опрос.
Результаты: в работе приведены критерии, примеры и ограничения метода.
Вывод: подготовка сильнее, когда автор заранее знает слабые места.
""".strip()


def test_analyze_with_regulation_mock():
    client = TestClient(app)

    response = client.post(
        "/api/analyses",
        files={
            "file": ("material.txt", MATERIAL_TEXT.encode("utf-8"), "text/plain"),
            "regulation_file": ("regulation.txt", REGULATION_TEXT.encode("utf-8"), "text/plain"),
        },
        data={"material_type": "доклад", "audience_type": "жюри", "title": "С регламентом"},
    )

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["regulation_analysis"] is not None
    assert result["regulation_analysis"]["checklist"]

    list_response = client.get("/api/analyses")
    assert list_response.status_code == 200
    assert list_response.json()[0]["has_regulation"] is True


def test_analyze_with_benchmark_mock():
    client = TestClient(app)

    response = client.post(
        "/api/analyses",
        files={
            "file": ("material.txt", MATERIAL_TEXT.encode("utf-8"), "text/plain"),
            "benchmark_file": ("benchmark.txt", BENCHMARK_TEXT.encode("utf-8"), "text/plain"),
        },
        data={"material_type": "доклад", "audience_type": "жюри", "title": "С эталоном"},
    )

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["benchmark_comparison"] is not None
    assert result["benchmark_comparison"]["missing_elements"]
    assert result["benchmark_comparison"]["action_items"]

    list_response = client.get("/api/analyses")
    assert list_response.status_code == 200
    assert list_response.json()[0]["has_benchmark"] is True


def test_audience_knowledge_level():
    client = TestClient(app)

    response = client.post(
        "/api/analyses",
        files={"file": ("material.txt", MATERIAL_TEXT.encode("utf-8"), "text/plain")},
        data={
            "material_type": "доклад",
            "audience_type": "широкая аудитория",
            "audience_knowledge_level": "1",
        },
    )

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["audience_knowledge_level"] == 1
    assert result["audience_adaptation_notes"]


def test_overthinking_guard_exists():
    client = TestClient(app)

    response = client.post(
        "/api/analyses",
        files={"file": ("material.txt", MATERIAL_TEXT.encode("utf-8"), "text/plain")},
        data={"material_type": "доклад", "audience_type": "жюри"},
    )

    assert response.status_code == 200
    guard = response.json()["result"]["overthinking_guard"]
    assert guard
    assert len(guard["next_best_three_actions"]) <= 3
    assert set(guard["critical_fixes"]).isdisjoint(set(guard["optional_improvements"]))


def test_overthinking_guard_ready_logic():
    result = analyze_text(
        text=MATERIAL_TEXT,
        filename="material.txt",
        material_type="доклад",
        audience_type="жюри",
        provider=MockLLMProvider(),
    )
    for claim in result.claims:
        claim.risk_level = "low"

    result.persuasiveness_score = 85
    high_guard = build_overthinking_guard(result, None, None, 3)
    assert high_guard.readiness_verdict in {"ready", "almost_ready"}

    result.persuasiveness_score = 40
    low_guard = build_overthinking_guard(result, None, None, 3)
    assert low_guard.readiness_verdict == "needs_work"


def test_prompt_contains_no_overthinking_rule():
    prompt_service = PromptService()
    prompt = prompt_service.system_prompt() + "\n" + prompt_service.build_user_prompt(
        text=MATERIAL_TEXT,
        filename="material.txt",
        material_type="доклад",
        audience_type="жюри",
        audience_knowledge_level=3,
    )

    assert "лишнюю тревогу" in prompt.lower()
    assert "Не провоцируй лишнюю тревогу" in prompt
