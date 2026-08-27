import React, { useRef, useState, useEffect } from "react";
import {
  Play,
  Pause,
  RotateCcw,
  Maximize2,
  Minimize2,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  Film,
  AlertTriangle,
} from "lucide-react";
import { getVideoUrl } from "../api/client";

export default function VideoPlayer({
  analysisId,
  filename,
  durationS = 30,
  fps = 25,
  events = [],
  seekTime,
  onSelectEvent,
}) {
  const videoRef = useRef(null);
  const containerRef = useRef(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [videoDuration, setVideoDuration] = useState(durationS || 30);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [videoError, setVideoError] = useState(null);

  const videoSrc = analysisId ? getVideoUrl(analysisId) : null;

  // Reload when analysisId changes
  useEffect(() => {
    setVideoError(null);
    setCurrentTime(0);
    setCurrentFrame(0);
    setIsPlaying(false);
    if (videoRef.current) {
      videoRef.current.currentTime = 0;
      videoRef.current.load();
    }
  }, [analysisId]);

  // React to seekTime changes
  useEffect(() => {
    if (seekTime !== null && seekTime !== undefined && videoRef.current) {
      videoRef.current.currentTime = seekTime;
      setCurrentTime(seekTime);
      setCurrentFrame(Math.round(seekTime * fps));
    }
  }, [seekTime, fps]);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play().then(() => setIsPlaying(true)).catch((err) => {
        console.error("Playback error:", err);
      });
    }
  };

  const handleTimeUpdate = () => {
    if (!videoRef.current) return;
    const t = videoRef.current.currentTime;
    setCurrentTime(t);
    setCurrentFrame(Math.round(t * fps));
  };

  const handleLoadedMetadata = () => {
    if (!videoRef.current) return;
    setVideoDuration(videoRef.current.duration || durationS || 30);
  };

  const handleSeek = (e) => {
    if (!videoRef.current) return;
    const t = parseFloat(e.target.value);
    videoRef.current.currentTime = t;
    setCurrentTime(t);
    setCurrentFrame(Math.round(t * fps));
  };

  const stepFrame = (deltaFrames) => {
    if (!videoRef.current) return;
    videoRef.current.pause();
    setIsPlaying(false);
    const newTime = Math.max(
      0,
      Math.min(videoDuration, currentTime + deltaFrames / fps)
    );
    videoRef.current.currentTime = newTime;
    setCurrentTime(newTime);
    setCurrentFrame(Math.round(newTime * fps));
  };

  const changeSpeed = (speed) => {
    if (!videoRef.current) return;
    videoRef.current.playbackRate = speed;
    setPlaybackSpeed(speed);
  };

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().catch(console.error);
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(console.error);
      setIsFullscreen(false);
    }
  };

  // Find active conflict at current time
  const activeConflict = events.find(
    (ev) =>
      Math.abs(ev.timestamp_s - currentTime) <= Math.max(0.8, (ev.duration_s || 0.5) / 2)
  );

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins.toString().padStart(2, "0")}:${secs.padStart(4, "0")}`;
  };

  if (!analysisId) {
    return (
      <div className="panel flex flex-col gap-3">
        <div className="panel-title">Annotated CCTV feed</div>
        <div className="flex aspect-video w-full flex-col items-center justify-center rounded-lg border border-dashed border-junction-line bg-junction-bg/40 p-6 text-center">
          <Film className="w-10 h-10 text-junction-muted mb-2 opacity-50" />
          <div className="text-sm font-semibold text-slate-300">
            Awaiting analysis
          </div>
          <div className="max-w-sm text-xs text-junction-muted mt-1">
            Click "Run Demo Analysis" or upload a CCTV clip to generate and view the real annotated YOLO video stream.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="panel flex flex-col overflow-hidden p-0 border border-junction-line bg-[#070A10]"
    >
      {/* Video Top Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-junction-panel border-b border-junction-line text-xs font-mono text-slate-300">
        <div className="flex items-center space-x-2.5">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
          <span className="font-bold text-white uppercase tracking-wider">
            CCTV CAM TELEMETRY
          </span>
          <span className="text-junction-muted">|</span>
          <span className="text-junction-accent truncate max-w-xs">
            {filename || "annotated_feed.mp4"}
          </span>
        </div>
        <div className="flex items-center space-x-2 text-[11px]">
          <span className="px-2 py-0.5 rounded bg-junction-panel2 border border-junction-line text-slate-300">
            FRAME #{currentFrame}
          </span>
        </div>
      </div>

      {/* Video Frame */}
      <div className="relative aspect-video w-full bg-black flex items-center justify-center overflow-hidden">
        <video
          key={analysisId}
          ref={videoRef}
          src={videoSrc}
          className="w-full h-full object-contain"
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onEnded={() => setIsPlaying(false)}
          onError={(e) => {
            console.error("Video element error:", e);
            setVideoError("Unable to decode video stream in browser.");
          }}
          playsInline
          preload="auto"
        />

        {videoError && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/80 p-4 text-center">
            <div className="text-red-400 text-xs font-mono">
              <AlertTriangle className="w-6 h-6 mx-auto mb-1" />
              <span>{videoError}</span>
            </div>
          </div>
        )}

        {/* Live conflict overlay flag if in conflict window */}
        {activeConflict && (
          <div className="absolute top-4 right-4 z-20 max-w-sm rounded-xl border border-red-500/50 bg-junction-bg/95 backdrop-blur-md p-3 shadow-lg shadow-red-500/20 animate-pulse">
            <div className="flex items-center space-x-2 text-red-400 font-mono text-xs font-bold uppercase">
              <ShieldAlert className="w-4 h-4" />
              <span>{activeConflict.severity_label} CONFLICT</span>
            </div>
            <p className="mt-1 text-xs text-slate-200 font-medium">
              {activeConflict.headline || activeConflict.explanation}
            </p>
            {activeConflict.min_ttc_s && (
              <div className="mt-1.5 flex items-center space-x-3 text-[10px] font-mono text-junction-muted">
                <span>TTC: <strong className="text-red-400">{activeConflict.min_ttc_s}s</strong></span>
                <span>Gap: <strong className="text-amber-400">{activeConflict.min_gap_px}px</strong></span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Video Controls & Timeline Bar */}
      <div className="px-4 py-3 bg-junction-panel border-t border-junction-line flex flex-col space-y-2">
        {/* Scrubber Progress Bar with Conflict Markers */}
        <div className="relative w-full flex items-center">
          <input
            type="range"
            min="0"
            max={videoDuration || 1}
            step="0.01"
            value={currentTime}
            onChange={handleSeek}
            className="w-full h-1.5 bg-junction-bg rounded-lg appearance-none cursor-pointer accent-junction-accent focus:outline-none"
          />

          {/* Conflict markers on timeline */}
          {videoDuration > 0 &&
            events.map((ev, idx) => {
              const leftPct = Math.min(
                100,
                Math.max(0, (ev.timestamp_s / videoDuration) * 100)
              );
              const isCrit =
                ev.severity_label === "CRITICAL" || ev.severity_label === "HIGH";
              return (
                <button
                  key={idx}
                  onClick={() => {
                    if (videoRef.current) {
                      videoRef.current.currentTime = ev.timestamp_s;
                      setCurrentTime(ev.timestamp_s);
                    }
                    if (onSelectEvent) onSelectEvent(ev);
                  }}
                  title={`${ev.severity_label} ${ev.type_label} @ ${ev.timestamp_s}s`}
                  style={{ left: `${leftPct}%` }}
                  className={`absolute w-2 h-3.5 -top-1 -translate-x-1/2 rounded-sm cursor-pointer transition-transform hover:scale-150 ${
                    isCrit ? "bg-red-500 shadow-md shadow-red-500/50" : "bg-amber-400"
                  }`}
                />
              );
            })}
        </div>

        {/* Buttons and Time Display */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              onClick={togglePlay}
              className="p-1.5 rounded-lg bg-junction-accent/20 hover:bg-junction-accent/30 text-junction-accent border border-junction-accent/40 transition-colors"
              title={isPlaying ? "Pause" : "Play"}
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-current" />}
            </button>

            <button
              onClick={() => stepFrame(-1)}
              className="p-1.5 rounded-lg bg-junction-panel2 hover:bg-junction-panel text-slate-300 border border-junction-line transition-colors"
              title="Step Back 1 Frame"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => stepFrame(1)}
              className="p-1.5 rounded-lg bg-junction-panel2 hover:bg-junction-panel text-slate-300 border border-junction-line transition-colors"
              title="Step Forward 1 Frame"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>

            <div className="font-mono text-xs text-slate-300 ml-2">
              <span className="text-white font-semibold">{formatTime(currentTime)}</span>
              <span className="text-junction-muted"> / </span>
              <span className="text-junction-muted">{formatTime(videoDuration)}</span>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* Speed Options */}
            <div className="flex items-center rounded-lg bg-junction-bg border border-junction-line p-0.5 text-xs font-mono">
              {[0.5, 1.0, 2.0].map((spd) => (
                <button
                  key={spd}
                  onClick={() => changeSpeed(spd)}
                  className={`px-2 py-0.5 rounded text-[10px] transition-colors ${
                    playbackSpeed === spd
                      ? "bg-junction-accent/20 text-junction-accent font-bold"
                      : "text-junction-muted hover:text-slate-200"
                  }`}
                >
                  {spd}x
                </button>
              ))}
            </div>

            <button
              onClick={toggleFullscreen}
              className="p-1.5 rounded-lg bg-junction-panel2 hover:bg-junction-panel text-slate-300 border border-junction-line transition-colors"
              title="Fullscreen"
            >
              {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
