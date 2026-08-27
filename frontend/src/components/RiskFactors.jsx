import React from "react";
import { Layers } from "lucide-react";

export default function RiskFactors({ factors = [] }) {
  if (!factors || factors.length === 0) {
    return (
      <div className="panel flex flex-col gap-3">
        <div className="panel-title">Risk factors</div>
        <div className="flex h-56 items-center justify-center rounded-lg border border-dashed border-junction-line bg-junction-bg/40 text-center text-xs text-junction-muted">
          Dominant risk contributors ranked by impact will appear here.
        </div>
      </div>
    );
  }

  const getBarColor = (idx) => {
    const colors = ["bg-red-500", "bg-orange-500", "bg-amber-500", "bg-sky-400", "bg-indigo-400"];
    return colors[idx % colors.length];
  };

  return (
    <div className="panel flex flex-col justify-between">
      <div className="panel-title flex items-center space-x-2">
        <Layers className="w-3.5 h-3.5 text-junction-accent" />
        <span>Dominant Risk Factors</span>
      </div>

      <div className="space-y-3 my-2">
        {factors.map((item, idx) => (
          <div key={idx} className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-200 capitalize truncate max-w-[180px]">
                {item.factor}
              </span>
              <span className="font-mono text-white font-bold text-[11px]">
                {item.weight}%
              </span>
            </div>

            <div className="w-full bg-junction-bg rounded-full h-1.5 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${getBarColor(idx)}`}
                style={{ width: `${Math.max(4, item.weight)}%` }}
              />
            </div>

            <div className="text-[10px] font-mono text-junction-muted">
              Evidence: {item.evidence}
            </div>
          </div>
        ))}
      </div>

      <div className="pt-2 border-t border-junction-line text-[10px] text-junction-muted font-mono">
        Derived from observed physical conflict episodes
      </div>
    </div>
  );
}
