import json
from pathlib import Path

from tcg import pipeline
from tcg.models import Behavior, Candidate, CandidateStatus, Message, TrainingRecord
from tcg.settings import PipelineSettings
from tcg.storage import Store


def test_pipeline_exports_only_three_training_fields(tmp_path):
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps(
            [
                {
                    "instruction": "Bileşik faiz nedir?",
                    "input": "",
                    "output": "Bileşik faiz, faizin anaparaya eklenmesiyle hesaplanır.",
                },
                {
                    "instruction": "Kredi kartı yapılandırma şartları nelerdir?",
                    "input": "",
                    "output": "Koşullar güncel düzenlemeye bağlıdır.",
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    settings = PipelineSettings.model_validate(
        {
            "system_prompt": "Türkçe finans asistanısın.",
            "source": {"id": "test", "url": str(source), "revision": "test-rev"},
            "paths": {
                "state_db": tmp_path / "state.sqlite",
                "work_dir": tmp_path / "work",
                "tool_catalog": Path("data/tools/borsa_mcp.json"),
                "tool_overrides": Path("data/tools/borsa_overrides.tr.yaml"),
            },
        }
    )

    assert pipeline.ingest(settings) == 2
    assert pipeline.build(settings, include_seeds=False) == 2
    result = pipeline.validate(settings)
    assert result.get("invalid", 0) == 0
    reviewed = pipeline.review(settings, source_id="test")
    assert len(reviewed) == 2
    assert all(
        item["id"].startswith(f"TRFIN-{item['behavior']}-")
        and item["id"].rsplit("-", 1)[-1].isdigit()
        for item in reviewed
    )
    assert pipeline.approve_valid(settings, selected_ids={reviewed[0]["id"]}) == 1
    assert pipeline.approve_valid(settings, source_id="test") == 1
    assert pipeline.build(settings, include_seeds=False) == 2
    assert pipeline.report(settings)["status"] == {"accepted": 2}
    counts = pipeline.export(settings)
    assert sum(counts.values()) == 2

    rows = []
    for path in (tmp_path / "work").glob("*.jsonl"):
        rows.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())
    assert len(rows) == 2
    assert all(set(row) == {"id", "messages", "tools"} for row in rows)

    web_row = next(row for row in rows if "yapılandırma" in row["messages"][1]["content"])
    assert web_row["messages"][-1]["tool_calls"][0]["function"]["name"] == "web_search"

    assert pipeline.reject(settings, [reviewed[0]["id"]]) == 1
    pipeline.validate(settings)
    assert pipeline.report(settings)["status"] == {"accepted": 1, "rejected": 1}


def test_review_status_survives_domain_metadata_correction(tmp_path):
    record = TrainingRecord(
        id="TRFIN-finance_concept-0001",
        messages=[
            Message(role="user", content="Likidite nedir?"),
            Message(role="assistant", content="Bir varlığın hızla nakde çevrilebilmesidir."),
        ],
    )
    accepted = Candidate(
        record=record,
        behavior=Behavior.FINANCE_CONCEPT,
        domain="generic",
        source_id="curated-test-v1",
        group_id="liquidity",
        status=CandidateStatus.ACCEPTED,
    )
    corrected = accepted.model_copy(update={"domain": "financial_literacy"})
    corrected.status = CandidateStatus.PENDING

    with Store(tmp_path / "state.sqlite") as store:
        store.put_candidate(accepted)
        store.put_candidate(corrected, preserve_status_if_unchanged=True)
        stored = next(store.candidates())

    assert stored.domain == "financial_literacy"
    assert stored.status == CandidateStatus.ACCEPTED


def test_canonicalization_keeps_fresh_metadata_and_review_status(tmp_path):
    record = TrainingRecord(
        id="TRFIN-finance_concept-0001",
        messages=[
            Message(role="user", content="Likidite nedir?"),
            Message(role="assistant", content="Bir varlığın hızla nakde çevrilebilmesidir."),
        ],
    )
    accepted = Candidate(
        record=record,
        behavior=Behavior.FINANCE_CONCEPT,
        domain="generic",
        source_id="curated-test-v1",
        group_id="liquidity",
        status=CandidateStatus.ACCEPTED,
    )
    fresh = accepted.model_copy(deep=True, update={"domain": "financial_literacy"})
    fingerprint = pipeline._candidate_fingerprint(fresh)
    fresh.record.id = f"TRFIN-finance_concept-{fingerprint[:12]}"
    fresh.status = CandidateStatus.PENDING

    with Store(tmp_path / "state.sqlite") as store:
        store.put_candidate(accepted)
        store.put_candidate(fresh)
        pipeline._canonicalize_stored_candidate_ids(store, active_curated_fingerprints=None)
        candidates = list(store.candidates())

    assert len(candidates) == 1
    assert candidates[0].domain == "financial_literacy"
    assert candidates[0].status == CandidateStatus.ACCEPTED
