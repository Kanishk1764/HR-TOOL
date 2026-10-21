import React, { useState } from "react";
import { Candidate } from "@/lib/types";
import { X, ShieldCheck, AlertCircle, Quote, Calendar, Award, Building, CheckCircle2 } from "lucide-react";

interface Props {
  candidate: Candidate | null;
  onClose: () => void;
}

export const TraceabilityDrawer: React.FC<Props> = ({ candidate, onClose }) => {
  const [activeTab, setActiveTab] = useState<"skills" | "roles" | "insights">("skills");

  if (!candidate) return null;

  const vm = candidate.vacancyMatch;
  const insights = candidate.selectionInsights;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col border-l border-slate-200">
        {/* Header */}
        <div className="p-5 border-b border-slate-200 flex items-start justify-between bg-slate-50/50">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-emerald-700 bg-emerald-100/60 border border-emerald-200 px-2 py-0.5 rounded w-max mb-1.5">
              <ShieldCheck className="w-3.5 h-3.5" />
              Traceability Audit & Evidence Inspector
            </div>
            <h2 className="text-xl font-bold text-slate-900">{candidate.candidateName}</h2>
            <p className="text-xs text-slate-500 font-mono mt-0.5">{candidate.documentId}</p>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Match Snapshot */}
        <div className="p-4 bg-slate-50 border-b border-slate-200 grid grid-cols-3 gap-3 text-center text-xs">
          <div className="bg-white p-2.5 rounded-lg border border-slate-200">
            <span className="text-slate-500 block text-[11px]">Direct Match</span>
            <strong className="text-sm text-slate-900">{vm?.directMatchScore || 0}%</strong>
          </div>
          <div className="bg-white p-2.5 rounded-lg border border-slate-200">
            <span className="text-slate-500 block text-[11px]">Transferable Match</span>
            <strong className="text-sm text-indigo-600">{vm?.transferableScore || 0}%</strong>
          </div>
          <div className="bg-white p-2.5 rounded-lg border border-slate-200">
            <span className="text-slate-500 block text-[11px]">Supported Java Exp</span>
            <strong className="text-sm text-emerald-600">{vm?.supportedJavaYears || 0} Years</strong>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-slate-200 text-xs font-semibold px-4 pt-2">
          <button
            onClick={() => setActiveTab("skills")}
            className={`px-4 py-2.5 border-b-2 transition-all ${
              activeTab === "skills"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            Skill Claims & Verifiable Quotes ({candidate.skillClaims.length})
          </button>
          <button
            onClick={() => setActiveTab("roles")}
            className={`px-4 py-2.5 border-b-2 transition-all ${
              activeTab === "roles"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            Roles & Employment ({candidate.roles.length})
          </button>
          <button
            onClick={() => setActiveTab("insights")}
            className={`px-4 py-2.5 border-b-2 transition-all ${
              activeTab === "insights"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            Selection Insights & Gaps
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 flex-1 overflow-y-auto space-y-4 text-xs">
          {activeTab === "skills" && (
            <div className="space-y-4">
              <div className="bg-blue-50/60 border border-blue-200/60 p-3 rounded-lg text-blue-800 text-[11px]">
                <strong>Audit Note:</strong> Durations are calculated via deterministic interval union math. Every claim must have an exact verbatim quote verified against the document.
              </div>

              {candidate.skillClaims.map((claim, idx) => (
                <div key={idx} className="border border-slate-200 rounded-lg p-3.5 bg-white space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-900 text-sm">{claim.skill}</span>
                      <span className="text-[10px] bg-slate-100 text-slate-600 border px-1.5 py-0.5 rounded">
                        {claim.evidenceType}
                      </span>
                    </div>

                    <span className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded ${
                      claim.isQuoteVerified ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-amber-50 text-amber-700 border border-amber-200"
                    }`}>
                      {claim.isQuoteVerified ? (
                        <>
                          <CheckCircle2 className="w-3 h-3" /> Quote Verified in Document
                        </>
                      ) : (
                        <>
                          <AlertCircle className="w-3 h-3" /> Quote Unverified
                        </>
                      )}
                    </span>
                  </div>

                  {/* Quote block */}
                  <div className="bg-slate-50 border-l-2 border-slate-400 p-2 text-slate-700 italic flex items-start gap-1.5">
                    <Quote className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                    <span>&quot;{claim.supportingText}&quot;</span>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-500 pt-1">
                    {claim.start && (
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3 text-slate-400" />
                        {claim.start} to {claim.end || (claim.isOngoing ? "Present" : "unknown")}
                      </span>
                    )}
                    {claim.claimedDurationMonths && (
                      <span>Claimed: {claim.claimedDurationMonths} months ({claim.durationQualifier || "exact"})</span>
                    )}
                    {claim.statedLevel && (
                      <span className="flex items-center gap-1 text-indigo-600 font-semibold">
                        <Award className="w-3 h-3" /> Stated Level: {claim.statedLevel}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === "roles" && (
            <div className="space-y-4">
              {candidate.roles.map((r) => (
                <div key={r.id} className="border border-slate-200 rounded-lg p-3.5 bg-white space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 font-bold text-slate-900 text-sm">
                      <Building className="w-4 h-4 text-slate-500" />
                      {r.title}
                    </div>
                    <span className="text-slate-500 text-[11px]">
                      {r.start || "unknown"} – {r.end || (r.isCurrent ? "Present" : "unknown")}
                    </span>
                  </div>
                  <div className="text-xs text-blue-600 font-medium">{r.company}</div>

                  {r.responsibilities.length > 0 && (
                    <ul className="list-disc pl-4 space-y-1 text-slate-600 text-[11px]">
                      {r.responsibilities.map((resp, i) => (
                        <li key={i}>{resp}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          )}

          {activeTab === "insights" && insights && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="border border-slate-200 rounded-lg p-3 bg-slate-50">
                  <span className="text-[11px] text-slate-500 block">Tenure Stability Score</span>
                  <strong className="text-lg text-slate-900">{insights.stabilityScore} / 10</strong>
                  <p className="text-[10px] text-slate-500 mt-1">Average company tenure: {insights.averageTenureMonths} months</p>
                </div>

                <div className="border border-slate-200 rounded-lg p-3 bg-slate-50">
                  <span className="text-[11px] text-slate-500 block">Career Velocity</span>
                  <strong className="text-lg capitalize text-blue-600">{insights.careerVelocity}</strong>
                  <p className="text-[10px] text-slate-500 mt-1">Signals: {insights.leadershipSignals.length} detected</p>
                </div>
              </div>

              {insights.leadershipSignals.length > 0 && (
                <div className="border border-slate-200 rounded-lg p-3 bg-white">
                  <span className="font-semibold text-slate-800 block mb-2 text-xs">Leadership & Ownership Quotes</span>
                  <ul className="list-disc pl-4 space-y-1 text-slate-600 text-[11px]">
                    {insights.leadershipSignals.map((sig, i) => (
                      <li key={i}>{sig}</li>
                    ))}
                  </ul>
                </div>
              )}

              {insights.redFlags.length > 0 && (
                <div className="border border-amber-200 bg-amber-50 rounded-lg p-3 text-amber-800 text-[11px]">
                  <span className="font-semibold block mb-1">Audit Flags</span>
                  <ul className="list-disc pl-4 space-y-1">
                    {insights.redFlags.map((flag, i) => (
                      <li key={i}>{flag}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
