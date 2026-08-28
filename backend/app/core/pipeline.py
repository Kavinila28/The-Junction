"""End-to-end analysis pipeline.

Reads a CCTV video, runs YOLO+ByteTrack (via the detector), stabilises
track identity, models motion, runs the conflict engine, renders the
annotated video with the final calculated Junction Risk Score, and
completes with full forensic event provenance.

Runs in a worker thread pool (see services/worker.py) so FastAPI stays
responsive while a clip is being processed.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np

from app.config import settings
from app.core.annotator import Annotator
from app.core.conflict import ConflictEngine, TrackedObject
from app.core.detector import get_detector
from app.core.media import VideoWriter, read_video_props
from app.core.motion import MotionModel
from app.core.risk import compute_risk
from app.core.tracker import TrackContinuity
from app.db.database import update_analysis_progress

logger = logging.getLogger("the_junction.pipeline")


@dataclass
class PipelineResult:
    summary: dict = field(default_factory=dict)
    events: list[dict] = field(default_factory=list)


class Pipeline:
    """Analyse one video file; writes an annotated H.264 mp4."""

    def __init__(self, analysis_id: str) -> None:
        self.analysis_id = analysis_id

    def run(self, video_path, out_path) -> PipelineResult:
        t0 = time.time()
        logger.info(f"[{self.analysis_id}] Pipeline.run started for video: {video_path}")

        props = read_video_props(video_path)
        fps = props["fps"]
        w, h, total = props["width"], props["height"], props["frame_count"]
        stride = max(1, int(settings.frame_stride))
        num_samples = math.ceil(total / stride)

        logger.info(
            f"[{self.analysis_id}] Video properties: {w}x{h} @ {fps:.1f} FPS, {total} frames | "
            f"Frame stride: {stride} ({num_samples} frames to analyse)"
        )

        update_analysis_progress(
            self.analysis_id,
            status="running",
            stage="analysing",
            progress=1,
            extra={"current_frame": 0, "total_frames": total, "detections": 0, "events": 0},
        )

        detector = get_detector()
        continuity = TrackContinuity()
        motion = MotionModel()
        engine = ConflictEngine(w, h, fps)

        class_counts: dict[str, int] = {}
        max_concurrent: dict[str, int] = {}
        objects_seen: set[int] = set()

        frame_tracks: dict[int, list[TrackedObject]] = {}
        frame_active: dict[int, list[dict]] = {}

        logger.info(f"[{self.analysis_id}] Starting Pass 1: YOLO inference and ByteTrack tracking (stride={stride})...")

        # -------------------------------------------------------------
        # PASS 1: Detection, Tracking, Motion, & Conflict Analysis
        # -------------------------------------------------------------
        results = detector.track_stream(str(video_path), vid_stride=stride)
        k = 0
        dets = []

        for result in results:
            actual_frame = min(k * stride, total - 1)
            dets = detector.detections_from_result(result)
            dets = [d for d in dets if d.track_id is not None]
            dets = continuity.apply(actual_frame, dets)

            tracked: list[TrackedObject] = []
            for d in dets:
                motion_obj = motion.update(actual_frame, d.track_id, d.box)
                v = motion_obj.velocity_px()
                speed_px_s = motion_obj.speed_px_per_second(fps)
                tracked.append(
                    TrackedObject(
                        track_id=d.track_id,
                        cls_name=d.cls_name,
                        box=d.box,
                        centroid=motion_obj.centroid() or ((0.0, 0.0)),
                        velocity=v,
                        speed_px_s=speed_px_s,
                        accel_px_f2=motion_obj.acceleration_px_per_frame2(),
                    )
                )
                class_counts[d.cls_name] = class_counts.get(d.cls_name, 0) + 1
                objects_seen.add(d.track_id)

            if tracked:
                per_class = {}
                for t in tracked:
                    per_class[t.cls_name] = per_class.get(t.cls_name, 0) + 1
                for cls, n in per_class.items():
                    max_concurrent[cls] = max(max_concurrent.get(cls, 0), n)

            speeds = [t.speed_px_s for t in tracked]
            v_p95 = float(np.percentile(speeds, 95)) if len(speeds) > 3 else 40.0
            active = engine.update(
                actual_frame, tracked, {"v_p95_px_s": v_p95}
            )

            frame_tracks[actual_frame] = tracked
            frame_active[actual_frame] = active

            k += 1
            if k == 1 or k % 3 == 0 or k >= num_samples:
                pct = min(88, max(1, int(88 * k / max(num_samples, 1))))
                update_analysis_progress(
                    self.analysis_id,
                    status="running",
                    stage="analysing",
                    progress=pct,
                    extra={
                        "current_frame": actual_frame,
                        "total_frames": total,
                        "detections": len(dets),
                        "events": len(engine.events),
                    },
                )
                if k % 15 == 0 or k == 1 or k >= num_samples:
                    logger.info(
                        f"[{self.analysis_id}] Pass 1 progress: frame {actual_frame}/{total} "
                        f"(sampled {k}/{num_samples} = {pct}%) | events: {len(engine.events)}"
                    )

        events = engine.finish(last_frame=total)
        duration_s = total / fps
        risk = compute_risk(events, duration_s)

        # Final HUD metrics containing actual computed Risk Score and Category
        final_hud = {
            "risk_score": risk.score,
            "risk_category": risk.category,
            "total_events": len(events),
        }

        logger.info(
            f"[{self.analysis_id}] Pass 1 complete in {time.time()-t0:.2f}s. "
            f"Risk Score: {risk.score}/100 ({risk.category}). Starting Pass 2 (H.264 rendering)..."
        )

        # -------------------------------------------------------------
        # PASS 2: Video Annotation & Encoding with Final Risk HUD
        # -------------------------------------------------------------
        update_analysis_progress(
            self.analysis_id,
            status="running",
            stage="rendering",
            progress=90,
            extra={
                "current_frame": total,
                "total_frames": total,
                "detections": 0,
                "events": len(events),
                "risk_score": risk.score,
            },
        )

        annotator = Annotator(w, h, fps)
        writer = VideoWriter(out_path, w, h, fps)
        cap = cv2.VideoCapture(str(video_path))
        render_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Map to closest sampled track data for smooth rendering
            sample_key = (render_idx // stride) * stride
            tr = frame_tracks.get(sample_key, frame_tracks.get(render_idx, []))
            act = frame_active.get(sample_key, frame_active.get(render_idx, []))
            framed = annotator.render(frame, tr, act, render_idx, final_hud)
            writer.write(framed)
            render_idx += 1

            if render_idx == 1 or render_idx % 10 == 0 or render_idx >= total:
                pct = min(98, 90 + int(8 * render_idx / max(total, 1)))
                update_analysis_progress(
                    self.analysis_id,
                    status="running",
                    stage="rendering",
                    progress=pct,
                    extra={
                        "current_frame": render_idx,
                        "total_frames": total,
                        "detections": 0,
                        "events": len(events),
                        "risk_score": risk.score,
                    },
                )

        cap.release()
        writer.close()
        t_total = time.time() - t0
        logger.info(f"[{self.analysis_id}] Pass 2 complete. Video saved to {out_path}. Total pipeline runtime: {t_total:.2f}s")

        summary = {
            "duration_s": round(duration_s, 2),
            "frame_count": total,
            "fps": fps,
            "width": w,
            "height": h,
            "analysed_frames": k,
            "frame_stride": stride,
            "objects_tracked": len(objects_seen),
            "class_counts": class_counts,
            "max_concurrent": max_concurrent,
            "risk_score": risk.score,
            "risk_category": risk.category,
            "counts": risk.counts,
            "severity_counts": risk.severity_counts,
            "events_per_minute": risk.events_per_minute,
            "factors": risk.factors,
            "recommendations": risk.recommendations,
            "processing_seconds": round(t_total, 2),
            "video_codec": writer.backend,
        }

        event_dicts = []
        for ev in events:
            event_dicts.append(_event_to_dict(ev))

        return PipelineResult(summary=summary, events=event_dicts)


def _event_to_dict(ev) -> dict:
    return {
        "type": ev.type,
        "type_label": {
            "near_miss": "Near miss",
            "vehicle_pedestrian": "Vehicle-pedestrian",
            "trajectory_intersection": "Path intersection",
            "sudden_braking": "Sudden braking",
        }.get(ev.type, ev.type),
        "frame_start": ev.frame_start,
        "frame_end": ev.frame_end,
        "timestamp_s": round(ev.timestamp_s, 2),
        "duration_s": round(ev.duration_s, 2),
        "severity": ev.severity,
        "severity_label": ev.severity_label,
        "actor_a_class": ev.actor_a,
        "actor_a_id": ev.actor_a_id,
        "actor_b_class": ev.actor_b,
        "actor_b_id": ev.actor_b_id,
        "min_gap_px": round(ev.min_gap_px, 1),
        "min_ttc_s": round(ev.min_ttc_s, 2) if ev.min_ttc_s < 1e8 else None,
        "max_speed_px_s": round(ev.max_speed_px_s, 1),
        "headline": ev.headline,
        "explanation": ev.explanation,
        "factors": ev.factors,
    }