import React from "react";
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from "recharts";
import { PieChart as PieIcon } from "lucide-react";

const TYPE_COLORS = {
  vehicle_pedestrian: "#ef4444",
  near_miss: "#f97316",
  sudden_braking: "#fbbf24",
  trajectory_intersection: "#38bdf8",
};

const TYPE_LABELS = {
  vehicle_pedestrian: "Vehicle–Pedestrian",
  near_miss: "Near Miss",
  sudden_braking: "Sudden Braking",
  trajectory_intersection: "Path Intersection",
};

export default function ConflictDistribution({ counts = {}, events = [] }) {
  // Extract counts
  let mergedCounts = { ...counts };
  if (Object.keys(mergedCounts).length === 0 && events.length > 0) {
    events.forEach((e) => {
      const t = e.event_type || e.type || "other";
      mergedCounts[t] = (mergedCounts[t] || 0) + 1;
    });
  }

  const data = Object.entries(mergedCounts)
    .filter(([_, count]) => count > 0)
    .map(([type, count]) => ({
      type,
      name: TYPE_LABELS[type] || type.replace(/_/g, " "),
      value: count,
      color: TYPE_COLORS[type] || "#818cf8",
    }));

  if (data.length === 0) {
    return (
      <div className="panel flex flex-col gap-3">
        <div className="panel-title">Conflict type distribution</div>
        <div className="flex h-56 items-center justify-center rounded-lg border border-dashed border-junction-line bg-junction-bg/40 text-center text-xs text-junction-muted">
          Bars for near-miss, vehicle–pedestrian, trajectory-intersection and braking events.
        </div>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const item = payload[0];
      const total = data.reduce((s, d) => s + d.value, 0);
      const pct = ((item.value / total) * 100).toFixed(1);
      return (
        <div className="rounded-lg border border-junction-line bg-junction-bg/95 p-2.5 shadow-xl backdrop-blur text-xs font-sans">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: item.payload.color }} />
            <span className="font-bold text-white">{item.name}</span>
          </div>
          <div className="mt-1 flex items-center space-x-3 text-slate-300 font-mono text-[11px]">
            <span>Count: <strong className="text-white">{item.value}</strong></span>
            <span>Ratio: <strong className="text-junction-accent">{pct}%</strong></span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="panel flex flex-col justify-between">
      <div className="panel-title flex items-center space-x-2">
        <PieIcon className="w-3.5 h-3.5 text-junction-accent" />
        <span>Conflict Type Distribution</span>
      </div>

      <div className="h-44 w-full my-2">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={42}
              outerRadius={65}
              paddingAngle={4}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} stroke="#0a0f1e" strokeWidth={2} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-2 gap-1.5 pt-2 border-t border-junction-line">
        {data.map((d) => (
          <div key={d.type} className="flex items-center justify-between text-[10px] font-mono">
            <div className="flex items-center space-x-1.5 truncate">
              <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: d.color }} />
              <span className="text-slate-300 truncate">{d.name}</span>
            </div>
            <span className="font-bold text-white ml-1">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
