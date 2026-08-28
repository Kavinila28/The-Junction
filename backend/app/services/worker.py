"""Background analysis worker.

Analysis runs in a dedicated thread pool so the API stays responsive
while a clip is being processed. Progress and errors are written to SQLite
and polled by the frontend.
"""

from __future__ import annotations

import concurrent.futures
import logging
import os
import threading
import traceback

from app.config import settings
from app.core.pipeline import Pipeline
from app.db.database import complete_analysis, fail_analysis, update_analysis_progress

logger = logging.getLogger("the_junction.worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="junction-worker")
_FUTURES: dict[str, concurrent.futures.Future] = {}
_LOCK = threading.Lock()


def start_analysis(analysis_id: str, video_path, annotated_path) -> None:
    """Queue+run an analysis in the background."""
    with _LOCK:
        if analysis_id in _FUTURES and not _FUTURES[analysis_id].done():
            logger.info(f"[PID {os.getpid()}] [{analysis_id}] Analysis already active, skipping duplicate submit.")
            return

        logger.info(f"[PID {os.getpid()}] [{analysis_id}] Submitting worker task | DB: {settings.db_path} | Video: {video_path}")
        future = _EXECUTOR.submit(_run_worker, analysis_id, video_path, annotated_path)
        _FUTURES[analysis_id] = future


def _run_worker(analysis_id: str, video_path, annotated_path) -> None:
    pid = os.getpid()
    db_path = str(settings.db_path)
    logger.info(f"[PID {pid}] [{analysis_id}] Worker started | DB: {db_path} | Video: {video_path}")
    try:
        pipeline = Pipeline(analysis_id)
        result = pipeline.run(video_path, annotated_path)
        complete_analysis(analysis_id, result.summary, annotated_path, result.events)
        logger.info(f"[PID {pid}] [{analysis_id}] Worker completed | DB: {db_path} | Risk Score: {result.summary.get('risk_score')}")
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
        logger.error(f"[PID {pid}] [{analysis_id}] Worker failed | DB: {db_path} | Error:\n{err}")
        fail_analysis(analysis_id, err)
        update_analysis_progress(
            analysis_id,
            status="failed",
            stage="failed",
            detail=f"{type(exc).__name__}: {exc}",
        )
    finally:
        with _LOCK:
            _FUTURES.pop(analysis_id, None)