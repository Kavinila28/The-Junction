import React, { useState, useEffect, useRef } from "react";
import {
  Upload,
  Play,
  Sliders,
  ShieldAlert,
  Film,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import HealthBadge from "./components/HealthBadge.jsx";
import PipelineStrip from "./components/PipelineStrip.jsx";
import KpiCards from "./components/KpiCards.jsx";
import VideoPlayer from "./components/VideoPlayer.jsx";
import ConflictTimeline from "./components/ConflictTimeline.jsx";
import ConflictDistribution from "./components/ConflictDistribution.jsx";
import RiskFactors from "./components/RiskFactors.jsx";
import RecommendationCard from "./components/RecommendationCard.jsx";
import EventTable from "./components/EventTable.jsx";
import InterventionSimulator from "./components/InterventionSimulator.jsx";
import UploadModal from "./components/UploadModal.jsx";
import ProcessingModal from "./components/ProcessingModal.jsx";
import AnalysisFailedPanel from "./components/AnalysisFailedPanel.jsx";
import {
  getAnalysis,
  listAnalyses,
  startDemoAnalysis,
  uploadVideo,
} from "./api/client";

export default function App() {
  const [activeAnalysis, setActiveAnalysis] = useState(null);
  const [status, setStatus] = useState("idle"); // idle, uploading, queued, running, completed, failed
  const [stage, setStage] = useState("idle");
  const [progress, setProgress] = useState(0);
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState(null);

  const [activeTab, setActiveTab] = useState("dashboard"); // dashboard, simulator
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(null);
  const [seekTime, setSeekTime] = useState(null);

  const pollingTimerRef = useRef(null);

  // Load existing analysis on mount if available
  useEffect(() => {
    const loadRecent = async () => {
      try {
        const res = await listAnalyses();
        if (res.analyses && res.analyses.length > 0) {
          const completed = res.analyses.find((a) => a.status === "completed");
          const targetId = completed ? completed.id : res.analyses[0].id;
          const fullData = await getAnalysis(targetId);
          setActiveAnalysis(fullData);
          setStatus(fullData.status);
          setStage(fullData.stage || fullData.status);
          setProgress(fullData.progress || 100);
          setDetail(fullData.detail);

          if (fullData.status === "running" || fullData.status === "queued") {
            pollAnalysis(targetId);
          }
        }
      } catch (err) {
        console.warn("Could not fetch recent analyses:", err);
      }
    };
    loadRecent();

    return () => {
      if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
    };
  }, []);

  const pollAnalysis = (analysisId) => {
    if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);

    pollingTimerRef.current = setInterval(async () => {
      try {
        const data = await getAnalysis(analysisId);
        setActiveAnalysis(data);
        setStatus(data.status);
        setStage(data.stage || data.status);
        setProgress(data.progress || 0);
        setDetail(data.detail);

        if (data.status === "completed") {
          clearInterval(pollingTimerRef.current);
          setStatus("completed");
          setStage("completed");
          setProgress(100);
        } else if (data.status === "failed") {
          clearInterval(pollingTimerRef.current);
          setStatus("failed");
          setStage("failed");
          setError(data.detail || "Video analysis encountered an error.");
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 1000);
  };

  // Run Demo Analysis Workflow
  const handleRunDemo = async () => {
    setError(null);
    setStatus("queued");
    setStage("queued");
    setProgress(0);
    setDetail({ current_frame: 0, total_frames: 647, detections: 0, events: 0 });
    setUploadingFile({ name: "demo_traffic_sample.mp4", size: 10 * 1024 * 1024 });

    try {
      const res = await startDemoAnalysis();
      pollAnalysis(res.analysis_id);
    } catch (err) {
      setStatus("failed");
      setError(err.message || "Failed to start demo analysis.");
    }
  };

  // Run Upload Video Workflow
  const handleUploadFile = async (file) => {
    setError(null);
    setStatus("uploading");
    setStage("uploading");
    setProgress(10);
    setUploadingFile({ name: file.name, size: file.size });

    try {
      const res = await uploadVideo(file);
      setStatus("queued");
      setStage("queued");
      setProgress(15);
      pollAnalysis(res.analysis_id);
    } catch (err) {
      setStatus("failed");
      setError(err.message || "Video upload failed.");
    }
  };

  const isProcessing = status === "uploading" || status === "queued" || status === "running";
  const hasAnalysis = Boolean(activeAnalysis && activeAnalysis.status === "completed");

  return (
    <div className="min-h-screen bg-junction-bg text-slate-100 font-sans selection:bg-junction-accent selection:text-slate-950">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top,rgba(56,189,248,0.08),transparent_60%)]" />

      {/* Top Header */}
      <header className="sticky top-0 z-40 border-b border-junction-line bg-junction-bg/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-3.5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-junction-accent to-junction-accent2 text-sm font-extrabold text-white shadow-lg shadow-sky-500/20">
              <ShieldAlert className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-lg font-extrabold tracking-tight text-white">
                  THE&nbsp;JUNCTION
                </h1>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-junction-accent/10 text-junction-accent border border-junction-accent/30">
                  CV CONFLICT INTELLIGENCE
                </span>
              </div>
              <p className="text-[11px] font-medium text-junction-muted">
                Predicting danger before it becomes an accident.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <HealthBadge />
          </div>
        </div>

        {/* Navigation bar */}
        <nav className="mx-auto max-w-7xl px-6">
          <div className="flex gap-6 text-sm font-semibold border-t border-junction-line/40 pt-1">
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`pb-2.5 transition-all ${
                activeTab === "dashboard"
                  ? "border-b-2 border-junction-accent text-slate-100 font-bold"
                  : "border-b-2 border-transparent text-junction-muted hover:text-slate-300"
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab("simulator")}
              className={`pb-2.5 transition-all flex items-center space-x-1.5 ${
                activeTab === "simulator"
                  ? "border-b-2 border-junction-accent text-slate-100 font-bold"
                  : "border-b-2 border-transparent text-junction-muted hover:text-slate-300"
              }`}
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>Intervention Simulator</span>
            </button>
          </div>
        </nav>
      </header>

      {/* Main Content Area */}
      <main className="relative mx-auto max-w-7xl px-6 py-6 pb-16">
        {/* Action Header Banner */}
        <div className="mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl border border-junction-line bg-junction-panel/80 glass-panel">
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-bold text-white">
                Road Conflict Telemetry & Prevention
              </h2>
              {activeAnalysis?.source === "demo" && (
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 uppercase">
                  DEMO ANALYSIS
                </span>
              )}
            </div>
            <p className="mt-1 text-xs text-junction-muted max-w-xl">
              Upload CCTV footage or run the bundled intersection demo to detect near-misses, vehicle-pedestrian crossing exposures, and sudden braking in image space.
            </p>
          </div>

          {/* TWO OBVIOUS USER ACTIONS */}
          <div className="flex flex-wrap items-center gap-3 flex-shrink-0">
            {/* Secondary: RUN DEMO ANALYSIS */}
            <button
              onClick={handleRunDemo}
              disabled={isProcessing}
              className="flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold bg-junction-panel2 hover:bg-slate-700 text-slate-100 border border-junction-line shadow-sm transition-all disabled:opacity-50"
            >
              <Play className="w-4 h-4 text-junction-accent fill-current" />
              <span>Run Demo Analysis</span>
            </button>

            {/* Primary: UPLOAD CCTV FOOTAGE */}
            <button
              onClick={() => setIsUploadModalOpen(true)}
              disabled={isProcessing}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-junction-accent hover:bg-sky-400 text-junction-bg shadow-lg shadow-sky-500/20 transition-all disabled:opacity-50"
            >
              <Upload className="w-4 h-4" />
              <span>Upload CCTV Footage</span>
            </button>
          </div>
        </div>

        {/* Dynamic 5-Step Pipeline Indicator */}
        <PipelineStrip
          analysis={activeAnalysis}
          status={status}
          stage={stage}
          progress={progress}
          detail={detail}
        />

        {/* Error panel if failed */}
        {error && (
          <AnalysisFailedPanel
            error={error}
            onRetry={handleRunDemo}
          />
        )}

        {/* Tab 1: Dashboard View */}
        {activeTab === "dashboard" && (
          <div className="space-y-6">
            {/* 4 KPI Metric Cards */}
            <KpiCards
              summary={activeAnalysis?.summary}
              events={activeAnalysis?.events || []}
            />

            {/* Main Video & Analytics Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Video Player + Timeline */}
              <div className="lg:col-span-8 space-y-6">
                <VideoPlayer
                  analysisId={hasAnalysis ? activeAnalysis.id : null}
                  filename={activeAnalysis?.filename}
                  durationS={activeAnalysis?.duration_s || activeAnalysis?.summary?.duration_s || 30}
                  fps={activeAnalysis?.fps || activeAnalysis?.summary?.fps || 25}
                  events={activeAnalysis?.events || []}
                  seekTime={seekTime}
                  onSelectEvent={(ev) => setSeekTime(ev.timestamp_s)}
                />

                <ConflictTimeline
                  events={activeAnalysis?.events || []}
                  durationS={activeAnalysis?.duration_s || activeAnalysis?.summary?.duration_s || 30}
                  onSelectTimestamp={(t) => setSeekTime(t)}
                />
              </div>

              {/* Right Column: Breakdown Charts & Recommendations */}
              <div className="lg:col-span-4 space-y-6">
                <ConflictDistribution
                  counts={activeAnalysis?.summary?.counts}
                  events={activeAnalysis?.events || []}
                />

                <RiskFactors factors={activeAnalysis?.summary?.factors || []} />

                <RecommendationCard
                  recommendations={activeAnalysis?.summary?.recommendations || []}
                  onOpenSimulator={() => setActiveTab("simulator")}
                />
              </div>
            </div>

            {/* Full Forensic Event Table at Bottom */}
            <EventTable
              events={activeAnalysis?.events || []}
              onSeek={(t) => setSeekTime(t)}
            />
          </div>
        )}

        {/* Tab 2: Intervention Simulator View */}
        {activeTab === "simulator" && (
          <div className="space-y-6">
            <InterventionSimulator
              analysisId={activeAnalysis?.id}
              baselineScore={activeAnalysis?.summary?.risk_score || 61}
              baselineCategory={activeAnalysis?.summary?.risk_category || "HIGH"}
              onClose={() => setActiveTab("dashboard")}
            />

            {/* Event Table Context */}
            <EventTable
              events={activeAnalysis?.events || []}
              onSeek={(t) => {
                setSeekTime(t);
                setActiveTab("dashboard");
              }}
            />
          </div>
        )}

        {/* Upload Modal */}
        <UploadModal
          isOpen={isUploadModalOpen}
          onClose={() => setIsUploadModalOpen(false)}
          onUploadFile={handleUploadFile}
          isUploading={status === "uploading"}
        />

        {/* Live Processing Overlay during Video Analysis */}
        <ProcessingModal
          isOpen={isProcessing}
          status={status}
          stage={stage}
          progress={progress}
          detail={detail}
          videoName={uploadingFile?.name}
          videoSize={uploadingFile?.size}
        />
      </main>

      {/* Footer */}
      <footer className="border-t border-junction-line/80 bg-junction-bg/90 py-5 text-center text-xs text-junction-muted font-mono">
        THE JUNCTION — Road Conflict Intelligence · FastAPI · Ultralytics YOLOv8n · ByteTrack · OpenCV · SQLite · React
      </footer>
    </div>
  );
}