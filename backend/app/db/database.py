"""SQLite persistence for analyses, events and risk summaries.

A single database file holds every analysis run by the service. Writes
are guarded by a module-level lock (workers and the API share the file).
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone

from app.config import settings

_LOCK = threading.Lock()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses (
    id            TEXT PRIMARY KEY,
    filename      TEXT NOT NULL,
    source        TEXT NOT NULL DEFAULT 'upload',
    status        TEXT NOT NULL DEFAULT 'queued',
    progress      INTEGER NOT NULL DEFAULT 0,
    stage         TEXT NOT NULL DEFAULT 'queued',
    detail        TEXT,
    created_at    TEXT NOT NULL,
    completed_at  TEXT,
    video_path    TEXT,
    annotated_path TEXT,
    duration_s    REAL,
    frame_count   INTEGER,
    fps           REAL,
    width         INTEGER,
    height        INTEGER,
    risk_score    INTEGER,
    risk_category TEXT,
    summary       TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id    TEXT NOT NULL,
    event_type     TEXT NOT NULL,
    type_label     TEXT NOT NULL,
    frame_start    INTEGER,
    frame_end      INTEGER,
    timestamp_s    REAL,
    duration_s     REAL,
    severity       INTEGER,
    severity_label TEXT,
    actor_a_class  TEXT,
    actor_a_id     INTEGER,
    actor_b_class  TEXT,
    actor_b_id     INTEGER,
    min_gap_px     REAL,
    min_ttc_s      REAL,
    max_speed_px_s REAL,
    headline       TEXT,
    explanation    TEXT,
    factors        TEXT,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);

CREATE INDEX IF NOT EXISTS idx_events_analysis ON events(analysis_id);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(settings.db_path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _LOCK:
        conn = _connect()
        try:
            conn.executescript(_SCHEMA)
            conn.commit()
        finally:
            conn.close()


def create_analysis(filename: str, source: str, video_path) -> str:
    import uuid

    analysis_id = uuid.uuid4().hex[:12]
    now = datetime.now(timezone.utc).isoformat()
    with _LOCK:
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT INTO analyses (id, filename, source, status, stage,
                                      created_at, video_path)
                VALUES (?, ?, ?, 'queued', 'queued', ?, ?)
                """,
                (analysis_id, filename, source, now, str(video_path)),
            )
            conn.commit()
        finally:
            conn.close()
    return analysis_id


def update_analysis_progress(
    analysis_id: str, *, status: str | None = None, stage: str | None = None,
    progress: int | None = None, detail: str | None = None,
    extra: dict | None = None,
) -> None:
    sets: list[str] = []
    params: list = []
    if status is not None:
        sets.append("status = ?")
        params.append(status)
    if stage is not None:
        sets.append("stage = ?")
        params.append(stage)
    if progress is not None:
        sets.append("progress = ?")
        params.append(progress)
    if detail is not None:
        sets.append("detail = ?")
        params.append(detail)
    if extra:
        sets.append("detail = ?")
        params.append(json.dumps(extra))
    if not sets:
        return
    params.append(analysis_id)
    with _LOCK:
        conn = _connect()
        try:
            conn.execute(f"UPDATE analyses SET {', '.join(sets)} WHERE id = ?", params)
            conn.commit()
        finally:
            conn.close()


def complete_analysis(analysis_id: str, summary: dict, annotated_path, events: list[dict]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _LOCK:
        conn = _connect()
        try:
            conn.execute(
                """
                UPDATE analyses
                  SET status='completed', stage='completed', progress=100,
                      completed_at=?, annotated_path=?,
                      duration_s=?, frame_count=?, fps=?, width=?, height=?,
                      risk_score=?, risk_category=?, summary=?
                WHERE id = ?
                """,
                (
                    now,
                    str(annotated_path),
                    summary.get("duration_s"),
                    summary.get("frame_count"),
                    summary.get("fps"),
                    summary.get("width"),
                    summary.get("height"),
                    summary.get("risk_score"),
                    summary.get("risk_category"),
                    json.dumps(summary),
                    analysis_id,
                ),
            )
            conn.executemany(
                """
                INSERT INTO events (analysis_id, event_type, type_label,
                    frame_start, frame_end, timestamp_s, duration_s, severity,
                    severity_label, actor_a_class, actor_a_id, actor_b_class,
                    actor_b_id, min_gap_px, min_ttc_s, max_speed_px_s,
                    headline, explanation, factors)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                [
                    (
                        analysis_id,
                        e["type"],
                        e["type_label"],
                        e["frame_start"],
                        e["frame_end"],
                        e["timestamp_s"],
                        e["duration_s"],
                        e["severity"],
                        e["severity_label"],
                        e["actor_a_class"],
                        e["actor_a_id"],
                        e["actor_b_class"],
                        e["actor_b_id"],
                        e["min_gap_px"],
                        e["min_ttc_s"],
                        e["max_speed_px_s"],
                        e["headline"],
                        e["explanation"],
                        json.dumps(e["factors"]),
                    )
                    for e in events
                ],
            )
            conn.commit()
        finally:
            conn.close()


def fail_analysis(analysis_id: str, message: str) -> None:
    with _LOCK:
        conn = _connect()
        try:
            conn.execute(
                "UPDATE analyses SET status='failed', stage='failed', detail=? WHERE id = ?",
                (message, analysis_id),
            )
            conn.commit()
        finally:
            conn.close()


def _row_to_analysis(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["summary"] = json.loads(d["summary"]) if d.get("summary") else None
    d["detail"] = json.loads(d["detail"]) if d.get("detail") else None
    return d


def get_analysis(analysis_id: str) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
        return _row_to_analysis(row) if row else None
    finally:
        conn.close()


def list_analyses(limit: int = 20) -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT id, filename, source, status, progress, stage, risk_score,"
            " risk_category, created_at, duration_s, frame_count FROM analyses"
            " ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_events(analysis_id: str) -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM events WHERE analysis_id = ? ORDER BY frame_start", (analysis_id,)
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["factors"] = json.loads(d["factors"]) if d.get("factors") else []
            out.append(d)
        return out
    finally:
        conn.close()