import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

export default function AnalysisFailedPanel({ error, onRetry }) {
  if (!error) return null;

  return (
    <div className="panel mb-6 border-red-500/40 bg-red-500/10 p-5">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-start space-x-3">
          <div className="p-2 rounded-lg bg-red-500/20 text-red-400 mt-0.5">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-red-300 uppercase tracking-wider font-mono">
              ANALYSIS FAILED
            </h3>
            <p className="text-xs text-slate-200 mt-1 max-w-2xl font-mono leading-relaxed">
              {typeof error === "string" ? error : error.message || JSON.stringify(error)}
            </p>
          </div>
        </div>

        {onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-red-500 hover:bg-red-400 text-junction-bg font-bold text-xs transition-all flex-shrink-0"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Analysis</span>
          </button>
        )}
      </div>
    </div>
  );
}
