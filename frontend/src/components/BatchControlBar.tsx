import React from "react";
import { Play, Download, ShieldAlert, Sparkles, Loader2, CheckCircle } from "lucide-react";
import { getExportUrl } from "@/lib/api";

interface Props {
  totalAvailable: number;
  parsedCount: number;
  isProcessing: boolean;
  selectedLimit: number | null;
  onSelectLimit: (limit: number | null) => void;
  onStartProcess: () => void;
}

export const BatchControlBar: React.FC<Props> = ({
  totalAvailable,
  parsedCount,
  isProcessing,
  selectedLimit,
  onSelectLimit,
  onStartProcess,
}) => {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div className="flex flex-col sm:flex-row sm:items-center gap-4">
        <div>
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
            Batch Mode (Cost Control)
          </span>
          <div className="inline-flex bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-medium">
            <button
              onClick={() => onSelectLimit(10)}
              disabled={isProcessing}
              className={`px-3 py-1.5 rounded-md transition-all ${
                selectedLimit === 10
                  ? "bg-white text-slate-900 shadow-sm font-semibold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Default: Fixed 10 Resumes
            </button>
            <button
              onClick={() => onSelectLimit(null)}
              disabled={isProcessing}
              className={`px-3 py-1.5 rounded-md transition-all ${
                selectedLimit === null
                  ? "bg-white text-slate-900 shadow-sm font-semibold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Parse All ({totalAvailable} Resumes)
            </button>
          </div>
        </div>

        <div className="hidden sm:block h-8 w-px bg-slate-200 my-auto" />

        <div className="text-xs text-slate-500">
          <div>Parsed: <strong className="text-slate-800">{parsedCount}</strong> / {totalAvailable} available</div>
          <div className="text-emerald-600 font-medium flex items-center gap-1 mt-0.5">
            <CheckCircle className="w-3 h-3" /> Catches 1–4 Guardrails Active
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2.5">
        <button
          onClick={onStartProcess}
          disabled={isProcessing}
          className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-sm transition-all disabled:opacity-50"
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Processing Resumes...
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              {parsedCount > 0 ? "Reprocess Batch" : "Start Batch Parsing"}
            </>
          )}
        </button>

        {parsedCount > 0 && (
          <>
            <a
              href={getExportUrl("jsonl")}
              download="results.jsonl"
              className="inline-flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-3 py-2.5 rounded-lg border border-slate-200 transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              results.jsonl
            </a>

            <a
              href={getExportUrl("csv")}
              download="skills.csv"
              className="inline-flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-3 py-2.5 rounded-lg border border-slate-200 transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              skills.csv
            </a>
          </>
        )}
      </div>
    </div>
  );
};
