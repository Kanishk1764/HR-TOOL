import React, { useState } from "react";
import { SkillProxyRule } from "@/lib/types";
import { Sparkles, CheckCircle2, XCircle, ArrowRight, Layers, HelpCircle } from "lucide-react";

interface Props {
  proxies: SkillProxyRule[];
  onToggleProxy: (target: string, proxy: string, current: boolean) => void;
}

export const KnowledgeGraphVisual: React.FC<Props> = ({ proxies, onToggleProxy }) => {
  const [selectedRule, setSelectedRule] = useState<SkillProxyRule | null>(null);

  // Group into distinct targets and proxies for layout
  const distinctTargets = Array.from(new Set(proxies.map((p) => p.targetSkill)));
  const distinctProxies = Array.from(new Set(proxies.map((p) => p.proxySkill)));

  return (
    <div className="bg-gradient-to-b from-slate-900 via-slate-900 to-slate-950 rounded-xl p-5 text-white border border-slate-800 shadow-xl overflow-hidden">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-blue-500/20 border border-blue-400/40 flex items-center justify-center text-blue-400">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold tracking-tight text-white flex items-center gap-2">
              Interactive JD Knowledge Graph Network
              <span className="text-[10px] font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/30 px-2 py-0.5 rounded-full">
                Vector / Semantic Proxies
              </span>
            </h4>
            <p className="text-xs text-slate-400">
              Visualizes how candidate skills bridge into mandatory JD requirements. Click any node or link to toggle.
            </p>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs text-slate-400">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50" />
            <span className="text-[11px]">Active Transfer</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-slate-600 border border-dashed border-slate-400" />
            <span className="text-[11px]">Inactive / Blocked</span>
          </div>
        </div>
      </div>

      {/* Interactive Visual Network Canvas */}
      <div className="relative min-h-[340px] flex items-center justify-between px-2 sm:px-8 py-4">
        {/* Left Column: Candidate Proxy Skills (Adjacent Experience) */}
        <div className="flex flex-col justify-around h-full space-y-4 z-10 w-44">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
            <span>Candidate Proxies</span>
          </div>
          {proxies.map((p) => {
            const isSelected = selectedRule?.proxySkill === p.proxySkill && selectedRule?.targetSkill === p.targetSkill;
            return (
              <div
                key={`proxy-${p.proxySkill}`}
                onClick={() => {
                  setSelectedRule(p);
                  onToggleProxy(p.targetSkill, p.proxySkill, p.isEnabled);
                }}
                className={`group cursor-pointer p-2.5 rounded-lg border transition-all text-left ${
                  p.isEnabled
                    ? "bg-slate-800/90 border-emerald-500/60 shadow-lg shadow-emerald-950/40 text-emerald-300 hover:border-emerald-400"
                    : "bg-slate-800/40 border-slate-700/60 text-slate-400 hover:border-slate-500"
                } ${isSelected ? "ring-2 ring-blue-400" : ""}`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs tracking-tight">{p.proxySkill}</span>
                  <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded font-bold ${
                    p.isEnabled ? "bg-emerald-500/20 text-emerald-400" : "bg-slate-700 text-slate-400"
                  }`}>
                    {Math.round(p.transferabilityWeight * 100)}%
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 mt-1 line-clamp-1">
                  Ramp-up: {p.rampUpEstimateWeeks}
                </div>
              </div>
            );
          })}
        </div>

        {/* Center: Dynamic SVG Connecting Links */}
        <div className="flex-1 px-4 relative flex items-center justify-center">
          <svg className="w-full h-[320px] overflow-visible">
            <defs>
              <linearGradient id="activeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#10b981" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.8" />
              </linearGradient>
            </defs>

            {proxies.map((p, idx) => {
              const total = proxies.length;
              // Compute dynamic Y offsets
              const startY = 35 + idx * 62;
              const endY = 35 + idx * 62;
              const midX = 140;

              return (
                <g key={`edge-${p.proxySkill}-${p.targetSkill}`}>
                  {/* Connecting Bézier line */}
                  <path
                    d={`M 10 ${startY} C ${midX} ${startY}, ${midX} ${endY}, 270 ${endY}`}
                    fill="none"
                    stroke={p.isEnabled ? "url(#activeGrad)" : "#475569"}
                    strokeWidth={p.isEnabled ? 2.5 : 1.5}
                    strokeDasharray={p.isEnabled ? "none" : "4 4"}
                    className="transition-all duration-300"
                  />

                  {/* Transferability Weight Badge in Center */}
                  <foreignObject x="115" y={startY - 12} width="55" height="26">
                    <div
                      onClick={() => onToggleProxy(p.targetSkill, p.proxySkill, p.isEnabled)}
                      className={`cursor-pointer text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-full text-center border shadow-xs transition-transform hover:scale-110 ${
                        p.isEnabled
                          ? "bg-slate-900 border-emerald-500/70 text-emerald-300"
                          : "bg-slate-800 border-slate-600 text-slate-400"
                      }`}
                    >
                      {p.isEnabled ? "✓" : "✕"} {Math.round(p.transferabilityWeight * 100)}%
                    </div>
                  </foreignObject>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Right Column: JD Target Skills (Mandatory Requirements) */}
        <div className="flex flex-col justify-around h-full space-y-4 z-10 w-44">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1 flex items-center justify-end gap-1">
            <span>JD Target Requirements</span>
          </div>
          {proxies.map((p) => {
            return (
              <div
                key={`target-${p.targetSkill}-${p.proxySkill}`}
                className="p-2.5 rounded-lg border bg-blue-950/40 border-blue-500/40 text-blue-200 text-right shadow-md"
              >
                <div className="flex items-center justify-end gap-1.5">
                  <span className="font-semibold text-xs tracking-tight">{p.targetSkill}</span>
                  <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                </div>
                <div className="text-[10px] text-blue-300/70 mt-1">
                  Mandatory Competency
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Bottom Context Panel */}
      <div className="mt-4 pt-3 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-slate-400 gap-2">
        <div>
          💡 <strong>Tip:</strong> Click any proxy rule to toggle. When enabled, candidates with foundation skills (e.g. <em>Spring MVC</em>) receive weighted proxy credit toward the vacancy requirement (<em>Spring Boot</em>) without hallucinating dates.
        </div>
        <div className="text-right text-[11px] text-slate-500 shrink-0">
          Deterministic Matrix Engine
        </div>
      </div>
    </div>
  );
};
