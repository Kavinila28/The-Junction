import React from "react";
import { Loader2, Cpu, CheckCircle2, Film } from "lucide-react";

export default function ProcessingModal({
  isOpen,
  status,
  stage,
  progress,
  detail,
  videoName,
  videoSize,
}) {
  if (!isOpen) return null;

  const currentFrame = detail?.current_frame || 0;
  const totalFrames = detail?.total_frames || 1;
  const detections = detail?.detections || 0;
  const events = detail?.events || 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-md rounded-2xl border border-junction-accent/40 bg-junction-panel p-6 shadow-2xl text-center">
        {/* Animated Scanner Ring */}
        <div className="relative mx-auto w-16 h-16 mb-4 flex items-center justify-center">
          <div className="absolute inset-0 rounded-full border-2 border-junction-accent/20 animate-ping" />
          <div className="absolute inset-0 rounded-full border-2 border-dashed border-junction-accent animate-spin" />
          <div className="w-12 h-12 rounded-full bg-junction-accent/10 flex items-center justify-center text-junction-accent">
            <Cpu className="w-6 h-6 animate-pulse" />
          </div>
        </div>

        <h3 className="text-base font-bold text-white uppercase tracking-wider">
          ANALYZING CCTV FOOTAGE
        </h3>
        <p className="text-xs text-junction-muted font-mono mt-1">
          Passing footage through YOLOv8n & Conflict Engine
        </p>

        {/* Video metadata */}
        {videoName && (
          <div className="mt-4 p-3 rounded-lg bg-junction-bg/60 border border-junction-line flex items-center justify-between text-xs font-mono text-left">
            <div className="flex items-center space-x-2 truncate">
              <Film className="w-4 h-4 text-junction-accent flex-shrink-0" />
              <span className="text-slate-200 truncate">{videoName}</span>
            </div>
            {videoSize && (
              <span className="text-junction-muted ml-2 flex-shrink-0">
                {(videoSize / (1024 * 1024)).toFixed(1)} MB
              </span>
            )}
          </div>
        )}

        {/* Progress bar */}
        <div className="my-5 space-y-2 text-left">
          <div className="flex justify-between text-xs font-mono">
            <span className="text-junction-accent font-semibold">
              {status === "uploading"
                ? "UPLOADING STREAM"
                : totalFrames > 1
                ? `Frame ${currentFrame} / ${totalFrames}`
                : "INITIALIZING PIPELINE"}
            </span>
            <span className="text-white font-bold">{progress}%</span>
          </div>

          <div className="w-full bg-junction-bg rounded-full h-2.5 overflow-hidden p-0.5 border border-junction-line">
            <div
              className="bg-gradient-to-r from-junction-accent to-junction-accent2 h-full rounded-full transition-all duration-300"
              style={{ width: `${Math.max(5, progress)}%` }}
            />
          </div>
        </div>

        {/* Live telemetry counters */}
        <div className="grid grid-cols-2 gap-2 text-xs font-mono text-left pt-2 border-t border-junction-line">
          <div className="p-2 rounded bg-junction-bg/40 border border-junction-line/60">
            <span className="text-[10px] text-junction-muted block">PIPELINE STATE</span>
            <span className="text-slate-200 font-bold uppercase">{stage || status}</span>
          </div>
          <div className="p-2 rounded bg-junction-bg/40 border border-junction-line/60">
            <span className="text-[10px] text-junction-muted block">CONFLICTS FLAGGED</span>
            <span className="text-junction-warning font-bold">{events} events</span>
          </div>
        </div>

        <p className="mt-4 text-[10px] text-junction-muted font-mono">
          Local CV execution • Real-time ByteTrack tracking
        </p>
      </div>
    </div>
  );
}
