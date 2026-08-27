import React from "react";
import { CheckCircle2, Circle, Loader2, AlertCircle } from "lucide-react";

export default function PipelineStrip({ analysis, status, stage, progress, detail }) {
  const isRunning = status === "running" || status === "queued" || status === "uploading";
  const isCompleted = status === "completed";
  const isFailed = status === "failed";

  const getStepState = (stepIndex) => {
    if (isCompleted) return "completed";
    if (isFailed) return "failed";
    if (!isRunning) return "pending";

    // Dynamic stage progression based on backend progress (0-100%)
    if (progress < 15) {
      return stepIndex === 0 ? "active" : "pending";
    } else if (progress < 45) {
      if (stepIndex < 1) return "completed";
      if (stepIndex === 1) return "active";
      return "pending";
    } else if (progress < 70) {
      if (stepIndex < 2) return "completed";
      if (stepIndex === 2) return "active";
      return "pending";
    } else if (progress < 90) {
      if (stepIndex < 3) return "completed";
      if (stepIndex === 3) return "active";
      return "pending";
    } else {
      if (stepIndex < 4) return "completed";
      if (stepIndex === 4) return "active";
      return "pending";
    }
  };

  const steps = [
    { label: "Upload CCTV Footage", desc: "Ingesting video stream" },
    { label: "YOLO Detection", desc: "YOLOv8n road user inference" },
    { label: "Multi-Object Tracking", desc: "ByteTrack identity continuity" },
    { label: "Conflict Analysis", desc: "Near-miss & braking physics" },
    { label: "Risk Scoring", desc: "Deterministic 0–100 index" },
  ];

  return (
    <div className="panel mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-junction-line pb-3">
        <div className="panel-title">Analysis Pipeline Progress</div>
        {isRunning && (
          <div className="flex items-center space-x-2 text-xs font-mono text-junction-accent">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>
              {detail?.current_frame !== undefined && detail?.total_frames
                ? `Frame ${detail.current_frame} / ${detail.total_frames} (${progress}%)`
                : `Processing (${progress}%)`}
            </span>
            {detail?.events !== undefined && (
              <span className="text-junction-muted">
                • {detail.events} conflict(s) flagged
              </span>
            )}
          </div>
        )}
        {isCompleted && (
          <span className="inline-flex items-center space-x-1.5 text-xs font-mono text-junction-success font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Analysis Complete (100%)</span>
          </span>
        )}
      </div>

      <ol className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {steps.map((step, i) => {
          const state = getStepState(i);
          const isActive = state === "active";
          const isDone = state === "completed";
          const isFail = state === "failed";

          return (
            <li
              key={step.label}
              className={`flex items-start gap-2.5 rounded-lg border p-3 transition-all ${
                isActive
                  ? "border-junction-accent/50 bg-junction-accent/10 shadow-[0_0_15px_rgba(56,189,248,0.2)]"
                  : isDone
                  ? "border-emerald-500/30 bg-emerald-500/10"
                  : isFail
                  ? "border-red-500/30 bg-red-500/10"
                  : "border-junction-line bg-junction-panel2/60"
              }`}
            >
              <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold">
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : isActive ? (
                  <Loader2 className="w-4 h-4 text-junction-accent animate-spin" />
                ) : isFail ? (
                  <AlertCircle className="w-4 h-4 text-red-400" />
                ) : (
                  <span className="text-junction-muted">{i + 1}</span>
                )}
              </span>
              <div className="flex-1 min-w-0">
                <div
                  className={`text-xs font-semibold truncate ${
                    isActive
                      ? "text-junction-accent font-bold"
                      : isDone
                      ? "text-slate-100"
                      : "text-junction-muted"
                  }`}
                >
                  {step.label}
                </div>
                <div className="text-[10px] text-junction-muted/80 truncate">
                  {step.desc}
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
