from app.services.analysis_pipeline import analyze_text
from app.services.llm.mock_provider import MockLLMProvider
from app.services.storage_service import get_analysis_result, list_analysis_runs, save_analysis_result


def test_storage_service_saves_lists_and_loads():
    from app.database import SessionLocal

    result = analyze_text(
        text="Цель проекта: помочь студентам готовиться к защите. 73% участников отметили пользу.",
        filename="sample.txt",
        material_type="питч проекта",
        audience_type="жюри",
        provider=MockLLMProvider(),
    )

    with SessionLocal() as session:
        save_analysis_result(session, result)
        runs = list_analysis_runs(session)
        loaded = get_analysis_result(session, result.id)

    assert len(runs) == 1
    assert runs[0].id == result.id
    assert loaded is not None
    assert loaded.id == result.id
    assert loaded.persuasiveness_score >= 0
