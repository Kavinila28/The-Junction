import React, { useState, useEffect } from "react";
import {
  Sliders,
  Sparkles,
  ArrowDownRight,
  Info,
  CheckSquare,
  Square,
  RefreshCw,
  X,
} from "lucide-react";
import { simulateInterventions } from "../api/client";

const COUNTERMEASURES = [
  {
    id: "pedestrian_signal",
    title: "Dedicated Pedestrian Signal with LPI",
    category: "Signal Infrastructure",
    description:
      "Provides a 3–7s lead pedestrian interval before vehicle turn phase to eliminate turning conflict overlaps.",
    targeted: ["Pedestrian Conflicts", "Near Misses"],
    cost: "$$",
  },
  {
    id: "zebra_crossing",
    title: "Raised High-Visibility Zebra Crossing",
    category: "Physical Roadway",
    description:
      "Elevates crosswalk profile and adds high-intensity reflector studs, increasing driver yielding rates.",
    targeted: ["Pedestrian Conflicts", "Unsafe Proximity"],
    cost: "$",
  },
  {
    id: "reduce_speed",
    title: "Traffic Calming & Speed Reduction Zone (30 km/h)",
    category: "Speed Management",
    description:
      "Transverse optical bars and radar feedback signs reduce vehicle approach kinetic energy.",
    targeted: ["Sudden Deceleration", "Near Misses"],
    cost: "$",
  },
  {
    id: "lane_markings",
    title: "Turn Channelization & Curved Guide Markings",
    category: "Road Geometry",
    description:
      "Physical splitter islands and retroreflective guide lines prevent left-turn trajectory drift.",
    targeted: ["Path Intersection", "Unsafe Proximity"],
    cost: "$",
  },
  {
    id: "signal_timing",
    title: "Extended All-Red Clearance Phase",
    category: "Signal Infrastructure",
    description:
      "Extends clearance interval between conflicting phases to eliminate dilemma zone collisions.",
    targeted: ["Near Misses", "Path Convergence"],
    cost: "$",
  },
];

export default function InterventionSimulator({
  analysisId,
  baselineScore = 61,
  baselineCategory = "HIGH",
  onClose,
}) {
  const [selected, setSelected] = useState(["pedestrian_signal"]);
  const [simulation, setSimulation] = useState(null);
  const [loading, setLoading] = useState(false);

  const toggle = (id) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const runSim = async () => {
    if (!analysisId) return;
    setLoading(true);
    try {
      const res = await simulateInterventions(analysisId, selected);
      setSimulation(res);
    } catch (err) {
      console.error("Simulation error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runSim();
  }, [selected, analysisId]);

  const getCategoryColor = (cat) => {
    switch (cat) {
      case "CRITICAL":
        return "text-red-400 bg-red-500/20 border-red-500/40";
      case "HIGH":
        return "text-orange-400 bg-orange-500/20 border-orange-500/40";
      case "MODERATE":
        return "text-amber-400 bg-amber-500/20 border-amber-500/40";
      case "LOW":
      default:
        return "text-emerald-400 bg-emerald-500/20 border-emerald-500/40";
    }
  };

  return (
    <div className="panel mb-6 border-junction-accent/40 bg-junction-panel">
      <div className="flex items-center justify-between border-b border-junction-line pb-3 mb-4">
        <div className="flex items-center space-x-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-junction-accent/20 text-junction-accent">
            <Sliders className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              INTERVENTION IMPACT SIMULATOR
            </h3>
            <p className="text-xs text-junction-muted">
              Deterministic decision-support countermeasure projections
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={runSim}
            disabled={loading}
            className="flex items-center space-x-1 px-2.5 py-1 rounded bg-junction-panel2 border border-junction-line text-xs font-mono text-slate-300 hover:text-white"
          >
            <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} />
            <span>Recalculate</span>
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 rounded text-junction-muted hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Countermeasures (7 cols) */}
        <div className="lg:col-span-7 space-y-2.5">
          <div className="text-xs font-mono uppercase tracking-wider text-junction-muted mb-1">
            Toggle Proposed Interventions
          </div>

          <div className="space-y-2">
            {COUNTERMEASURES.map((item) => {
              const isChecked = selected.includes(item.id);
              return (
                <div
                  key={item.id}
                  onClick={() => toggle(item.id)}
                  className={`p-3 rounded-lg border transition-all cursor-pointer ${
                    isChecked
                      ? "border-junction-accent/40 bg-junction-accent/10"
                      : "border-junction-line bg-junction-panel2/40 hover:border-junction-line/80"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start space-x-2.5">
                      <div className="mt-0.5 text-junction-accent">
                        {isChecked ? (
                          <CheckSquare className="w-4 h-4" />
                        ) : (
                          <Square className="w-4 h-4 text-junction-muted" />
                        )}
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-bold text-white">
                            {item.title}
                          </span>
                          <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-junction-bg text-junction-muted border border-junction-line">
                            {item.category}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-300 mt-0.5">
                          {item.description}
                        </p>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono font-bold text-junction-muted px-1.5 py-0.5 rounded bg-junction-bg">
                      {item.cost}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Projected Risk Impact (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="text-xs font-mono uppercase tracking-wider text-junction-muted mb-1">
            Projected Safety Impact
          </div>

          <div className="grid grid-cols-2 gap-2.5">
            {/* Baseline */}
            <div className="bg-junction-bg p-3 rounded-lg border border-junction-line text-center">
              <span className="text-[10px] font-mono text-junction-muted uppercase">
                Baseline Risk
              </span>
              <div className="text-2xl font-bold font-mono text-white mt-0.5">
                {simulation?.baseline_risk_score ?? baselineScore}
              </div>
              <span
                className={`inline-block text-[9px] font-mono font-bold px-1.5 py-0.2 rounded border uppercase mt-1 ${getCategoryColor(
                  simulation?.baseline_risk_category || baselineCategory
                )}`}
              >
                {simulation?.baseline_risk_category || baselineCategory}
              </span>
            </div>

            {/* Projected */}
            <div className="bg-emerald-500/10 p-3 rounded-lg border border-emerald-500/30 text-center">
              <span className="text-[10px] font-mono text-emerald-400 uppercase font-semibold">
                Projected Risk
              </span>
              <div className="text-2xl font-bold font-mono text-emerald-300 mt-0.5">
                {simulation?.projected_risk_score ?? "—"}
              </div>
              <span
                className={`inline-block text-[9px] font-mono font-bold px-1.5 py-0.2 rounded border uppercase mt-1 ${getCategoryColor(
                  simulation?.projected_risk_category || "LOW"
                )}`}
              >
                {simulation?.projected_risk_category || "—"}
              </span>
            </div>
          </div>

          {/* Overall Reduction */}
          <div className="p-3 rounded-lg bg-gradient-to-r from-emerald-950/40 via-junction-panel2 to-emerald-950/40 border border-emerald-500/30 flex items-center justify-between">
            <div>
              <span className="text-xs font-mono text-slate-200 block">
                Estimated Risk Reduction
              </span>
              <span className="text-[10px] text-junction-muted font-mono">
                From {selected.length} countermeasure(s)
              </span>
            </div>
            <div className="text-2xl font-extrabold text-emerald-400 font-mono flex items-center">
              <ArrowDownRight className="w-5 h-5 mr-0.5" />
              {simulation?.overall_reduction_percent ?? "0.0"}%
            </div>
          </div>

          {/* Breakdown */}
          <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
            {simulation?.interventions_impact?.map((imp, idx) => (
              <div
                key={idx}
                className="p-2 rounded bg-junction-bg/60 border border-junction-line text-[11px] font-mono flex items-center justify-between"
              >
                <span className="text-slate-300 truncate max-w-[200px]">
                  {imp.title}
                </span>
                <span className="text-emerald-400 font-bold">
                  -{imp.individual_reduction_percent}%
                </span>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t border-junction-line flex items-start space-x-1.5 text-[9px] text-junction-muted font-mono">
            <Info className="w-3 h-3 text-junction-accent flex-shrink-0 mt-0.5" />
            <span>
              ESTIMATE — deterministic decision-support projection based on observed conflict distribution, not a guaranteed real-world prediction.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
