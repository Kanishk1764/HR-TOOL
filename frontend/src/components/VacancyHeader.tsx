import React from "react";
import { Briefcase, MapPin, Clock, CheckCircle2, ChevronDown, Plus, Trash2 } from "lucide-react";
import { VacancyInfo, VacancySummary } from "@/lib/types";

interface Props {
  vacancy: VacancyInfo | null;
  vacancies?: VacancySummary[];
  activeVacancyId?: string;
  onSelectVacancy?: (id: string) => void;
  onOpenCreateVacancy?: () => void;
  onDeleteVacancy?: (id: string) => void;
}

export const VacancyHeader: React.FC<Props> = ({
  vacancy,
  vacancies = [],
  activeVacancyId,
  onSelectVacancy,
  onOpenCreateVacancy,
  onDeleteVacancy,
}) => {
  if (!vacancy) return null;

  const isDefaultBenchmark = activeVacancyId?.includes("SeniorSoftwareEngineerJavaBackend");

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm mb-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div>
          <div className="flex flex-wrap items-center gap-3 mb-1">
            <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-blue-600">
              <Briefcase className="w-3.5 h-3.5" />
              Active Workspace
            </div>

            {/* Vacancy Switcher Dropdown */}
            {vacancies.length > 0 && (
              <div className="flex items-center gap-2">
                <select
                  value={activeVacancyId}
                  onChange={(e) => onSelectVacancy && onSelectVacancy(e.target.value)}
                  className="bg-slate-100/80 hover:bg-slate-100 border border-slate-200 text-slate-800 text-xs font-semibold rounded-lg px-2.5 py-1 outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
                >
                  {vacancies.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.title} ({v.resumeCount} Resumes{v.parsedCount > 0 ? ` • ${v.parsedCount} Parsed` : ""})
                    </option>
                  ))}
                </select>

                <button
                  onClick={onOpenCreateVacancy}
                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 px-2 py-1 rounded-lg transition-colors cursor-pointer"
                  title="Create a new isolated vacancy workspace"
                >
                  <Plus className="w-3 h-3" />
                  New Vacancy
                </button>

                {activeVacancyId && !isDefaultBenchmark && (
                  <button
                    onClick={() => onDeleteVacancy && onDeleteVacancy(activeVacancyId)}
                    className="inline-flex items-center gap-1 text-[11px] font-semibold text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 px-2 py-1 rounded-lg transition-colors cursor-pointer"
                    title="Delete this custom vacancy and its resumes"
                  >
                    <Trash2 className="w-3 h-3" />
                    Delete
                  </button>
                )}
              </div>
            )}
          </div>

          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            {vacancy.title}
          </h1>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-sm text-slate-600">
          <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg">
            <Clock className="w-4 h-4 text-slate-500" />
            <span>Target: <strong>{vacancy.experienceMinYears}–{vacancy.experienceMaxYears} Years</strong></span>
          </div>
          <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg">
            <MapPin className="w-4 h-4 text-slate-500" />
            <span>{vacancy.location}</span>
          </div>
        </div>
      </div>

      <div className="pt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <span className="text-xs font-medium text-slate-500 block mb-2">Required Core Stack</span>
          <div className="flex flex-wrap gap-1.5">
            {vacancy.requiredCoreSkills.map((s) => (
              <span key={s} className="text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200/60 px-2 py-0.5 rounded">
                {s}
              </span>
            ))}
          </div>
        </div>

        <div>
          <span className="text-xs font-medium text-slate-500 block mb-2">Domain & Payments</span>
          <div className="flex flex-wrap gap-1.5">
            {vacancy.requiredDomainSkills.map((s) => (
              <span key={s} className="text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/60 px-2 py-0.5 rounded">
                {s}
              </span>
            ))}
          </div>
        </div>

        <div>
          <span className="text-xs font-medium text-slate-500 block mb-2">DevOps & Cloud</span>
          <div className="flex flex-wrap gap-1.5">
            {vacancy.requiredInfraSkills.map((s) => (
              <span key={s} className="text-xs font-medium bg-purple-50 text-purple-700 border border-purple-200/60 px-2 py-0.5 rounded">
                {s}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
