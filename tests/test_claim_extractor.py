from app.claim_extractor import extract_claims


def test_extracts_number_claim():
    text = "По нашим оценкам, 73% студентов улучшают структуру работы после обратной связи."

    claims = extract_claims(text)

    assert claims
    assert any(claim.claim_type == "number" for claim in claims)
    assert any(claim.evidence_status == "needs_source" for claim in claims)

