"""Track continuity stabilisation.

Pre-built trackers (ByteTrack) occasionally split one object into two
track IDs or drop an ID for a few frames (occlusion, flicker). This
module re-links such fragments so that analysis and annotation use a
single stable identity per physical object.

It is *not* a replacement for the Kalman/IOU tracker — it is a
disambiguation layer on top of it: ByteTrack assigns raw IDs, this
layer maps raw IDs -> stable IDs and reuses a stable ID when an
appearing raw ID clearly continues a briefly-missed object.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.detector import Detection

_LOOKBACK_GAP = 5  # max absent frames before a fragment is forgotten
_RELINK_IOU_RATIO = 0.55  # min IoU for an appearing box to claim a stale fragment
_MAX_STALE = 300


@dataclass
class TrackContinuity:
    """Map unstable tracker IDs to continuous, stable object IDs."""

    _id_map: dict[int, int] = field(default_factory=dict)
    _last_box: dict[int, tuple[float, float, float, float]] = field(default_factory=dict)
    _stale: dict[int, tuple[int, int, tuple[float, float, float, float]]] = field(
        default_factory=dict
    )
    _next_id: int = field(default=1)

    @staticmethod
    def _iou(a, b) -> float:
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        ix1, iy1 = max(ax1, bx1), max(ay1, by1)
        ix2, iy2 = min(ax2, bx2), min(ay2, by2)
        inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
        if inter <= 0:
            return 0.0
        area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
        area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
        return inter / (area_a + area_b - inter + 1e-9)

    def apply(self, frame_idx: int, detections: list[Detection]) -> list[Detection]:
        seen_raw = {int(d.track_id) for d in detections if d.track_id is not None}
        bbox_by_raw = {
            int(d.track_id): d.box for d in detections if d.track_id is not None
        }

        self._prune_stale(frame_idx)

        # 1) freshly-appeared raw IDs
        appeared = [rid for rid in seen_raw if rid not in self._id_map]
        claimed: set[int] = set()
        for raw in appeared:
            box = bbox_by_raw[raw]
            if raw in self._stale:
                # Same tracker ID reappearing -> direct continuation.
                stable, _frame, _old = self._stale.pop(raw)
                self._id_map[raw] = stable
                claimed.add(stable)
            else:
                # Try to claim a stale fragment of another raw ID (IoU close).
                best_stable, best_score = None, _RELINK_IOU_RATIO
                for stale_raw, (stable, _f, last_box) in self._stale.items():
                    if stable in claimed:
                        continue
                    score = self._iou(last_box, box)
                    if score > best_score:
                        best_stable, best_score = stable, score
                if best_stable is not None:
                    for stale_raw in [
                        k for k, (s, _f, _b) in self._stale.items() if s == best_stable
                    ]:
                        del self._stale[stale_raw]
                    self._id_map[raw] = best_stable
                    claimed.add(best_stable)
                else:
                    self._id_map[raw] = self._next_id
                    self._next_id += 1

        # 2) tracks that disappeared this frame become stale fragments
        for raw in list(self._id_map):
            if raw not in seen_raw:
                stable = self._id_map.pop(raw)
                last_box = self._last_box.get(raw)
                if last_box is not None:
                    self._stale[raw] = (stable, frame_idx, last_box)

        # 3) rewrite raw ids to stable ids
        for det in detections:
            if det.track_id is not None:
                raw = int(det.track_id)
                det.track_id = self._id_map.get(raw, raw)
                self._last_box[raw] = det.box

        return detections

    def _prune_stale(self, frame_idx: int) -> None:
        expired = [
            raw
            for raw, (_s, f, _b) in self._stale.items()
            if frame_idx - f > _LOOKBACK_GAP
        ]
        for raw in expired:
            del self._stale[raw]
        if len(self._stale) > _MAX_STALE:
            overflow = len(self._stale) - _MAX_STALE
            for raw in list(self._stale)[:overflow]:
                del self._stale[raw]