import React, { useState } from "react";
import { ShieldAlert, Search, Play, Filter } from "lucide-react";

export default function EventTable({ events = [], onSeek }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [severityFilter, setSeverityFilter] = useState("ALL");

  if (!events || events.length === 0) {
    return (
      <div className="panel flex flex-col gap-3">
        <div className="panel-title">Detected events</div>
        <div className="flex h-40 items-center justify-center rounded-lg border border-dashed border-junction-line bg-junction-bg/40 text-center text-xs text-junction-muted">
          Every detected conflict with track IDs, type, severity, timestamp and explanation will appear here.
        </div>
      </div>
    );
  }

  const filtered = events.filter((ev) => {
    const term = searchTerm.toLowerCase();
    const matchesSearch =
      searchTerm === "" ||
      (ev.type_label || ev.type || "").toLowerCase().includes(term) ||
      (ev.headline || "").toLowerCase().includes(term) ||
      (ev.explanation || "").toLowerCase().includes(term) ||
      String(ev.actor_a_id || "").includes(term) ||
      String(ev.actor_b_id || "").includes(term);

    const matchesSeverity =
      severityFilter === "ALL" ||
      (ev.severity_label || "").toUpperCase() === severityFilter.toUpperCase();

    return matchesSearch && matchesSeverity;
  });

  const getSeverityBadge = (sev) => {
    switch (sev) {
      case "CRITICAL":
        return "bg-red-500/20 text-red-300 border-red-500/40";
      case "HIGH":
        return "bg-orange-500/20 text-orange-300 border-orange-500/40";
      case "MODERATE":
        return "bg-amber-500/20 text-amber-300 border-amber-500/40";
      case "LOW":
      default:
        return "bg-junction-accent/20 text-junction-accent border-junction-accent/40";
    }
  };

  const formatSec = (s) => {
    const mins = Math.floor(s / 60);
    const secs = (s % 60).toFixed(1);
    return `${mins.toString().padStart(2, "0")}:${secs.padStart(4, "0")}s`;
  };

  return (
    <div className="panel flex flex-col gap-3 overflow-hidden">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-junction-line pb-3">
        <div className="flex items-center space-x-2">
          <div className="panel-title flex items-center space-x-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-junction-accent" />
            <span>Forensic Conflict Events Log</span>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-junction-panel2 border border-junction-line text-junction-muted">
            {filtered.length} recorded
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Search */}
          <div className="relative">
            <Search className="w-3 h-3 absolute left-2.5 top-1/2 -translate-y-1/2 text-junction-muted" />
            <input
              type="text"
              placeholder="Search events..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-7 pr-2.5 py-1 rounded-lg bg-junction-bg border border-junction-line text-xs text-slate-200 placeholder-junction-muted/60 focus:outline-none focus:border-junction-accent font-mono w-40 sm:w-48"
            />
          </div>

          {/* Filter */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-2 py-1 rounded-lg bg-junction-bg border border-junction-line text-xs text-slate-300 focus:outline-none focus:border-junction-accent font-mono"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MODERATE">Moderate</option>
            <option value="LOW">Low</option>
          </select>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse font-sans">
          <thead>
            <tr className="border-b border-junction-line text-[10px] font-mono uppercase tracking-wider text-junction-muted">
              <th className="py-2.5 px-3">Time / Frame</th>
              <th className="py-2.5 px-3">Severity</th>
              <th className="py-2.5 px-3">Conflict Type</th>
              <th className="py-2.5 px-3">Involved Actors</th>
              <th className="py-2.5 px-3">Metrics (TTC / Speed)</th>
              <th className="py-2.5 px-3">Explanation</th>
              <th className="py-2.5 px-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-junction-line/60">
            {filtered.map((ev, i) => (
              <tr
                key={ev.id || i}
                onClick={() => onSeek && onSeek(ev.timestamp_s)}
                className="hover:bg-junction-panel2/50 transition-colors cursor-pointer"
              >
                <td className="py-2.5 px-3 font-mono">
                  <span className="font-bold text-white">
                    {formatSec(ev.timestamp_s || 0)}
                  </span>
                  <span className="block text-[10px] text-junction-muted">
                    F#{ev.frame_start}
                  </span>
                </td>

                <td className="py-2.5 px-3">
                  <span
                    className={`inline-block font-mono text-[9px] font-bold px-1.5 py-0.5 rounded border uppercase ${getSeverityBadge(
                      ev.severity_label
                    )}`}
                  >
                    {ev.severity_label || "LOW"}
                  </span>
                </td>

                <td className="py-2.5 px-3 font-semibold text-slate-200">
                  {ev.type_label || ev.type}
                </td>

                <td className="py-2.5 px-3 font-mono text-[11px]">
                  <div className="flex items-center space-x-1">
                    {ev.actor_a_class && (
                      <span className="px-1.5 py-0.5 rounded bg-junction-bg border border-junction-line text-slate-300">
                        #{ev.actor_a_id} {ev.actor_a_class}
                      </span>
                    )}
                    {ev.actor_b_class && (
                      <>
                        <span className="text-junction-muted">↔</span>
                        <span className="px-1.5 py-0.5 rounded bg-junction-bg border border-junction-line text-slate-300">
                          #{ev.actor_b_id} {ev.actor_b_class}
                        </span>
                      </>
                    )}
                  </div>
                </td>

                <td className="py-2.5 px-3 font-mono text-[11px]">
                  {ev.min_ttc_s ? (
                    <span className="text-red-400 font-bold">
                      TTC: {ev.min_ttc_s}s
                    </span>
                  ) : (
                    <span className="text-junction-muted">
                      {ev.max_speed_px_s ? `${ev.max_speed_px_s} px/s` : "Decel"}
                    </span>
                  )}
                </td>

                <td className="py-2.5 px-3 text-slate-300 text-xs max-w-sm truncate">
                  {ev.explanation || ev.headline}
                </td>

                <td className="py-2.5 px-3 text-right">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onSeek) onSeek(ev.timestamp_s);
                    }}
                    className="inline-flex items-center space-x-1 px-2 py-1 rounded bg-junction-accent/10 hover:bg-junction-accent/20 text-junction-accent border border-junction-accent/30 text-[10px] font-mono transition-colors"
                  >
                    <Play className="w-2.5 h-2.5 fill-current" />
                    <span>Play</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
