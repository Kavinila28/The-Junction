"""Draw detection, tracking, trajectory and conflict overlays on frames.

Pure OpenCV drawing - no ML here. The annotator receives the live tracked
objects and active conflict alerts for each frame and renders the visual
language of the dashboard onto the original footage.
"""

from __future__ import annotations

import cv2
import numpy as np

CLASS_COLORS = {
    "pedestrian": (34, 211, 238),    # cyan
    "bicycle": (163, 230, 53),       # lime
    "car": (96, 165, 250),           # blue
    "motorcycle": (245, 158, 11),    # amber
    "bus": (52, 211, 153),           # emerald
    "truck": (244, 114, 182),        # pink
}

SEVERITY_COLORS = {
    1: (0, 255, 255),      # yellow (LOW)
    2: (0, 165, 255),      # orange (MODERATE)
    3: (0, 80, 255),       # red (HIGH)
    4: (0, 0, 220),        # deep red (CRITICAL)
}

TRAIL_LEN = 14
FONT = cv2.FONT_HERSHEY_SIMPLEX


class Annotator:
    def __init__(self, width: int, height: int, fps: float) -> None:
        self.w = width
        self.h = height
        self.fps = fps
        self._trails: dict[int, list[tuple[int, int]]] = {}

    def render(
        self,
        frame: np.ndarray,
        tracks: list,
        active: list[dict],
        frame_idx: int,
        hud: dict,
    ) -> np.ndarray:
        """tracks: TrackedObject list; active: active alert dicts from engine."""
        overlay = frame.copy()

        # trajectories / trails (draw beneath boxes)
        seen: set[int] = set()
        for t in tracks:
            trail = self._trails.setdefault(t.track_id, [])
            trail.append((int(t.centroid[0]), int(t.centroid[1])))
            if len(trail) > TRAIL_LEN:
                trail.pop(0)
            seen.add(t.track_id)
            color = CLASS_COLORS.get(t.cls_name, (200, 200, 200))
            if len(trail) >= 2:
                for i in range(1, len(trail)):
                    alpha = i / max(len(trail), 1)
                    cv2.line(overlay, trail[i - 1], trail[i], tuple(int(c * alpha) for c in color), 2)
        for tid in list(self._trails):
            if tid not in seen:
                self._trails.pop(tid, None)

        # detection boxes + labels
        for t in tracks:
            x1, y1, x2, y2 = (int(v) for v in t.box)
            color = CLASS_COLORS.get(t.cls_name, (200, 200, 200))
            label = f"{t.cls_name}#{t.track_id}"
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
            (tw, th), _ = cv2.getTextSize(label, FONT, 0.5, 1)
            cv2.rectangle(overlay, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
            cv2.putText(overlay, label, (x1 + 2, y1 - 4), FONT, 0.5, (15, 20, 35), 1, cv2.LINE_AA)

        # conflict alerts
        for alert in active:
            color = SEVERITY_COLORS.get(alert.get("severity", 2), (0, 165, 255))
            ids = (alert.get("actor_a_id"), alert.get("actor_b_id"))
            centers = []
            for tid in ids:
                if tid is None:
                    continue
                tr = next((t for t in tracks if t.track_id == tid), None)
                if tr:
                    cx, cy = tr.centroid
                    centers.append((int(cx), int(cy)))
                    x1, y1, x2, y2 = (int(v) for v in tr.box)
                    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 3)
            if len(centers) == 2:
                cv2.line(overlay, centers[0], centers[1], color, 2)
                mid = ((centers[0][0] + centers[1][0]) // 2, (centers[0][1] + centers[1][1]) // 2)
                tag = alert["type"].replace("_", " ").upper()
                (tw, th), _ = cv2.getTextSize(tag, FONT, 0.5, 1)
                cv2.rectangle(overlay, (mid[0], mid[1] - th - 6), (mid[0] + tw + 4, mid[1]), color, -1)
                cv2.putText(overlay, tag, (mid[0] + 2, mid[1] - 4), FONT, 0.5, (10, 12, 20), 1, cv2.LINE_AA)

        self._draw_hud(overlay, frame_idx, hud)
        return overlay

    def _draw_hud(self, frame: np.ndarray, frame_idx: int, hud: dict) -> None:
        # top-left brand
        cv2.rectangle(frame, (12, 10), (260, 34), (13, 18, 30), -1)
        cv2.putText(frame, "THE JUNCTION  |  conflict intelligence", (18, 28), FONT, 0.55, (56, 189, 248), 1, cv2.LINE_AA)

        # top-right risk chip
        score = hud.get("risk_score", "-")
        cat = hud.get("risk_category", "")
        color = SEVERITY_COLORS.get(_cat_level(cat), (0, 165, 255))
        if cat:
            chip = f"RISK {score} / 100  {cat}"
        else:
            chip = f"RISK {score} / 100"
        (tw, th), _ = cv2.getTextSize(chip, FONT, 0.6, 1)
        x = self.w - tw - 30
        cv2.rectangle(frame, (x - 8, 12), (x + tw + 12, 12 + th + 12), color, -1)
        cv2.putText(frame, chip, (x, 12 + th + 4), FONT, 0.6, (15, 18, 25), 1, cv2.LINE_AA)

        # bottom-right meta
        ev = hud.get("total_events", 0)
        t = frame_idx / self.fps
        meta = f"frame {frame_idx}  ·  {t:.1f}s  ·  events {ev}"
        (mw, mh), _ = cv2.getTextSize(meta, FONT, 0.45, 1)
        cv2.rectangle(frame, (self.w - mw - 30, self.h - 40), (self.w - 14, self.h - 12), (13, 18, 30), -1)
        cv2.putText(frame, meta, (self.w - mw - 24, self.h - 20), FONT, 0.45, (141, 162, 192), 1, cv2.LINE_AA)


def _cat_level(cat: str) -> int:
    return {"LOW": 1, "MODERATE": 2, "HIGH": 3, "CRITICAL": 4}.get(cat, 2)