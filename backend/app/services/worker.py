"""Background analysis worker.

Analysis runs on a daemon thread so the API stays responsive while a clip
is being processed. Progress is written to SQLite and polled by the
frontend.
"""

from __future__ import annotations

import threading

from app.core.pipeline import Pipeline
from app.db.database import complete_analysis, fail_analysis

_QUEUE = {}
_QUEUE_LOCK = threading.Lock()


def start_analysis(analysis_id: str, video_path, annotated_path) -> None:
    """Queue+run an analysis in the background (idempotent per analysis)."""
    with _QUEUE_LOCK:
        if analysis_id in _QUEUE:
            return
        event = threading.Event()
        thread = threading.Thread(
            target=_run_worker,
            args=(analysis_id, video_path, annotated_path, event),
            name=f"analysis-{analysis_id}",
            daemon=True,
        )
        _QUEUE[analysis_id] = event
    thread.start()


def _run_worker(analysis_id, video_path, annotated_path, event) -> None:
    try:
        result = Pipeline(analysis_id).run(video_path, annotated_path)
        complete_analysis(analysis_id, result.summary, annotated_path, result.events)
    except Exception as exc:  # noqa: BLE001
        import traceback

        fail_analysis(analysis_id, f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}")
    finally:
        with _QUEUE_LOCK:
            _QUEUE.pop(analysis_id, None)
            event.set()