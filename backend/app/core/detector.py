"""Pretrained YOLO detector wrapper.

Uses a stock Ultralytics YOLOv8n model pretrained on COCO. Nothing is
trained in this project; the network runs inference only. The wrapper
holds the model in a process-wide singleton so heavy weights are loaded
once and shared by every analysis request.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Optional

from ultralytics import YOLO
from ultralytics.engine.results import Results

from app.config import settings

_LOCK = threading.Lock()
_INSTANCE: Optional["YOLODetector"] = None

# Class index -> human label (COCO, restricted to junction-relevant classes).
CLASS_NAMES = {
    0: "pedestrian",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


@dataclass
class Detection:
    """A single detected object in a frame."""

    track_id: Optional[int]
    cls: int
    cls_name: str
    box: tuple[float, float, float, float]  # x1, y1, x2, y2
    conf: float


class YOLODetector:
    """Thin wrapper around an Ultralytics YOLO model."""

    def __init__(self) -> None:
        path = str(settings.model_path)
        if not settings.model_path.exists():
            # Ultralytics downloads the pretrained weights to the model dir.
            self._model = YOLO(settings.model_name)
        else:
            self._model = YOLO(path)
        self._model.to("cpu")
        self._warm()

    def _warm(self) -> None:
        """Run one dummy inference so first real frame isn't slow."""
        import numpy as np

        dummy = np.zeros((settings.imgsz, settings.imgsz, 3), dtype="uint8")
        self._model.predict(
            dummy, imgsz=settings.imgsz, verbose=False, device="cpu"
        )

    def track_stream(
        self, source: str, half: bool = False, vid_stride: Optional[int] = None
    ):
        """Yield an Ultralytics Results stream with ByteTrack tracking enabled.

        The tracker is stateful across yielded frames, producing stable
        track IDs in ``result.boxes.id``.
        """
        stride = vid_stride if vid_stride is not None else settings.frame_stride
        return self._model.track(
            source=source,
            stream=True,
            imgsz=settings.imgsz,
            conf=settings.conf_threshold,
            iou=settings.iou_threshold,
            classes=settings.junction_classes,
            tracker="bytetrack.yaml",
            vid_stride=stride,
            persist=True,
            verbose=False,
            device="cpu",
        )

    @staticmethod
    def detections_from_result(result: Results) -> list[Detection]:
        """Convert an Ultralytics Results into plain Detection dataclasses."""
        out: list[Detection] = []
        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            return out
        cls = boxes.cls.cpu().tolist()
        conf = boxes.conf.cpu().tolist()
        xyxy = boxes.xyxy.cpu().tolist()
        ids = boxes.id.cpu().tolist() if boxes.id is not None else [None] * len(boxes)
        for c, cf, box, tid in zip(cls, conf, xyxy, ids):
            c_int = int(c)
            out.append(
                Detection(
                    track_id=int(tid) if tid is not None else None,
                    cls=c_int,
                    cls_name=CLASS_NAMES.get(c_int, str(c_int)),
                    box=tuple(float(v) for v in box),
                    conf=float(cf),
                )
            )
        return out


def get_detector() -> YOLODetector:
    """Return the process-wide detector instance (loaded once)."""
    global _INSTANCE
    with _LOCK:
        if _INSTANCE is None:
            _INSTANCE = YOLODetector()
        return _INSTANCE