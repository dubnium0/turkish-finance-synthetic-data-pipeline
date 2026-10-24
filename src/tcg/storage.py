"""SQLite-backed source, candidate, and review state."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Iterator
from datetime import UTC, datetime
from pathlib import Path

from .models import Candidate, CandidateStatus

_SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS source_rows (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    instruction TEXT NOT NULL,
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    raw_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS candidates (
    id TEXT PRIMARY KEY,
    record_json TEXT NOT NULL,
    behavior TEXT NOT NULL,
    domain TEXT NOT NULL,
    source_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    status TEXT NOT NULL,
    errors_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_candidates_group ON candidates(group_id);
"""


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(_SCHEMA)

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> Store:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def add_source_rows(self, rows: Iterable[dict[str, str]]) -> int:
        before = self.connection.total_changes
        with self.connection:
            self.connection.executemany(
                """INSERT OR REPLACE INTO source_rows
                   (id, source_id, instruction, input, output, raw_json)
                   VALUES (:id, :source_id, :instruction, :input, :output, :raw_json)""",
                rows,
            )
        return self.connection.total_changes - before

    def source_rows(self, limit: int | None = None) -> Iterator[sqlite3.Row]:
        sql = "SELECT * FROM source_rows ORDER BY id"
        params: tuple[int, ...] = ()
        if limit is not None:
            sql += " LIMIT ?"
            params = (limit,)
        yield from self.connection.execute(sql, params)

    def put_candidate(
        self, candidate: Candidate, *, preserve_status_if_unchanged: bool = False
    ) -> None:
        now = datetime.now(UTC).isoformat()
        record_json = candidate.record.model_dump_json()
        status = candidate.status.value
        errors_json = json.dumps(candidate.errors, ensure_ascii=False)
        if preserve_status_if_unchanged:
            existing = self.connection.execute(
                """SELECT record_json, behavior, domain, source_id, group_id,
                          status, errors_json
                   FROM candidates WHERE id = ?""",
                (candidate.record.id,),
            ).fetchone()
            unchanged = existing and (
                existing["record_json"],
                existing["behavior"],
                existing["source_id"],
                existing["group_id"],
            ) == (
                record_json,
                candidate.behavior.value,
                candidate.source_id,
                candidate.group_id,
            )
            if unchanged:
                status = existing["status"]
                errors_json = existing["errors_json"]
        with self.connection:
            self.connection.execute(
                """INSERT OR REPLACE INTO candidates
                   (id, record_json, behavior, domain, source_id, group_id,
                    status, errors_json, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    candidate.record.id,
                    record_json,
                    candidate.behavior.value,
                    candidate.domain,
                    candidate.source_id,
                    candidate.group_id,
                    status,
                    errors_json,
                    now,
                ),
            )

    def candidates(self, statuses: set[CandidateStatus] | None = None) -> Iterator[Candidate]:
        sql = "SELECT * FROM candidates"
        params: tuple[str, ...] = ()
        if statuses:
            values = tuple(sorted(status.value for status in statuses))
            sql += f" WHERE status IN ({','.join('?' for _ in values)})"
            params = values
        sql += " ORDER BY id"
        for row in self.connection.execute(sql, params):
            yield Candidate.model_validate(
                {
                    "record": json.loads(row["record_json"]),
                    "behavior": row["behavior"],
                    "domain": row["domain"],
                    "source_id": row["source_id"],
                    "group_id": row["group_id"],
                    "status": row["status"],
                    "errors": json.loads(row["errors_json"]),
                }
            )

    def replace_candidates(self, candidates: Iterable[Candidate]) -> None:
        now = datetime.now(UTC).isoformat()
        rows = [
            (
                candidate.record.id,
                candidate.record.model_dump_json(),
                candidate.behavior.value,
                candidate.domain,
                candidate.source_id,
                candidate.group_id,
                candidate.status.value,
                json.dumps(candidate.errors, ensure_ascii=False),
                now,
            )
            for candidate in candidates
        ]
        with self.connection:
            self.connection.execute("DELETE FROM candidates")
            self.connection.executemany(
                """INSERT INTO candidates
                   (id, record_json, behavior, domain, source_id, group_id,
                    status, errors_json, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )

    def set_status(self, ids: Iterable[str], status: CandidateStatus) -> int:
        now = datetime.now(UTC).isoformat()
        before = self.connection.total_changes
        with self.connection:
            self.connection.executemany(
                "UPDATE candidates SET status = ?, updated_at = ? WHERE id = ?",
                ((status.value, now, candidate_id) for candidate_id in ids),
            )
        return self.connection.total_changes - before

    def counts(self) -> dict[str, int]:
        rows = self.connection.execute(
            "SELECT status, COUNT(*) AS n FROM candidates GROUP BY status ORDER BY status"
        )
        return {row["status"]: row["n"] for row in rows}
