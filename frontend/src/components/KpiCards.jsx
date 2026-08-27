import React from "react";
import { ShieldAlert, AlertTriangle, UserX, Gauge } from "lucide-react";

export default function KpiCards({ summary, events = [] }) {
  const hasData = Boolean(summary);

  const totalConflicts = hasData
    ? (summary.counts ? Object.values(summary.counts).reduce((a, b) => a + b, 0) : events.length)
    : "—";

  const highRiskCount = hasData
    ? (summary.severity_counts?.CRITICAL || 0) + (summary.severity_counts?.HIGH || 0)
    : "—";

  const pedConflicts = hasData
    ? (summary.counts?.vehicle_pedestrian || 0)
    : "—";

  const riskScore = hasData ? summary.risk_score : "—";
  const riskCategory = hasData ? summary.risk_category : "Awaiting analysis";

  const getCategoryStyles = (cat) => {
    switch (cat) {
      case "CRITICAL":
        return {
          bg: "bg-red-500/10",
          border: "border-red-500/30",
          text: "text-red-400",
          badge: "bg-red-500/20 text-red-300 border-red-500/40",
          bar: "bg-red-500",
        };
      case "HIGH":
        return {
          bg: "bg-orange-500/10",
          border: "border-orange-500/30",
          text: "text-orange-400",
          badge: "bg-orange-500/20 text-orange-300 border-orange-500/40",
          bar: "bg-orange-500",
        };
      case "MODERATE":
        return {
          bg: "bg-amber-500/10",
          border: "border-amber-500/30",
          text: "text-amber-400",
          badge: "bg-amber-500/20 text-amber-300 border-amber-500/40",
          bar: "bg-amber-500",
        };
      case "LOW":
        return {
          bg: "bg-emerald-500/10",
          border: "border-emerald-500/30",
          text: "text-emerald-400",
          badge: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
          bar: "bg-emerald-500",
        };
      default:
        return {
          bg: "bg-junction-panel2/60",
          border: "border-junction-line",
          text: "text-junction-muted",
          badge: "bg-junction-line text-junction-muted",
          bar: "bg-junction-muted",
        };
    }
  };

  const style = getCategoryStyles(riskCategory);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* 1. Junction Risk Score */}
      <div className={`kpi-card ${hasData ? `${style.bg} ${style.border}` : ""}`}>
        <div className="flex items-center justify-between">
          <span className="panel-title">Junction Risk Score</span>
          <Gauge className={`w-4 h-4 ${style.text}`} />
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="stat-value font-mono">
            {hasData ? `${riskScore}` : "—"}
          </span>
          {hasData && <span className="text-xs text-junction-muted font-mono">/ 100</span>}
          {hasData && (
            <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${style.badge}`}>
              {riskCategory}
            </span>
          )}
        </div>
        {hasData ? (
          <div className="w-full bg-junction-bg rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${style.bar}`}
              style={{ width: `${Math.min(100, Math.max(5, riskScore))}%` }}
            />
          </div>
        ) : (
          <div className="text-xs text-junction-muted">Waiting for analysis</div>
        )}
      </div>

      {/* 2. Total Conflicts */}
      <div className="kpi-card">
        <div className="flex items-center justify-between">
          <span className="panel-title">Conflicts Detected</span>
          <ShieldAlert className="w-4 h-4 text-junction-accent" />
        </div>
        <div className="stat-value font-mono text-white">
          {totalConflicts}
        </div>
        <div className="text-xs text-junction-muted">
          {hasData ? `${summary.events_per_minute || 0} events/min rate` : "Near misses & braking events"}
        </div>
      </div>

      {/* 3. High-Risk Events */}
      <div className="kpi-card">
        <div className="flex items-center justify-between">
          <span className="panel-title">High-Risk Events</span>
          <AlertTriangle className="w-4 h-4 text-junction-danger" />
        </div>
        <div className="stat-value font-mono text-junction-danger">
          {highRiskCount}
        </div>
        <div className="text-xs text-junction-muted">
          {hasData ? "Severity HIGH & CRITICAL" : "Sub-second TTC / near misses"}
        </div>
      </div>

      {/* 4. Pedestrian Conflicts */}
      <div className="kpi-card">
        <div className="flex items-center justify-between">
          <span className="panel-title">Pedestrian Conflicts</span>
          <UserX className="w-4 h-4 text-junction-warning" />
        </div>
        <div className="stat-value font-mono text-junction-warning">
          {pedConflicts}
        </div>
        <div className="text-xs text-junction-muted">
          {hasData ? "VRU crossing exposures" : "Vehicle–pedestrian interactions"}
        </div>
      </div>
    </div>
  );
}
