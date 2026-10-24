"""End-to-end curation pipeline."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path

from .agentic_cases import agentic_candidates
from .builders import build_instruction_candidate, seed_candidates
from .calculation_cases import calculation_candidates
from .classify import classify_instruction
from .generated_cases import generated_candidates
from .hard_cases import hard_case_candidates
from .live_cases import live_record_candidates
from .models import Candidate, CandidateStatus
from .settings import PipelineSettings
from .sources import ingest_instruction_source, load_tools, tool_map
from .storage import Store
from .validation import validate_candidate, validate_collection

_CURATED_SOURCE_IDS = {
    "curated-agentic-v1",
    "curated-borsa-single-v1",
    "curated-calculation-v1",
    "curated-hard-v1",
    "curated-generated-v1",
    "curated-live-v1",
    "curated-seed-v1",
}

_STATUS_PRIORITY = {
    CandidateStatus.PENDING: 0,
    CandidateStatus.VALID: 1,
    CandidateStatus.INVALID: 2,
    CandidateStatus.REJECTED: 3,
    CandidateStatus.ACCEPTED: 4,
}


def _candidate_fingerprint(candidate: Candidate) -> str:
    record = candidate.record.model_dump(exclude={"id"})
    identity = json.dumps(
        {"source": candidate.source_id, "group": candidate.group_id, "record": record},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(identity.encode()).hexdigest()


def _canonicalize_candidate_id(candidate: Candidate) -> Candidate:
    candidate.record.id = (
        f"TRFIN-{candidate.behavior.value}-{_candidate_fingerprint(candidate)[:12]}"
    )
    return candidate


def _canonicalize_stored_candidate_ids(
    store: Store, active_curated_fingerprints: set[str] | None
) -> None:
    canonical: dict[str, Candidate] = {}
    for candidate in store.candidates():
        fingerprint = _candidate_fingerprint(candidate)
        if (
            active_curated_fingerprints is not None
            and candidate.source_id in _CURATED_SOURCE_IDS
            and fingerprint not in active_curated_fingerprints
        ):
            continue
        current = canonical.get(fingerprint)
        if current is None:
            canonical[fingerprint] = candidate
            continue

        reviewed = max((current, candidate), key=lambda item: _STATUS_PRIORITY[item.status])
        fingerprint_id = fingerprint[:12]
        fresh = (
            candidate
            if candidate.record.id.endswith(fingerprint_id)
            else current
            if current.record.id.endswith(fingerprint_id)
            else candidate
        )
        fresh.status = reviewed.status
        fresh.errors = reviewed.errors
        canonical[fingerprint] = fresh

    counters: Counter[str] = Counter()
    ordered = sorted(
        canonical.items(),
        key=lambda item: (item[1].behavior.value, item[0]),
    )
    for _, candidate in ordered:
        behavior = candidate.behavior.value
        counters[behavior] += 1
        candidate.record.id = f"TRFIN-{behavior}-{counters[behavior]:04d}"
    store.replace_candidates(candidate for _, candidate in ordered)


def initialize(settings: PipelineSettings) -> dict[str, int]:
    tools = load_tools(settings)
    with Store(settings.paths.state_db) as store:
        counts = store.counts()
    return {"tools": len(tools), **counts}


def ingest(settings: PipelineSettings, limit: int | None = None) -> int:
    with Store(settings.paths.state_db) as store:
        return ingest_instruction_source(settings, store, limit)


def build(settings: PipelineSettings, limit: int | None = None, include_seeds: bool = True) -> int:
    tools = tool_map(load_tools(settings))
    written = 0
    with Store(settings.paths.state_db) as store:
        active_curated_fingerprints: set[str] | None = None
        if include_seeds:
            curated = [
                *seed_candidates(settings.system_prompt, tools),
                *hard_case_candidates(settings.system_prompt, tools),
                *generated_candidates(settings.system_prompt, tools),
                *agentic_candidates(settings.system_prompt, tools),
                *live_record_candidates(settings.system_prompt, tools),
                *calculation_candidates(settings.system_prompt),
            ]
            active_curated_fingerprints = {
                _candidate_fingerprint(candidate) for candidate in curated
            }
            curated = [_canonicalize_candidate_id(candidate) for candidate in curated]
            for candidate in curated:
                store.put_candidate(candidate, preserve_status_if_unchanged=True)
                written += 1
        for row in store.source_rows(limit):
            raw = dict(row)
            classification = classify_instruction(raw["instruction"], raw["input"])
            candidate = _canonicalize_candidate_id(
                build_instruction_candidate(
                    raw,
                    classification,
                    settings.system_prompt,
                    tools,
                    date.today().year,
                )
            )
            store.put_candidate(candidate, preserve_status_if_unchanged=True)
            written += 1
        _canonicalize_stored_candidate_ids(store, active_curated_fingerprints)
    return written


def validate(settings: PipelineSettings) -> dict[str, int | list[str]]:
    with Store(settings.paths.state_db) as store:
        candidates = list(store.candidates())
        collection_errors = validate_collection(candidates)
        for candidate in candidates:
            previous = candidate.status
            checked = validate_candidate(candidate)
            if (
                previous in {CandidateStatus.ACCEPTED, CandidateStatus.REJECTED}
                and checked.status == CandidateStatus.VALID
            ):
                checked.status = previous
            store.put_candidate(checked)
        return {
            "checked": len(candidates),
            "collection_errors": collection_errors,
            **store.counts(),
        }


def approve_valid(
    settings: PipelineSettings,
    limit: int | None = None,
    *,
    source_id: str | None = None,
    selected_ids: set[str] | None = None,
) -> int:
    with Store(settings.paths.state_db) as store:
        candidates = list(store.candidates({CandidateStatus.VALID}))
        if source_id is not None:
            candidates = [candidate for candidate in candidates if candidate.source_id == source_id]
        if selected_ids is not None:
            candidates = [
                candidate for candidate in candidates if candidate.record.id in selected_ids
            ]
        ids = [candidate.record.id for candidate in candidates]
        if limit is not None:
            ids = ids[:limit]
        return store.set_status(ids, CandidateStatus.ACCEPTED)


def review(
    settings: PipelineSettings,
    *,
    status: CandidateStatus = CandidateStatus.VALID,
    source_id: str | None = None,
    limit: int = 20,
) -> list[dict[str, str]]:
    with Store(settings.paths.state_db) as store:
        candidates = list(store.candidates({status}))
    if source_id is not None:
        candidates = [candidate for candidate in candidates if candidate.source_id == source_id]
    return [
        {
            "id": candidate.record.id,
            "behavior": candidate.behavior.value,
            "domain": candidate.domain,
            "source": candidate.source_id,
            "query": next(
                message.content for message in candidate.record.messages if message.role == "user"
            ),
            "target": (
                "tool_call"
                if any(message.tool_calls for message in candidate.record.messages)
                else candidate.record.messages[-1].content
            ),
        }
        for candidate in candidates[:limit]
    ]


def reject(settings: PipelineSettings, ids: list[str]) -> int:
    with Store(settings.paths.state_db) as store:
        return store.set_status(ids, CandidateStatus.REJECTED)


def _split(group_id: str, settings: PipelineSettings) -> str:
    value = int(hashlib.sha256(f"{settings.split_seed}:{group_id}".encode()).hexdigest()[:8], 16)
    point = value / 0xFFFFFFFF
    cumulative = 0.0
    for name, weight in settings.splits.items():
        cumulative += weight
        if point < cumulative:
            return name
    return next(reversed(settings.splits))


def _write_text_atomic(path: Path, content: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def export(settings: PipelineSettings) -> dict[str, int]:
    settings.paths.work_dir.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[str]] = {name: [] for name in settings.splits}
    with Store(settings.paths.state_db) as store:
        accepted = list(store.candidates({CandidateStatus.ACCEPTED}))
    for candidate in accepted:
        split = _split(candidate.group_id, settings)
        grouped[split].append(candidate.record.model_dump_json(exclude_none=True))
    for split, rows in grouped.items():
        path = settings.paths.work_dir / f"{split}.jsonl"
        _write_text_atomic(path, "\n".join(rows) + ("\n" if rows else ""))
    manifest = {
        "project": settings.project_name,
        "schema": ["id", "messages", "tools"],
        "source_revision": settings.source.revision,
        "counts": {name: len(rows) for name, rows in grouped.items()},
    }
    _write_text_atomic(
        settings.paths.work_dir / "manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2),
    )
    return manifest["counts"]


def report(settings: PipelineSettings) -> dict:
    with Store(settings.paths.state_db) as store:
        candidates = list(store.candidates())
        status = store.counts()
    behavior = Counter(candidate.behavior.value for candidate in candidates)
    domain = Counter(candidate.domain for candidate in candidates)
    source = Counter(candidate.source_id for candidate in candidates)
    return {
        "status": status,
        "behavior": dict(sorted(behavior.items())),
        "domain": dict(sorted(domain.items())),
        "source": dict(sorted(source.items())),
    }
