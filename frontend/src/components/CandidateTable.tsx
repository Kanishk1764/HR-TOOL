import React from "react";
import { Candidate } from "@/lib/types";
import { ExternalLink, CheckCircle, AlertTriangle, ShieldCheck } from "lucide-react";

interface Props {
  candidates: Candidate[];
  onSelectCandidate: (candidate: Candidate) => void;
}

export const CandidateTable: React.FC<Props> = ({ candidates, onSelectCandidate }) => {
  if (candidates.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-12 text-center text-slate-500">
        No candidates parsed yet. Click <strong>Start Batch Parsing</strong> above to evaluate the default 10 resumes.
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden mb-6">
      <div className="p-4 border-b border-slate-100 flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-800">
          Candidate Evaluation Leaderboard ({candidates.length})
        </h3>
        <span className="text-xs text-slate-500">
          Direct vs Transferable Matching
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-600">
          <thead className="bg-slate-50 border-b border-slate-200 font-semibold text-slate-700 uppercase tracking-wider text-[11px]">
            <tr>
              <th className="py-3 px-4">Candidate / Document</th>
              <th className="py-3 px-4">Direct Match</th>
              <th className="py-3 px-4">Transferable</th>
              <th className="py-3 px-4">Supported Java Exp</th>
              <th className="py-3 px-4">Evidence & Key Skills</th>
              <th className="py-3 px-4">Verdict</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {candidates.map((c) => {
              const vm = c.vacancyMatch;
              const direct = vm ? vm.directMatchScore : 0;
              const transferable = vm ? vm.transferableScore : 0;
              const javaYears = vm ? vm.supportedJavaYears : 0;
              const verdict = vm ? vm.verdict : "Under Review";

              const verdictColor =
                verdict === "Strong Fit"
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : verdict === "Transferable Fit"
                  ? "bg-indigo-50 text-indigo-700 border-indigo-200"
                  : verdict === "Junior/Mid Fit"
                  ? "bg-amber-50 text-amber-700 border-amber-200"
                  : "bg-slate-100 text-slate-600 border-slate-200";

              return (
                <tr key={c.documentId} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4">
                    <div className="font-bold text-slate-900 text-xs">{c.candidateName}</div>
                    <div className="text-[11px] text-slate-400 font-mono truncate max-w-[200px]" title={c.documentId}>
                      {c.documentId}
                    </div>
                  </td>

                  <td className="py-3 px-4">
                    <div className="flex items-center gap-1.5">
                      <span className="font-bold text-slate-800 text-xs">{direct}%</span>
                      <div className="w-16 bg-slate-100 h-1.5 rounded-full overflow-hidden">
                        <div
                          className="bg-blue-600 h-full rounded-full"
                          style={{ width: `${Math.min(100, direct)}%` }}
                        />
                      </div>
                    </div>
                  </td>

                  <td className="py-3 px-4">
                    <div className="flex items-center gap-1.5">
                      <span className="font-bold text-indigo-600 text-xs">{transferable}%</span>
                      <div className="w-16 bg-slate-100 h-1.5 rounded-full overflow-hidden">
                        <div
                          className="bg-indigo-500 h-full rounded-full"
                          style={{ width: `${Math.min(100, transferable)}%` }}
                        />
                      </div>
                    </div>
                  </td>

                  <td className="py-3 px-4">
                    <span className={`font-semibold ${javaYears >= 5.0 ? "text-emerald-700" : "text-slate-700"}`}>
                      {javaYears > 0 ? `${javaYears} yrs` : "0.0 yrs (undated)"}
                    </span>
                  </td>

                  <td className="py-3 px-4">
                    <div className="flex flex-wrap gap-1 max-w-[260px]">
                      {c.skillSummary.slice(0, 4).map((s) => (
                        <span
                          key={s.skill}
                          className="bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded text-[10px] border border-slate-200"
                        >
                          {s.skill}
                        </span>
                      ))}
                      {c.skillSummary.length > 4 && (
                        <span className="text-[10px] text-slate-400 self-center">
                          +{c.skillSummary.length - 4} more
                        </span>
                      )}
                    </div>
                  </td>

                  <td className="py-3 px-4">
                    <span className={`inline-flex px-2 py-0.5 rounded text-[11px] font-semibold border ${verdictColor}`}>
                      {verdict}
                    </span>
                  </td>

                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => onSelectCandidate(c)}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 px-2.5 py-1.5 rounded-md transition-all"
                    >
                      <ShieldCheck className="w-3.5 h-3.5" />
                      Inspect Audit
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
