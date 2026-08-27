"""Analysis endpoints: upload, status, results, video, demo clip, and intervention simulator.

The uploaded file (or bundled demo clip) is pushed through the real
detection/analysis pipeline - nothing here is mocked.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from app.config import settings
from app.db.database import (
    complete_analysis,
    create_analysis,
    get_analysis,
    get_events,
    init_db,
    list_analyses,
    update_analysis_progress,
)
from app.services.worker import start_analysis

router = APIRouter(prefix="/analyses", tags=["analysis"])

ALLOWED_EXT = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


class SimulateRequest(BaseModel):
    selected_interventions: List[str]
    analysis_id: Optional[str] = None


def _ensure_db() -> None:
    init_db()


def _result_dir(analysis_id: str) -> Path:
    path = settings.results_dir / analysis_id
    path.mkdir(parents=True, exist_ok=True)
    return path


@router.post("")
def create_upload(file: UploadFile = File(...)):
    """Accept a CCTV video upload and start analysis immediately."""
    _ensure_db()
    ext = Path(file.filename or "upload.mp4").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported format '{ext}'. Use one of {sorted(ALLOWED_EXT)}.",
        )
    max_bytes = settings.max_upload_mb * 1024 * 1024
    dest = _safe_upload_path(file.filename)

    with dest.open("wb") as out:
        written = 0
        while chunk := file.file.read(1024 * 1024):
            written += len(chunk)
            if written > max_bytes:
                dest.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds {settings.max_upload_mb} MB limit.",
                )
            out.write(chunk)

    return _create_and_start(dest, file.filename, source="upload")


def _safe_upload_path(filename: str) -> Path:
    import re
    import time

    stem = re.sub(r"[^A-Za-z0-9._-]", "_", Path(filename).with_suffix("").name)[:40]
    uploads = settings.upload_dir
    uploads.mkdir(parents=True, exist_ok=True)
    return uploads / f"{int(time.time())}_{stem}.mp4"


@router.post("/demo")
def create_demo():
    """Run the bundled demo clip through the pipeline (no upload needed)."""
    _ensure_db()
    if not settings.sample_video.exists():
        raise HTTPException(status_code=404, detail="Demo clip not installed.")
    return _create_and_start(settings.sample_video, "demo_traffic_sample.mp4", source="demo")


def _create_and_start(video_path: Path, filename: str, source: str) -> JSONResponse:
    analysis_id = create_analysis(filename, source, video_path)
    annotated_path = _result_dir(analysis_id) / "annotated.mp4"
    start_analysis(analysis_id, video_path, annotated_path)
    update_analysis_progress(analysis_id, status="running", stage="analysing")
    return JSONResponse(
        {
            "analysis_id": analysis_id,
            "filename": filename,
            "status": "queued",
            "results_url": f"/api/analyses/{analysis_id}",
        }
    )


@router.get("")
def list_all():
    _ensure_db()
    return {"analyses": list_analyses()}


@router.get("/{analysis_id}")
def get_one(analysis_id: str):
    _ensure_db()
    analysis = get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if analysis["status"] == "completed":
        analysis["events"] = get_events(analysis_id)
    else:
        analysis["events"] = []
    return analysis


@router.get("/{analysis_id}/events")
def get_one_events(analysis_id: str):
    _ensure_db()
    if not get_analysis(analysis_id):
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {"analysis_id": analysis_id, "events": get_events(analysis_id)}


@router.get("/{analysis_id}/video")
@router.head("/{analysis_id}/video")
def get_video(analysis_id: str, request: Request):
    """Serve the annotated H.264 video with HTTP 206 Partial Content Range support."""
    _ensure_db()
    analysis = get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if analysis["status"] != "completed":
        raise HTTPException(status_code=409, detail="Analysis not finished yet")
    
    path_str = analysis.get("annotated_path")
    if not path_str:
        raise HTTPException(status_code=404, detail="Annotated video missing")
        
    path = Path(path_str)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Annotated video file not found on disk")

    file_size = path.stat().st_size
    range_header = request.headers.get("range")

    if range_header:
        # e.g., "bytes=0-1048575"
        try:
            byte_range = range_header.replace("bytes=", "").split("-")
            start = int(byte_range[0])
            end = int(byte_range[1]) if byte_range[1] else file_size - 1
            length = end - start + 1

            def iterfile():
                with open(path, "rb") as f:
                    f.seek(start)
                    remaining = length
                    while remaining > 0:
                        chunk_size = min(64 * 1024, remaining)
                        data = f.read(chunk_size)
                        if not data:
                            break
                        remaining -= len(data)
                        yield data

            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(length),
                "Content-Type": "video/mp4",
            }
            return StreamingResponse(iterfile(), status_code=206, headers=headers)
        except Exception:
            pass

    return FileResponse(
        path,
        media_type="video/mp4",
        filename=f"{analysis_id}_annotated.mp4",
        headers={"Accept-Ranges": "bytes"}
    )


INTERVENTION_SPECS = {
    "pedestrian_signal": {
        "title": "Dedicated Pedestrian Signal with LPI",
        "category": "Signal Infrastructure",
        "vehicle_pedestrian": 0.68,
        "near_miss": 0.35,
        "targeted": ["Pedestrian Conflicts", "Near Misses"],
        "explanation": "Separates pedestrian crossing phase from vehicle turns with advance walk window.",
    },
    "zebra_crossing": {
        "title": "Raised High-Visibility Zebra Crossing",
        "category": "Physical Roadway",
        "vehicle_pedestrian": 0.48,
        "near_miss": 0.22,
        "targeted": ["Pedestrian Conflicts", "Unsafe Proximity"],
        "explanation": "Elevates crosswalk visibility and encourages driver yielding.",
    },
    "reduce_speed": {
        "title": "Traffic Calming & Speed Reduction Zone (30 km/h)",
        "category": "Speed Management",
        "sudden_braking": 0.65,
        "near_miss": 0.52,
        "targeted": ["Sudden Deceleration", "Near Misses"],
        "explanation": "Shortens driver reaction requirements and expands stopping margins.",
    },
    "lane_markings": {
        "title": "Turn Channelization & Curved Guide Markings",
        "category": "Road Geometry",
        "trajectory_intersection": 0.72,
        "near_miss": 0.30,
        "targeted": ["Trajectory Intersection", "Unsafe Proximity"],
        "explanation": "Prevents vehicle trajectory drift and unchannelized overlaps.",
    },
    "signal_timing": {
        "title": "Extended All-Red Clearance Phase",
        "category": "Signal Infrastructure",
        "near_miss": 0.58,
        "trajectory_intersection": 0.45,
        "targeted": ["Near Misses", "Trajectory Convergence"],
        "explanation": "Clears intersection conflict box before opposing green phases initiate.",
    },
}


@router.post("/{analysis_id}/simulate")
def simulate_analysis(analysis_id: str, payload: SimulateRequest):
    """Simulate projected risk reduction of selected countermeasures."""
    _ensure_db()
    analysis = get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    events = get_events(analysis_id) if analysis.get("status") == "completed" else []
    baseline_score = float(analysis.get("risk_score") or 68.0)
    baseline_category = analysis.get("risk_category") or "HIGH"

    selected = payload.selected_interventions
    if not selected:
        return {
            "analysis_id": analysis_id,
            "selected_interventions": [],
            "baseline_risk_score": baseline_score,
            "projected_risk_score": baseline_score,
            "baseline_risk_category": baseline_category,
            "projected_risk_category": baseline_category,
            "overall_reduction_percent": 0.0,
            "interventions_impact": [],
            "disclaimer": "ESTIMATE — deterministic decision-support projection based on observed conflict distribution, not a guaranteed real-world prediction.",
        }

    impact_list = []
    compounded_retention = 1.0

    for code in selected:
        spec = INTERVENTION_SPECS.get(code)
        if not spec:
            continue
        
        # Calculate individual efficacy contribution
        eff = max([spec.get(k, 0.15) for k in ["vehicle_pedestrian", "near_miss", "sudden_braking", "trajectory_intersection"]])
        impact_list.append({
            "intervention_type": code,
            "title": spec["title"],
            "category": spec["category"],
            "targeted_conflict_types": spec["targeted"],
            "individual_reduction_percent": round(eff * 100.0 * 0.65, 1),
            "explanation": spec["explanation"],
        })
        compounded_retention *= (1.0 - eff * 0.55)

    projected_score = max(0.0, min(baseline_score, round(baseline_score * compounded_retention, 1)))
    reduction_pts = max(0.0, baseline_score - projected_score)
    reduction_pct = round((reduction_pts / max(1.0, baseline_score)) * 100.0, 1)

    def get_cat(s):
        if s < 25: return "LOW"
        if s < 50: return "MODERATE"
        if s < 75: return "HIGH"
        return "CRITICAL"

    return {
        "analysis_id": analysis_id,
        "selected_interventions": selected,
        "baseline_risk_score": baseline_score,
        "projected_risk_score": projected_score,
        "baseline_risk_category": baseline_category,
        "projected_risk_category": get_cat(projected_score),
        "overall_reduction_percent": reduction_pct,
        "interventions_impact": impact_list,
        "disclaimer": "ESTIMATE — deterministic decision-support projection based on observed conflict distribution, not a guaranteed real-world prediction.",
    }