import React, { useState } from "react";
import { GitFork, ArrowRight, Check, X, Info, Network, LayoutGrid } from "lucide-react";
import { SkillProxyRule } from "@/lib/types";
import { KnowledgeGraphVisual } from "./KnowledgeGraphVisual";

interface Props {
  proxies: SkillProxyRule[];
  onToggleProxy: (target: string, proxy: string, current: boolean) => void;
}

export const KnowledgeGraphCard: React.FC<Props> = ({ proxies, onToggleProxy }) => {
  const [viewMode, setViewMode] = useState<"visual" | "cards">("visual");

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600">
            <GitFork className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              JD-Driven Skill Knowledge Graph & Transferability Rules
            </h3>
            <p className="text-xs text-slate-500">
              Anchored to this vacancy. Toggle proxies to allow adjacent foundation skills (e.g. Spring MVC for Spring Boot, Stripe for Razorpay).
            </p>
          </div>
        </div>

        {/* View Switcher Toggle */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-semibold">
          <button
            onClick={() => setViewMode("visual")}
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md transition-all cursor-pointer ${
              viewMode === "visual"
                ? "bg-white text-indigo-700 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Network className="w-3.5 h-3.5" />
            Visual Network Graph
          </button>
          <button
            onClick={() => setViewMode("cards")}
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md transition-all cursor-pointer ${
              viewMode === "cards"
                ? "bg-white text-indigo-700 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <LayoutGrid className="w-3.5 h-3.5" />
            Rule Cards
          </button>
        </div>
      </div>

      {viewMode === "visual" ? (
        <KnowledgeGraphVisual proxies={proxies} onToggleProxy={onToggleProxy} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 pt-1">
        {proxies.map((p) => (
          <div
            key={`${p.targetSkill}-${p.proxySkill}`}
            className={`border rounded-lg p-3 text-xs transition-all ${
              p.isEnabled
                ? "bg-slate-50/70 border-slate-200"
                : "bg-slate-100/50 border-slate-200/60 opacity-60"
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5 font-semibold text-slate-800">
                <span className="bg-white border px-1.5 py-0.5 rounded text-blue-600 font-mono">
                  {p.proxySkill}
                </span>
                <ArrowRight className="w-3 h-3 text-slate-400" />
                <span className="bg-white border px-1.5 py-0.5 rounded text-slate-900 font-mono">
                  {p.targetSkill}
                </span>
              </div>

              <button
                onClick={() => onToggleProxy(p.targetSkill, p.proxySkill, p.isEnabled)}
                className={`px-2 py-0.5 rounded text-[11px] font-semibold flex items-center gap-1 transition-colors ${
                  p.isEnabled
                    ? "bg-emerald-600 text-white hover:bg-emerald-700"
                    : "bg-slate-300 text-slate-700 hover:bg-slate-400"
                }`}
              >
                {p.isEnabled ? (
                  <>
                    <Check className="w-3 h-3" /> Allowed
                  </>
                ) : (
                  <>
                    <X className="w-3 h-3" /> Off
                  </>
                )}
              </button>
            </div>

            <div className="text-[11px] text-slate-600 space-y-1">
              <div>
                Weight: <strong>{Math.round(p.transferabilityWeight * 100)}%</strong> • Est. Ramp-up: <strong>{p.rampUpEstimateWeeks}</strong>
              </div>
              <div className="text-slate-500 line-clamp-1">
                Shared: {p.sharedConcepts.join(", ")}
              </div>
            </div>
          </div>
        ))}
      </div>
    )}
  </div>
);
};
