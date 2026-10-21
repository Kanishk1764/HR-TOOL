import React, { useState, useEffect } from "react";
import { X, Upload, FileText, Briefcase, Plus, CheckCircle, Loader2 } from "lucide-react";
import { VacancyInfo } from "@/lib/types";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  currentVacancy: VacancyInfo | null;
  onResumesUploaded: (count: number) => void;
  onVacancyUpdated: (newVacancy: VacancyInfo) => void;
}

export const HRPortalModal: React.FC<Props> = ({
  isOpen,
  onClose,
  currentVacancy,
  onResumesUploaded,
  onVacancyUpdated,
}) => {
  // All hooks called unconditionally at top of component (Rules of Hooks)
  const [tab, setTab] = useState<"resumes" | "vacancy">("resumes");
  const [isUploading, setIsUploading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [createMode, setCreateMode] = useState<"new" | "edit">("new");

  // Form states for vacancy
  const [title, setTitle] = useState(currentVacancy?.title || "Senior Software Engineer");
  const [minExp, setMinExp] = useState(currentVacancy?.experienceMinYears || 5);
  const [maxExp, setMaxExp] = useState(currentVacancy?.experienceMaxYears || 10);
  const [location, setLocation] = useState(currentVacancy?.location || "Hybrid / Remote");
  const [coreSkills, setCoreSkills] = useState(currentVacancy?.requiredCoreSkills?.join(", ") || "Java, Spring Boot, Microservices");
  const [domainSkills, setDomainSkills] = useState(currentVacancy?.requiredDomainSkills?.join(", ") || "Payment Gateway, Stripe, Razorpay");

  // Sync form when currentVacancy updates
  useEffect(() => {
    if (currentVacancy) {
      setTitle(currentVacancy.title || "Senior Software Engineer");
      setMinExp(currentVacancy.experienceMinYears || 5);
      setMaxExp(currentVacancy.experienceMaxYears || 10);
      setLocation(currentVacancy.location || "Hybrid / Remote");
      setCoreSkills(currentVacancy.requiredCoreSkills?.join(", ") || "Java, Spring Boot, Microservices");
      setDomainSkills(currentVacancy.requiredDomainSkills?.join(", ") || "Payment Gateway, Stripe, Razorpay");
    }
  }, [currentVacancy]);

  // Early return ONLY after all hooks are declared
  if (!isOpen) return null;

  const handleResumeFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const files = Array.from(e.target.files);
    setIsUploading(true);
    setSuccessMessage(null);

    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));

    try {
      const res = await fetch("http://127.0.0.1:8000/api/resumes/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        setSuccessMessage(`Successfully uploaded ${data.uploadedCount} new resume(s)!`);
        onResumesUploaded(data.totalFiles);
      }
    } catch (err: any) {
      alert("Failed to upload resumes: " + err.message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleVacancyFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setIsUploading(true);
    setSuccessMessage(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/vacancy/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (res.ok && data.vacancy) {
        setSuccessMessage(`Loaded vacancy: "${data.vacancy.title}"`);
        onVacancyUpdated(data.vacancy);
      }
    } catch (err: any) {
      alert("Failed to upload vacancy: " + err.message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleCreateVacancyWorkspace = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsUploading(true);
    setSuccessMessage(null);

    const payload = {
      title,
      experienceMinYears: Number(minExp),
      experienceMaxYears: Number(maxExp),
      location,
      requiredCoreSkills: coreSkills.split(",").map((s) => s.trim()).filter(Boolean),
      requiredDomainSkills: domainSkills.split(",").map((s) => s.trim()).filter(Boolean),
      requiredInfraSkills: ["Docker", "Kubernetes", "CI/CD"],
      preferredSkills: ["Kafka", "AWS"],
    };

    try {
      const endpoint =
        createMode === "new"
          ? "http://127.0.0.1:8000/api/vacancies/create"
          : "http://127.0.0.1:8000/api/vacancy/update";

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (res.ok && data.vacancy) {
        if (createMode === "new") {
          setSuccessMessage(`Created isolated workspace for "${data.vacancy.title}". Previous vacancies remain 100% preserved!`);
        } else {
          setSuccessMessage(`Updated vacancy "${data.vacancy.title}" and re-scored candidates!`);
        }
        onVacancyUpdated(data.vacancy);
      }
    } catch (err: any) {
      alert("Failed to save vacancy: " + err.message);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-xl w-full shadow-2xl border border-slate-200 overflow-hidden flex flex-col">
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50/70">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-blue-600" />
              HR Portal & Vacancy Manager
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Upload resumes in batch or create a new isolated job vacancy workspace.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-slate-200 px-5 pt-2 text-xs font-semibold">
          <button
            onClick={() => {
              setTab("resumes");
              setSuccessMessage(null);
            }}
            className={`px-4 py-2.5 border-b-2 transition-all cursor-pointer ${
              tab === "resumes"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            Upload Resumes (Batch)
          </button>
          <button
            onClick={() => {
              setTab("vacancy");
              setSuccessMessage(null);
            }}
            className={`px-4 py-2.5 border-b-2 transition-all cursor-pointer ${
              tab === "vacancy"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            New Job Vacancy / JD
          </button>
        </div>

        {/* Success Banner */}
        {successMessage && (
          <div className="mx-5 mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs flex items-center gap-2">
            <CheckCircle className="w-4 h-4 shrink-0" />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Modal Body */}
        <div className="p-5 text-xs">
          {tab === "resumes" ? (
            <div className="space-y-4">
              <div className="border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-xl p-8 text-center transition-colors bg-slate-50/50">
                <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <h4 className="font-bold text-slate-800 mb-1">Upload Multiple Resumes</h4>
                <p className="text-slate-500 text-[11px] mb-4">
                  Select one or more PDF or DOCX files to add to the active vacancy pool.
                </p>
                <label className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold px-4 py-2 rounded-lg cursor-pointer transition-all shadow-sm">
                  {isUploading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" /> Uploading...
                    </>
                  ) : (
                    <>
                      <Plus className="w-3.5 h-3.5" /> Choose Resume Files
                    </>
                  )}
                  <input
                    type="file"
                    multiple
                    accept=".pdf,.docx,.txt"
                    onChange={handleResumeFileUpload}
                    className="hidden"
                    disabled={isUploading}
                  />
                </label>
              </div>

              <div className="text-[11px] text-slate-500 space-y-1 bg-slate-100/60 p-3 rounded-lg border border-slate-200">
                <p><strong>Compliance & Safety:</strong></p>
                <p>• Files are processed locally on your server without external profile scraping.</p>
                <p>• Reruns are safe and deduplicated by document ID automatically.</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Option A: Upload JD File */}
              <div className="border border-slate-200 rounded-lg p-3.5 bg-slate-50 flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-slate-800 text-xs">Upload Vacancy File (.txt / .json)</h4>
                  <p className="text-slate-500 text-[11px]">Automatically parses requirements and updates Knowledge Graph</p>
                </div>
                <label className="bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 font-semibold px-3 py-1.5 rounded-lg cursor-pointer text-xs transition-colors">
                  Choose File
                  <input
                    type="file"
                    accept=".txt,.json"
                    onChange={handleVacancyFileUpload}
                    className="hidden"
                    disabled={isUploading}
                  />
                </label>
              </div>

              <div className="text-center text-slate-400 text-[11px] font-semibold uppercase tracking-wider">
                — OR CONFIGURE DIRECTLY —
              </div>

              {/* Option B: Direct form */}
              <form onSubmit={handleCreateVacancyWorkspace} className="space-y-3">
                {/* Mode Selector */}
                <div className="flex items-center gap-3 bg-blue-50/70 p-2.5 rounded-lg border border-blue-200 text-xs">
                  <label className="flex items-center gap-1.5 cursor-pointer font-medium text-slate-800">
                    <input
                      type="radio"
                      name="vacancyMode"
                      value="new"
                      checked={createMode === "new"}
                      onChange={() => setCreateMode("new")}
                      className="accent-blue-600"
                    />
                    <span><strong>Create New Vacancy</strong> (Isolated Workspace)</span>
                  </label>
                  <label className="flex items-center gap-1.5 cursor-pointer font-medium text-slate-800">
                    <input
                      type="radio"
                      name="vacancyMode"
                      value="edit"
                      checked={createMode === "edit"}
                      onChange={() => setCreateMode("edit")}
                      className="accent-blue-600"
                    />
                    <span>Update Current</span>
                  </label>
                </div>

                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Job Title / Vacancy Name</label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    required
                    className="w-full border border-slate-300 rounded-lg px-3 py-1.5 text-xs focus:ring-1 focus:ring-blue-500 outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-700 font-semibold mb-1">Min Experience (Years)</label>
                    <input
                      type="number"
                      value={minExp}
                      onChange={(e) => setMinExp(Number(e.target.value))}
                      className="w-full border border-slate-300 rounded-lg px-3 py-1.5 text-xs outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-semibold mb-1">Location</label>
                    <input
                      type="text"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      className="w-full border border-slate-300 rounded-lg px-3 py-1.5 text-xs outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Required Core Skills (comma separated)</label>
                  <input
                    type="text"
                    value={coreSkills}
                    onChange={(e) => setCoreSkills(e.target.value)}
                    placeholder="e.g. Java, Spring Boot, Microservices, REST API"
                    className="w-full border border-slate-300 rounded-lg px-3 py-1.5 text-xs outline-none"
                  />
                </div>

                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Domain Skills (comma separated)</label>
                  <input
                    type="text"
                    value={domainSkills}
                    onChange={(e) => setDomainSkills(e.target.value)}
                    placeholder="e.g. Payment Gateway, Razorpay, Stripe"
                    className="w-full border border-slate-300 rounded-lg px-3 py-1.5 text-xs outline-none"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isUploading}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-lg transition-colors mt-2 cursor-pointer shadow-sm"
                >
                  {isUploading
                    ? "Processing..."
                    : createMode === "new"
                    ? "✨ Create New Vacancy Workspace (Preserve Previous)"
                    : "Update Active Vacancy & Re-score"}
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
