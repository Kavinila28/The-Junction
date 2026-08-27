"""Video reading and writing utilities.

Writing targets standard browser-playable H.264 (AVC1 / yuv420p).
PyAV / libx264 is the primary encoder, with imageio-ffmpeg as fallback.
"""

from __future__ import annotations

from typing import Optional
from pathlib import Path

import cv2
import numpy as np

_AVAIL = None


def writer_available() -> str:
    global _AVAIL
    if _AVAIL is None:
        try:
            import av  # noqa: F401
            _AVAIL = "av"
        except Exception:
            try:
                import imageio_ffmpeg  # noqa: F401
                _AVAIL = "imageio"
            except Exception:
                _AVAIL = "cv2"
    return _AVAIL


class VideoWriter:
    """Stateful frame writer that muxes browser-compatible H.264 MP4."""

    def __init__(self, path, width: int, height: int, fps: float) -> None:
        self.path = Path(path)
        self.width = width
        self.height = height
        self.fps = float(fps)
        self.backend = writer_available()
        self._av_container = None
        self._av_stream = None
        self._cv_writer: Optional[cv2.VideoWriter] = None

        if self.backend == "av":
            import av
            from fractions import Fraction

            self._av_container = av.open(str(path), mode="w")
            # libx264 produces standard AVC1 H.264 video playable across all modern browsers
            self._av_stream = self._av_container.add_stream("libx264", rate=Fraction(int(round(self.fps * 1000)), 1000))
            self._av_stream.width = width
            self._av_stream.height = height
            self._av_stream.pix_fmt = "yuv420p"
            self._av_stream.options = {"preset": "fast", "crf": "23"}
        else:
            fourcc = cv2.VideoWriter_fourcc(*"avc1")
            self._cv_writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))
            if not self._cv_writer.isOpened():
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                self._cv_writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))
                self.backend = "cv2-mp4v"
            else:
                self.backend = "cv2-avc1"

    def write(self, frame_bgr: np.ndarray) -> None:
        if self._av_container is not None and self._av_stream is not None:
            import av

            raw = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            video_frame = av.VideoFrame.from_ndarray(raw, format="rgb24")
            for packet in self._av_stream.encode(video_frame):
                self._av_container.mux(packet)
        elif self._cv_writer is not None:
            self._cv_writer.write(frame_bgr)

    def close(self) -> None:
        if self._av_container is not None and self._av_stream is not None:
            for packet in self._av_stream.encode(None):
                self._av_container.mux(packet)
            self._av_container.close()
            self._av_container = None
        if self._cv_writer is not None:
            self._cv_writer.release()
            self._cv_writer = None


def read_video_props(path):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"cannot open video: {path}")
    props = {
        "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "fps": float(cap.get(cv2.CAP_PROP_FPS)) or 25.0,
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    }
    cap.release()
    return props