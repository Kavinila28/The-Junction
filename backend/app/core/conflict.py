"""Conflict detection for a single CCTV clip.

Detects four event families from real tracked detections:

* ``near_miss``            - two objects converge closer than a safe gap
* ``vehicle_pedestrian``   - a vehicle closes on a pedestrian
* ``trajectory_intersection`` - predicted straight-line paths cross close ahead
* ``sudden_braking``       - a vehicle decelerates sharply while moving

Intensity is derived from measured geometry (pixel gaps, TTC, relative
speed) and motion; nothing here is simulated or fabricated.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

# --- tuning constants (pixels, frames, seconds) ---------------------------

VEHICLE_CLASSES = {"car", "motorcycle", "bus", "truck", "bicycle"}
PEDESTRIAN_CLASS = "pedestrian"

# Gap thresholds expressed as fractions of min(frame width, height).
GAP_BASE = 0.10        # "dangerous" edge-to-edge clearance
GAP_FAR = 0.20         # start watching a pair this far out
GAP_ESCAPE = 0.30      # leave the episode only beyond this; TTC<3s keeps it

MIN_CLOSE_FRAMES = 3   # close-count threshold before a weak approach opens
ESCAPE_FRAMES = 10     # consecutive wide frames before an episode closes

TTC_FAR = 2.5          # seconds; below this the pair is considered converging
TTC_HARD = 0.8         # seconds; adds severity
TTC_STRONG = 1.5       # seconds; counts as a strong approach

PREDICT_SECONDS = 1.2  # look-ahead for trajectory intersection

MIN_REL_SPEED_PX_S = 12.0  # relative speed needed to count a static overlap

BRAKE_ENTER_SPEED = 2.2   # px/frame the object must exceed before braking
BRAKE_DECEL_PER_F2 = 0.9  # px/frame^2 negative accel to call it braking
BRAKE_MIN_FRAMES = 2      # sustained braking frames to open an episode
BRAKE_RESUME = 4          # braking frames below threshold before episode closes
BRAKE_HARSH_PX_S2 = 45.0  # absolute decel (px/s^2) that upgrades severity

_SEV_WEIGHT = {1: 0.4, 2: 0.8, 3: 1.5, 4: 2.5}
_PED_SEV_BUMP = 1


@dataclass
class TrackedObject:
    """A detected, tracked object for one frame."""

    track_id: int
    cls_name: str
    box: tuple[float, float, float, float]
    centroid: tuple[float, float]
    velocity: Optional[tuple[float, float]]  # px/frame
    speed_px_s: float
    accel_px_f2: float


@dataclass
class ConflictEvent:
    """A completed conflict episode."""

    type: str
    frame_start: int
    frame_end: int
    timestamp_s: float
    duration_s: float
    severity: int
    severity_label: str
    actor_a: Optional[str]
    actor_a_id: Optional[int]
    actor_b: Optional[str]
    actor_b_id: Optional[int]
    min_gap_px: float
    min_ttc_s: float
    max_speed_px_s: float
    headline: str
    explanation: str
    factors: list[str]


@dataclass
class _Episode:
    kind: str = ""            # conflict type
    start: int = 0
    min_gap: float = 1e9
    min_ttc: float = 1e9
    max_rel_speed: float = 0.0
    actor_a: Optional[str] = None
    actor_a_id: Optional[int] = None
    actor_b: Optional[str] = None
    actor_b_id: Optional[int] = None


@dataclass
class _PairState:
    close_count: int = 0
    escape_count: int = 0
    episode: Optional[_Episode] = None


def box_center(box) -> tuple[float, float]:
    return (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0


def box_edge_gap(a, b) -> float:
    """Clearance between two boxes along x/y then euclidean (0 if overlapped)."""
    dx = max(0.0, abs((a[0] + a[2]) / 2 - (b[0] + b[2]) / 2) - ((a[2] - a[0]) + (b[2] - b[0])) / 2)
    dy = max(0.0, abs((a[1] + a[3]) / 2 - (b[1] + b[3]) / 2) - ((a[3] - a[1]) + (b[3] - b[1])) / 2)
    return float(math.hypot(dx, dy))


class ConflictEngine:
    """Frame-by-frame conflict detection and episode management."""

    def __init__(self, width: int, height: int, fps: float) -> None:
        self.w = width
        self.h = height
        self.fps = fps
        self.gap_base = GAP_BASE * min(width, height)
        self.gap_far = GAP_FAR * min(width, height)
        self.gap_escape = GAP_ESCAPE * min(width, height)
        self._pairs: dict[tuple[int, int], _PairState] = {}
        self._brakes: dict[int, dict] = {}
        self.events: list[ConflictEvent] = []
        self._active: list[ConflictEvent] = []
        self.frame_density: list[tuple[int, int]] = []  # (frame, n_objects)

    # -- public API ---------------------------------------------------------

    def update(
        self,
        frame_idx: int,
        tracks: list[TrackedObject],
        seg_velocity_stats: dict,
    ) -> list[dict]:
        """Feed one frame of tracked objects; returns active alerts (dicts)."""
        self.frame_density.append((frame_idx, len(tracks)))
        self._update_pairs(frame_idx, tracks)
        self._update_braking(frame_idx, tracks, seg_velocity_stats)
        return [
            {
                "type": a.type,
                "actor_a": a.actor_a,
                "actor_a_id": a.actor_a_id,
                "actor_b": a.actor_b,
                "actor_b_id": a.actor_b_id,
                "severity": a.severity,
            }
            for a in self._active
        ]

    def finish(self, last_frame: int | None = None) -> list[ConflictEvent]:
        """Close any open episodes and return all completed events."""
        if last_frame is None:
            last_frame = max((e.frame_end for e in self.events), default=0)
        for key, state in list(self._pairs.items()):
            if state.episode is not None:
                self._close_pair(key, state, last_frame)
        for tid, st in list(self._brakes.items()):
            if st.get("episode"):
                self._close_brake(tid, st)
        self._active = []
        return self.events

    # -- pair conflicts -------------------------------------------------------

    def _update_pairs(self, frame_idx: int, tracks: list[TrackedObject]) -> None:
        by_id = {t.track_id: t for t in tracks}
        active_now: list[ConflictEvent] = []

        pairs = self._candidate_pairs(tracks)
        for (ida, idb) in pairs:
            a, b = by_id[ida], by_id[idb]
            key = (min(ida, idb), max(ida, idb))
            state = self._pairs.setdefault(key, _PairState())

            gap = box_edge_gap(a.box, b.box)
            ttc = self._pair_ttc(a, b)

            dangerous = gap < self.gap_far or (ttc is not None and ttc < TTC_FAR)
            strong = gap < self.gap_base or (ttc is not None and ttc < TTC_STRONG)
            in_episode = state.episode is not None

            # Relative speed between the pair (px/s) - used to ignore pairs of
            # objects that merely rest touching (static overlap is not a conflict).
            rel = 0.0
            if a.velocity and b.velocity:
                rel = math.hypot(a.velocity[0] - b.velocity[0], a.velocity[1] - b.velocity[1]) * self.fps

            if dangerous:
                if strong:
                    state.close_count += 2 if rel >= MIN_REL_SPEED_PX_S else 1
                else:
                    state.close_count += 1
                state.escape_count = 0
            else:
                state.close_count = max(0, state.close_count - 1)
                state.escape_count += 1

            if in_episode:
                ep = state.episode
                ep.min_gap = min(ep.min_gap, gap)
                if ttc is not None:
                    ep.min_ttc = min(ep.min_ttc, ttc)
                ep.max_rel_speed = max(ep.max_rel_speed, rel)
                if state.escape_count >= ESCAPE_FRAMES:
                    self._close_pair(key, state, frame_idx)
                else:
                    active_now.append(self._expand(a, b, ep))
                continue

            if state.close_count >= MIN_CLOSE_FRAMES and rel >= MIN_REL_SPEED_PX_S:
                kind = self._classify(a, b, gap, ttc)
                state.episode = _Episode(
                    kind=kind, start=frame_idx, actor_a=a.cls_name,
                    actor_a_id=ida, actor_b=b.cls_name, actor_b_id=idb,
                )
                ep = state.episode
                ep.min_gap = min(ep.min_gap, gap)
                if ttc is not None:
                    ep.min_ttc = min(ep.min_ttc, ttc)
                ep.max_rel_speed = max(ep.max_rel_speed, rel)
                active_now.append(self._expand(a, b, ep))

        # Remove dead pairs rarely; close any episode that was mid-flight for
        # a pair that has stopped co-occurring in the frame.
        alive = set(pairs)
        for key in [k for k in self._pairs if k not in alive]:
            state = self._pairs[key]
            if state.episode is not None:
                self._close_pair(key, state, frame_idx)
            del self._pairs[key]

        self._active = active_now

    def _candidate_pairs(self, tracks: list[TrackedObject]) -> list[tuple[int, int]]:
        by_id = {t.track_id: t for t in tracks}
        # Cheap spatial prune: distance between centroids < 2*view scale.
        pairs: list[tuple[int, int]] = []
        ids = list(by_id)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = by_id[ids[i]], by_id[ids[j]]
                if a.cls_name == PEDESTRIAN_CLASS and b.cls_name == PEDESTRIAN_CLASS:
                    continue  # pedestrian-pedestrian has no road-conflict meaning
                ca, cb = a.centroid, b.centroid
                if math.hypot(ca[0] - cb[0], ca[1] - cb[1]) > 2.5 * min(self.w, self.h):
                    continue
                pairs.append((ids[i], ids[j]))
        return pairs

    def _pair_ttc(self, a: TrackedObject, b: TrackedObject) -> Optional[float]:
        """Time (s) until centroids meet if both keep current velocity."""
        if not a.velocity or not b.velocity:
            return None
        u = np.array(a.centroid) - np.array(b.centroid)
        dist = float(np.hypot(*u))
        if dist < 1e-6:
            return 0.0
        u = u / dist
        vrel = (np.array(a.velocity) - np.array(b.velocity)) * self.fps
        closing = float(np.dot(vrel, u))
        if closing >= 1e-3:  # moving apart
            return None
        return dist / max(abs(closing), 1e-6)

    def _classify(self, a: TrackedObject, b: TrackedObject, gap: float, ttc: Optional[float]) -> str:
        cls_pair = (a.cls_name, b.cls_name)
        if PEDESTRIAN_CLASS in cls_pair:
            # A pedestrian sharing space with any wheeled road user in a tight
            # window is a pedestrian conflict regardless of approach direction.
            if gap < self.gap_base or (ttc is not None and ttc < TTC_STRONG * 2):
                return "vehicle_pedestrian"
            return "near_miss"
        # vehicle-vehicle
        if ttc is not None and ttc < 2.0:
            pa, pb = (
                _predicted(a.centroid, a.velocity, PREDICT_SECONDS, self.fps),
                _predicted(b.centroid, b.velocity, PREDICT_SECONDS, self.fps),
            )
            if pa and pb:
                proj_dist = math.hypot(pa[0] - pb[0], pa[1] - pb[1])
                if proj_dist < 1.5 * self.gap_base:
                    return "trajectory_intersection"
        return "near_miss"

    def _expand(self, a: TrackedObject, b: TrackedObject, ep: _Episode) -> ConflictEvent:
        return ConflictEvent(
            type=ep.kind,
            frame_start=ep.start,
            frame_end=ep.start,
            timestamp_s=ep.start / self.fps,
            duration_s=0.0,
            severity=self._severity(ep),
            severity_label=_severity_label(self._severity(ep)),
            actor_a=ep.actor_a,
            actor_a_id=ep.actor_a_id,
            actor_b=ep.actor_b,
            actor_b_id=ep.actor_b_id,
            min_gap_px=ep.min_gap,
            min_ttc_s=ep.min_ttc,
            max_speed_px_s=ep.max_rel_speed,
            headline="",
            explanation="",
            factors=[],
        )

    def _severity(self, ep: _Episode) -> int:
        base = {
            "near_miss": 2,
            "trajectory_intersection": 3,
            "vehicle_pedestrian": 2,
            "sudden_braking": 2,
        }[ep.kind]
        sev = base
        if ep.kind == "vehicle_pedestrian":
            sev += _PED_SEV_BUMP
        if ep.min_ttc < TTC_HARD:
            sev += 1
        if ep.min_gap < 0.4 * self.gap_base:
            sev += 1
        return min(4, sev)

    def _close_pair(self, key: tuple[int, int], state: _PairState, frame_idx: int) -> None:
        ep = state.episode
        if ep is None:
            return
        ev = ConflictEvent(
            type=ep.kind,
            frame_start=ep.start,
            frame_end=frame_idx,
            timestamp_s=ep.start / self.fps,
            duration_s=(frame_idx - ep.start) / self.fps,
            severity=self._severity(ep),
            severity_label=_severity_label(self._severity(ep)),
            actor_a=ep.actor_a,
            actor_a_id=ep.actor_a_id,
            actor_b=ep.actor_b,
            actor_b_id=ep.actor_b_id,
            min_gap_px=ep.min_gap,
            min_ttc_s=ep.min_ttc,
            max_speed_px_s=ep.max_rel_speed,
            headline=_headline(ev_shim(ep)),
            explanation=_explain(ev_shim(ep), self.gap_base),
            factors=_factors(ep),
        )
        self.events.append(ev)
        state.episode = None
        state.close_count = 0
        state.escape_count = 0

    # -- braking -------------------------------------------------------------

    def _update_braking(
        self, frame_idx: int, tracks: list[TrackedObject], seg_velocity_stats: dict
    ) -> None:
        v_p95 = seg_velocity_stats.get("v_p95_px_s", 40.0)
        for t in tracks:
            if t.cls_name not in VEHICLE_CLASSES:
                continue
            accel_active = t.accel_px_f2 < -BRAKE_DECEL_PER_F2
            state = self._brakes.setdefault(t.track_id, {"accel_count": 0, "episode": None})

            if accel_active:
                state["accel_count"] += 1
            else:
                state["accel_count"] = max(0, state["accel_count"] - 1)

            started = state["episode"] is None and state["accel_count"] >= BRAKE_MIN_FRAMES
            if started and t.speed_px_s > BRAKE_ENTER_SPEED * self.fps:
                state["episode"] = {
                    "start": frame_idx,
                    "min_speed": t.speed_px_s,
                    "peak_decel": t.accel_px_f2,
                    "resume": 0,
                    "class": t.cls_name,
                }
                high_speed_bump = 1 if t.speed_px_s > 0.6 * v_p95 else 0
                state["episode"]["bump"] = high_speed_bump

            ep = state["episode"]
            if ep:
                ep["min_speed"] = min(ep["min_speed"], t.speed_px_s)
                ep["peak_decel"] = min(ep["peak_decel"], t.accel_px_f2)
                ep["end"] = frame_idx
                if accel_active:
                    ep["resume"] = 0
                else:
                    ep["resume"] += 1
                    if ep["resume"] >= BRAKE_RESUME:
                        self._close_brake(t.track_id, state)

    def _close_brake(self, tid: int, state: dict) -> None:
        ep = state.get("episode")
        state["episode"] = None
        state["accel_count"] = 0
        if not ep:
            return
        start = ep["start"]
        end = ep.get("end", start)
        peak_decel = abs(ep["peak_decel"]) * self.fps  # px/s^2
        sev = 2  # MODERATE baseline
        if peak_decel >= BRAKE_HARSH_PX_S2:
            sev += 1  # harsh braking
        if sev > 1 and ep.get("bump", 0) == 1 and peak_decel >= BRAKE_HARSH_PX_S2:
            sev += 1  # harsh braking from an unusually high approach speed
        ev = ConflictEvent(
            type="sudden_braking",
            frame_start=start,
            frame_end=end,
            timestamp_s=start / self.fps,
            duration_s=(end - start) / self.fps,
            severity=min(4, sev),
            severity_label=_severity_label(min(4, sev)),
            actor_a=ep["class"],
            actor_a_id=tid,
            actor_b=None,
            actor_b_id=None,
            min_gap_px=0.0,
            min_ttc_s=1e9,
            max_speed_px_s=ep["min_speed"],
            headline=f"{ep['class'].capitalize()} #{tid} braked sharply",
            explanation=(
                f"{ep['class']} #{tid} decelerated at up to {peak_decel:.0f} px/s² "
                f"while travelling at {ep['min_speed']:.0f} px/s (peak), between frames "
                f"{start}–{end} ({start / self.fps:.1f}s–{end / self.fps:.1f}s)."
            ),
            factors=["sharp deceleration"],
        )
        self.events.append(ev)


# -- helpers -----------------------------------------------------------------

def ev_shim(ep: _Episode):
    return ep


def _predicted(centroid, velocity: Optional[tuple[float, float]], seconds, fps):
    if not centroid or not velocity:
        return None
    return (
        centroid[0] + velocity[0] * seconds * fps,
        centroid[1] + velocity[1] * seconds * fps,
    )


def _severity_label(sev: int) -> str:
    return {1: "LOW", 2: "MODERATE", 3: "HIGH", 4: "CRITICAL"}.get(sev, "LOW")


def _headline(ep: _Episode) -> str:
    if ep.kind == "vehicle_pedestrian":
        return f"Vehicle–pedestrian conflict: {ep.actor_a} #{ep.actor_a_id} / {ep.actor_b} #{ep.actor_b_id}"
    if ep.kind == "trajectory_intersection":
        return f"Paths converge: {ep.actor_a} #{ep.actor_a_id} / {ep.actor_b} #{ep.actor_b_id}"
    if ep.kind == "sudden_braking":
        return f"{ep.actor_a} #{ep.actor_a_id} braked sharply"
    return f"Near miss: {ep.actor_a} #{ep.actor_a_id} / {ep.actor_b} #{ep.actor_b_id}"


def _explain(ep: _Episode, gap_base: float) -> str:
    gap_m = ep.min_gap / gap_base
    ttc = ep.min_ttc if ep.min_ttc < 1e8 else None
    if ep.kind == "vehicle_pedestrian":
        details = [f"the pair closed to {ep.min_gap:.0f}px ({(gap_m):.1f}x the reference gap)"]
        if ttc is not None:
            details.append(f"a predicted collision window of {ttc:.1f}s if neither acted")
        return "Vehicle–pedestrian interaction: " + "; ".join(details) + "."
    if ep.kind == "trajectory_intersection":
        details = ["predicted straight-line paths cross within the look-ahead horizon"]
        if ttc is not None:
            details.append(f"predicted TTC {ttc:.1f}s")
        return f"Paths of {ep.actor_a} #{ep.actor_a_id} and {ep.actor_b} #{ep.actor_b_id}: " + "; ".join(details) + "."
    if ep.kind == "sudden_braking":
        return f"{ep.actor_a} #{ep.actor_a_id} decelerated sharply from speed with limited stopping margin."
    details = [f"clearance fell to {ep.min_gap:.0f}px ({(gap_m):.1f}x the reference gap)"]
    if ttc is not None:
        details.append(f"TTC {ttc:.1f}s")
    return "Two road users converged; " + ", ".join(details) + " — no contact, but the margin is unsafe."


def _factors(ep: _Episode) -> list[str]:
    f = []
    if ep.kind in ("near_miss", "vehicle_pedestrian"):
        if ep.min_gap < 0.4:
            f.append("very tight clearance")
        if ep.min_ttc < TTC_HARD:
            f.append("low reaction margin")
    if ep.kind == "vehicle_pedestrian":
        f.append("pedestrian in traffic stream")
    if ep.max_rel_speed > 40.0:
        f.append("high relative speed")
    return f or ["close interaction"]