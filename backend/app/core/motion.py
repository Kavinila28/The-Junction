"""Per-object motion modelling.

Keeps a short centroid history per stable track ID and derives smooth
velocity/heading estimates by linear regression over recent frames.
All quantities are in pixels and frames/seconds unless stated.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

_HISTORY = 8  # keep at most this many recent centroid samples per object
_WINDOW = 5  # regression window length


@dataclass
class MotionSample:
    frame: int
    cx: float
    cy: float
    w: float
    h: float


@dataclass
class TrackMotion:
    history: list[MotionSample] = field(default_factory=list)

    def update(self, sample: MotionSample) -> None:
        self.history.append(sample)
        if len(self.history) > _HISTORY:
            self.history.pop(0)

    def velocity_px(self) -> tuple[float, float] | None:
        """Return (vx, vy) pixels/frame from a least-squares fit."""
        n = len(self.history)
        if n < 2:
            return None
        window = self.history[-_WINDOW:]
        frames = np.array([s.frame for s in window], dtype=float)
        xs = np.array([s.cx for s in window], dtype=float)
        ys = np.array([s.cy for s in window], dtype=float)
        if frames[-1] == frames[0]:
            return None
        dt = frames[-1] - frames[0]
        vx = (xs[-1] - xs[0]) / dt
        vy = (ys[-1] - ys[0]) / dt
        return float(vx), float(vy)

    def speed_px_per_frame(self) -> float:
        v = self.velocity_px()
        return float(np.hypot(*v)) if v else 0.0

    def speed_px_per_second(self, fps: float) -> float:
        return self.speed_px_per_frame() * fps

    def acceleration_px_per_frame2(self) -> float:
        """Centroid acceleration estimate (px/frame^2)."""
        if len(self.history) < 3:
            return 0.0
        a = self.history[-3]
        b = self.history[-2]
        c = self.history[-1]
        if b.frame == a.frame or c.frame == b.frame:
            return 0.0
        v1 = np.hypot(b.cx - a.cx, b.cy - a.cy) / (b.frame - a.frame)
        v2 = np.hypot(c.cx - b.cx, c.cy - b.cy) / (c.frame - b.frame)
        return float(v2 - v1)

    def centroid(self) -> tuple[float, float] | None:
        if not self.history:
            return None
        s = self.history[-1]
        return s.cx, s.cy

    def predicted_position(self, seconds: float, fps: float) -> tuple[float, float] | None:
        """Extrapolated centroid ``seconds`` into the future (linear motion)."""
        v = self.velocity_px()
        c = self.centroid()
        if v is None or c is None:
            return None
        vx, vy = v
        return c[0] + vx * seconds * fps, c[1] + vy * seconds * fps

    @property
    def last_box(self) -> tuple[float, float, float, float] | None:
        if not self.history:
            return None
        s = self.history[-1]
        return (s.cx - s.w / 2, s.cy - s.h / 2, s.cx + s.w / 2, s.cy + s.h / 2)


class MotionModel:
    """Registry of live per-track motion states."""

    def __init__(self) -> None:
        self._tracks: dict[int, TrackMotion] = {}

    def has(self, track_id: int) -> bool:
        return track_id in self._tracks

    def get(self, track_id: int) -> TrackMotion:
        return self._tracks.setdefault(track_id, TrackMotion())

    def update(self, frame_idx: int, track_id: int, box) -> TrackMotion:
        x1, y1, x2, y2 = box
        motion = self.get(track_id)
        motion.update(
            MotionSample(
                frame=frame_idx,
                cx=(x1 + x2) / 2.0,
                cy=(y1 + y2) / 2.0,
                w=x2 - x1,
                h=y2 - y1,
            )
        )
        return motion