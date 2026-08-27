import React from "react";
import { Sparkles, ArrowRight, ShieldCheck } from "lucide-react";

export default function RecommendationCard({ recommendations = [], onOpenSimulator }) {
  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="panel flex flex-col gap-3">
        <div className="panel-title">AI safety recommendation</div>
        <div className="flex h-56 items-center justify-center rounded-lg border border-dashed border-junction-line bg-junction-bg/40 text-center text-xs text-junction-muted">
          Rule-based interventions suggested by detected conflict patterns.
        </div>
      </div>
    );
  }

  const primary = recommendations[0];

  return (
    <div className="panel flex flex-col justify-between border-junction-accent/40 bg-gradient-to-br from-junction-panel via-junction-panel2 to-junction-panel">
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-1.5 text-xs font-mono font-bold text-junction-accent uppercase">
            <Sparkles className="w-3.5 h-3.5 animate-pulse" />
            <span>AI Safety Recommendation</span>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-junction-accent/10 border border-junction-accent/30 text-junction-accent">
            Priority #{primary.priority || 1}
          </span>
        </div>

        <h3 className="text-sm font-bold text-white mb-1.5">
          {primary.measure}
        </h3>

        <p className="text-xs text-slate-300 leading-relaxed mb-2.5">
          {primary.action}
        </p>

        <div className="p-2.5 rounded bg-junction-bg/60 border border-junction-line text-[11px] text-junction-muted">
          <strong className="text-slate-200">Rationale: </strong>
          {primary.rationale}
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-junction-line flex items-center justify-between">
        <span className="text-[10px] text-junction-muted font-mono">
          Decision-support heuristic
        </span>
        {onOpenSimulator && (
          <button
            onClick={onOpenSimulator}
            className="flex items-center space-x-1 text-xs font-semibold text-junction-accent hover:text-white transition-colors"
          >
            <span>Simulate impact</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        )}
      </div>
    </div>
  );
}
