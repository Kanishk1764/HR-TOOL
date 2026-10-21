"use client";

import React, { useEffect, useState } from "react";
import { VacancyHeader } from "@/components/VacancyHeader";
import { BatchControlBar } from "@/components/BatchControlBar";
import { KnowledgeGraphCard } from "@/components/KnowledgeGraphCard";
import { CandidateTable } from "@/components/CandidateTable";
import { TraceabilityDrawer } from "@/components/TraceabilityDrawer";
import { HRPortalModal } from "@/components/HRPortalModal";
import {
  fetchVacancy,
  fetchCandidates,
  fetchKnowledgeGraph,
  toggleProxyRule,
  fetchResumeStatus,
  triggerBatchProcess,
  fetchVacancies,
  selectVacancy,
  deleteVacancy,
} from "@/lib/api";
import { VacancyInfo, VacancySummary, Candidate, SkillProxyRule } from "@/lib/types";
import { Sparkles, Layers, RefreshCw, Cpu, CheckCircle, Upload, Plus } from "lucide-react";

export default function Home() {
  const [vacancy, setVacancy] = useState<VacancyInfo | null>(null);
  const [vacancies, setVacancies] = useState<VacancySummary[]>([]);
  const [activeVacancyId, setActiveVacancyId] = useState<string>("");
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [proxies, setProxies] = useState<SkillProxyRule[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [isHRModalOpen, setIsHRModalOpen] = useState<boolean>(false);

  const [totalFiles, setTotalFiles] = useState<number>(50);
  const [selectedLimit, setSelectedLimit] = useState<number | null>(10); // Default to fixed 10 resumes
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isLlmOnline, setIsLlmOnline] = useState<boolean>(false);
  const [llmModel, setLlmModel] = useState<string>("gpt-5.6-luna");

  // Initial load
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setErrorMsg(null);
      const [vData, vacList, cData, kgData, sData] = await Promise.all([
        fetchVacancy().catch(() => null),
        fetchVacancies().catch(() => []),
        fetchCandidates().catch(() => []),
        fetchKnowledgeGraph().catch(() => []),
        fetchResumeStatus().catch(() => ({ totalFiles: 50, parsedCount: 0, isLlmOnline: false, llmModel: "gpt-5.6-luna", activeVacancyId: "" })),
      ]);

      if (vData) setVacancy(vData);
      if (vacList && vacList.length > 0) setVacancies(vacList);
      if (cData) setCandidates(cData);
      if (kgData) setProxies(kgData);
      if (sData) {
        setTotalFiles(sData.totalFiles || 50);
        setIsLlmOnline(Boolean(sData.isLlmOnline));
        if (sData.llmModel) setLlmModel(sData.llmModel);
        if (sData.activeVacancyId) setActiveVacancyId(sData.activeVacancyId);
      }
    } catch (err: any) {
      setErrorMsg("Failed to connect to the backend API. Please make sure FastAPI backend is running.");
    }
  };

  const handleSelectVacancy = async (id: string) => {
    try {
      setErrorMsg(null);
      const res = await selectVacancy(id);
      if (res.vacancy) {
        setVacancy(res.vacancy);
        setActiveVacancyId(id);
      }
      if (res.candidates) {
        setCandidates(res.candidates);
      }
      if (res.totalFiles !== undefined) {
        setTotalFiles(res.totalFiles);
      }
      // Refresh vacancies list to update counts
      const updatedList = await fetchVacancies().catch(() => []);
      if (updatedList.length > 0) setVacancies(updatedList);
    } catch (err: any) {
      setErrorMsg("Failed to switch vacancy workspace: " + err.message);
    }
  };

  const handleDeleteVacancy = async (id: string) => {
    const vacToDelete = vacancies.find((v) => v.id === id);
    const confirmed = window.confirm(
      `Are you sure you want to delete vacancy "${vacToDelete?.title || id}"? All uploaded resumes and candidate scores for this vacancy will be removed.`
    );
    if (!confirmed) return;

    try {
      setErrorMsg(null);
      const res = await deleteVacancy(id);
      if (res.activeVacancy) setVacancy(res.activeVacancy);
      if (res.vacancies) setVacancies(res.vacancies);
      if (res.candidates) setCandidates(res.candidates);
      if (res.totalFiles !== undefined) setTotalFiles(res.totalFiles);
      if (res.activeVacancy?.id) setActiveVacancyId(res.activeVacancy.id);
      await loadData();
    } catch (err: any) {
      setErrorMsg("Failed to delete vacancy: " + (err.message || String(err)));
    }
  };

  const handleStartProcess = async () => {
    try {
      setIsProcessing(true);
      setErrorMsg(null);
      const res = await triggerBatchProcess(selectedLimit);
      if (res && res.results) {
        setCandidates(res.results);
      }
      await loadData();
    } catch (err: any) {
      setErrorMsg("Batch processing encountered an issue: " + (err.message || String(err)));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleToggleProxy = async (targetSkill: string, proxySkill: string, current: boolean) => {
    try {
      const res = await toggleProxyRule(targetSkill, proxySkill, !current);
      if (res.proxies) setProxies(res.proxies);
      if (res.candidates) {
        setCandidates(res.candidates);
        if (selectedCandidate) {
          const updated = res.candidates.find((c: Candidate) => c.documentId === selectedCandidate.documentId);
          if (updated) setSelectedCandidate(updated);
        }
      } else {
        const cData = await fetchCandidates();
        setCandidates(cData);
      }
    } catch (err: any) {
      console.error("Failed to toggle proxy:", err);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50/70 p-4 md:p-8 max-w-7xl mx-auto">
      {/* Top Navbar */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-200">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-slate-900 text-white flex items-center justify-center font-bold text-base shadow-sm">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
              Resume Intelligence & Vacancy Auditor
              <span className="text-[10px] font-semibold bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full uppercase tracking-wider">
                Precision Pipeline
              </span>
            </h1>
            <p className="text-xs text-slate-500">
              Deterministic Interval Math • Fact Extraction • JD Knowledge Graph • Anti-Hallucination
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* AI Connection Status Badge */}
          <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold ${
            isLlmOnline
              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
              : "bg-amber-50 text-amber-800 border-amber-200"
          }`}>
            <span className={`w-2 h-2 rounded-full ${isLlmOnline ? "bg-emerald-500 animate-pulse" : "bg-amber-500"}`} />
            <Cpu className="w-3.5 h-3.5" />
            <span>{isLlmOnline ? `AI Online: ${llmModel}` : "Local Fallback (No Key)"}</span>
          </div>

          <button
            onClick={() => setIsHRModalOpen(true)}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 px-3.5 py-1.5 rounded-lg shadow-sm transition-colors cursor-pointer"
          >
            <Upload className="w-3.5 h-3.5" />
            HR Portal / Upload
          </button>

          <button
            onClick={loadData}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white border border-slate-200 px-3 py-1.5 rounded-lg shadow-2xs hover:bg-slate-50 transition-colors cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>
      </header>

      {/* Error Banner if any */}
      {errorMsg && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center justify-between">
          <span>{errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="font-bold ml-4">✕</button>
        </div>
      )}

      {/* Vacancy Header Card with Isolated Multi-Vacancy Switcher */}
      <VacancyHeader
        vacancy={vacancy}
        vacancies={vacancies}
        activeVacancyId={activeVacancyId}
        onSelectVacancy={handleSelectVacancy}
        onOpenCreateVacancy={() => setIsHRModalOpen(true)}
        onDeleteVacancy={handleDeleteVacancy}
      />

      {/* Batch Processing & Cost Control Bar */}
      <BatchControlBar
        totalAvailable={totalFiles}
        parsedCount={candidates.length}
        isProcessing={isProcessing}
        selectedLimit={selectedLimit}
        onSelectLimit={setSelectedLimit}
        onStartProcess={handleStartProcess}
      />

      {/* JD Knowledge Graph Toggles */}
      <KnowledgeGraphCard
        proxies={proxies}
        onToggleProxy={handleToggleProxy}
      />

      {/* Candidates Table */}
      <CandidateTable
        candidates={candidates}
        onSelectCandidate={setSelectedCandidate}
      />

      {/* Traceability Audit Drawer */}
      <TraceabilityDrawer
        candidate={selectedCandidate}
        onClose={() => setSelectedCandidate(null)}
      />

      {/* HR Portal Modal */}
      <HRPortalModal
        isOpen={isHRModalOpen}
        onClose={() => setIsHRModalOpen(false)}
        currentVacancy={vacancy}
        onResumesUploaded={(count) => {
          setTotalFiles(count);
          loadData();
        }}
        onVacancyUpdated={(newVac) => {
          setVacancy(newVac);
          loadData();
        }}
      />
    </main>
  );
}
