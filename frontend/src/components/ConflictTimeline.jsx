import React from "react";
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  Tooltip,
  Cell,
} from "recharts";
import { Clock } from "lucide-react";

const SEVERITY_COLORS = {
  CRITICAL: "#ef4444",
  HIGH: "#f97316",
  MODERATE: "#fbbf24",
  LOW: "#38bdf8",
};

const SEVERITY_NUM = {
  CRITICAL: 4,
  HIGH: 3,
  MODERATE: 2,
  LOW: 1,
};

export default function ConflictTimeline({ events = [], durationS = 30, onSelectTimestamp }) {
  if (!events || events.length === 0) {
    return (
      <div className="panel flex flex-col gap-3">
        <div className="panel-title">Conflict timeline</div>
        <div className="flex h-56 items-center justify-center rounded-lg border border-dashed border-junction-line bg-junction-bg/40 text-center text-xs text-junction-muted">
          Timestamped events will be plotted here after analysis.
        </div>
      </div>
    );
  }

  const data = events.map((ev, i) => ({
    id: ev.id || i,
    timestamp: ev.timestamp_s,
    severityNum: SEVERITY_NUM[ev.severity_label] || ev.severity || 1,
    severity: ev.severity_label || "LOW",
    type: ev.type_label || ev.type,
    headline: ev.headline || ev.explanation,
    ttc: ev.min_ttc_s,
    gap: ev.min_gap_px,
    color: SEVERITY_COLORS[ev.severity_label] || "#38bdf8",
  }));

  const maxTime = Math.max(durationS, ...events.map((e) => (e.timestamp_s || 0) + 1));

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload;
      return (
        <div className="rounded-lg border border-junction-line bg-junction-bg/95 p-3 shadow-xl backdrop-blur text-xs max-w-xs font-sans">
          <div className="flex items-center justify-between border-b border-junction-line pb-1 mb-1.5 font-mono">
            <span
              className="font-bold px-1.5 py-0.5 rounded text-[10px]"
              style={{
                backgroundColor: `${item.color}25`,
                color: item.color,
                border: `1px solid ${item.color}50`,
              }}
            >
              {item.severity}
            </span>
            <span className="text-junction-muted">T: {item.timestamp}s</span>
          </div>
          <div className="font-semibold text-white">{item.type}</div>
          <p className="mt-1 text-slate-300 text-[11px] leading-tight">
            {item.headline}
          </p>
          {item.ttc && (
            <div className="mt-1.5 text-[10px] font-mono text-junction-muted">
              TTC: <strong className="text-red-400">{item.ttc}s</strong>
            </div>
          )}
          <div className="mt-1.5 pt-1 border-t border-junction-line text-[10px] text-junction-accent font-mono">
            Click dot to jump video
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="panel flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="panel-title flex items-center space-x-2">
          <Clock className="w-3.5 h-3.5 text-junction-accent" />
          <span>Conflict Timeline</span>
        </div>
        <div className="flex items-center space-x-2 text-[10px] font-mono">
          {Object.entries(SEVERITY_COLORS).map(([sev, col]) => (
            <span key={sev} className="flex items-center space-x-1">
              <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: col }} />
              <span className="text-junction-muted capitalize">{sev.toLowerCase()}</span>
            </span>
          ))}
        </div>
      </div>

      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 15, bottom: 20, left: 0 }}>
            <XAxis
              type="number"
              dataKey="timestamp"
              domain={[0, maxTime]}
              unit="s"
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: "#1f2c47" }}
            />
            <YAxis
              type="number"
              dataKey="severityNum"
              domain={[0.5, 4.5]}
              ticks={[1, 2, 3, 4]}
              tickFormatter={(val) => ["Low", "Mod", "High", "Crit"][val - 1] || ""}
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: "#1f2c47" }}
            />
            <ZAxis range={[60, 140]} />
            <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: "3 3", stroke: "#334155" }} />
            <Scatter
              data={data}
              onClick={(node) => {
                if (node && onSelectTimestamp) onSelectTimestamp(node.timestamp);
              }}
              cursor="pointer"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} stroke="#0a0f1e" strokeWidth={1.5} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
