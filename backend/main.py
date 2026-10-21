import os
import sys
import json
from typing import List, Dict, Any, Optional

# Ensure project root is in sys.path so backend imports work regardless of cwd
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Load .env variables (with zero-dependency fallback if python-dotenv is not installed)
for env_path in [os.path.join(root_dir, ".env"), os.path.join(root_dir, "backend", ".env")]:
    if os.path.exists(env_path):
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
        except ImportError:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip().strip("'\""))

from fastapi import FastAPI, Query, HTTPException, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from backend.app.llm.batch_worker import BatchProcessingPipeline, OUTPUT_DIR, RESUMES_DIR
from backend.app.models.schemas import ResumeResult
from backend.app.parsers.vacancy_parser import parse_vacancy_file
from backend.app.managers.vacancy_manager import VacancyManager, DEFAULT_JAVA_VACANCY_ID

app = FastAPI(
    title="Resume Data Extraction & Vacancy Matcher API",
    description="Precision factual resume parser and skill interval auditor with Multi-Vacancy Workspace Isolation",
    version="1.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vacancy_manager = VacancyManager()
pipeline = BatchProcessingPipeline(
    resumes_dir=vacancy_manager.get_active_vacancy_dir(),
    output_dir=vacancy_manager.get_active_output_dir(),
    vacancy_info=vacancy_manager.get_active_vacancy_info()
)
cached_results: List[ResumeResult] = []

class ToggleProxyRequest(BaseModel):
    targetSkill: str
    proxySkill: str
    isEnabled: bool

class ProcessRequest(BaseModel):
    limit: Optional[int] = 10  # Default 10 fixed resumes (cost control)
    batchSize: int = 5
    asOfDate: str = "2026-10-21"

class SelectVacancyRequest(BaseModel):
    vacancyId: str

class CreateVacancyRequest(BaseModel):
    title: str
    experienceMinYears: int = 3
    experienceMaxYears: int = 8
    location: str = "Hybrid / Remote"
    requiredCoreSkills: List[str] = []
    requiredDomainSkills: List[str] = []
    requiredInfraSkills: List[str] = []
    preferredSkills: List[str] = []
    jdText: Optional[str] = None

@app.get("/api/vacancies")
def list_vacancies():
    """Lists all isolated vacancy workspaces with resume and parsed counts."""
    return vacancy_manager.list_vacancies()

@app.post("/api/vacancies/select")
def select_vacancy(req: SelectVacancyRequest):
    """Switches active vacancy without overwriting or losing previous vacancy records."""
    global cached_results
    new_vac = vacancy_manager.switch_active_vacancy(req.vacancyId)
    pipeline.set_active_scope(
        resumes_dir=vacancy_manager.get_active_vacancy_dir(),
        output_dir=vacancy_manager.get_active_output_dir(),
        vacancy_info=new_vac
    )
    cached_results = []
    # Load candidates for this switched vacancy
    candidates = get_candidates()
    return {
        "status": "success",
        "vacancy": new_vac,
        "candidates": candidates,
        "totalFiles": len(pipeline.get_available_resume_files())
    }

@app.post("/api/vacancies/create")
def create_vacancy(req: CreateVacancyRequest):
    """Creates a new isolated vacancy workspace. All existing vacancies remain 100% untouched."""
    global cached_results
    new_vac = vacancy_manager.create_vacancy(
        title=req.title,
        min_exp=req.experienceMinYears,
        max_exp=req.experienceMaxYears,
        location=req.location,
        core_skills=req.requiredCoreSkills,
        domain_skills=req.requiredDomainSkills,
        infra_skills=req.requiredInfraSkills,
        preferred_skills=req.preferredSkills,
        jd_text=req.jdText
    )
    pipeline.set_active_scope(
        resumes_dir=vacancy_manager.get_active_vacancy_dir(),
        output_dir=vacancy_manager.get_active_output_dir(),
        vacancy_info=new_vac
    )
    cached_results = []
    return {
        "status": "success",
        "vacancy": new_vac,
        "vacancies": vacancy_manager.list_vacancies()
    }

@app.delete("/api/vacancies/{vacancy_id}")
def delete_vacancy(vacancy_id: str):
    """Deletes an isolated vacancy workspace. Baseline Java benchmark is protected."""
    global cached_results
    try:
        res = vacancy_manager.delete_vacancy(vacancy_id)
        # Update pipeline scope to the new active vacancy
        pipeline.set_active_scope(
            resumes_dir=vacancy_manager.get_active_vacancy_dir(),
            output_dir=vacancy_manager.get_active_output_dir(),
            vacancy_info=res["activeVacancy"]
        )
        cached_results = []
        candidates = get_candidates()
        return {
            "status": "success",
            "message": f"Vacancy workspace deleted successfully",
            "deletedId": vacancy_id,
            "activeVacancy": res["activeVacancy"],
            "vacancies": res["vacancies"],
            "candidates": candidates,
            "totalFiles": len(pipeline.get_available_resume_files())
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "activeVacancyId": vacancy_manager.active_vacancy_id,
        "llmModel": pipeline.llm_client.model,
        "isLlmOnline": pipeline.llm_client.is_available(),
        "availableResumesCount": len(pipeline.get_available_resume_files())
    }

@app.get("/api/vacancy")
def get_vacancy():
    return pipeline.vacancy_info

class VacancyUpdateRequest(BaseModel):
    title: str
    experienceMinYears: int = 5
    experienceMaxYears: int = 10
    location: str = "Hybrid / Remote"
    requiredCoreSkills: List[str]
    requiredDomainSkills: List[str] = []
    requiredInfraSkills: List[str] = []
    preferredSkills: List[str] = []

@app.post("/api/vacancy/update")
def update_vacancy(req: VacancyUpdateRequest):
    """Updates the vacancy specification and re-evaluates all candidates against the new requirements."""
    pipeline.vacancy_info = req.model_dump()
    vacancy_manager.save_vacancy_info(pipeline.vacancy_info)
    
    global cached_results
    if not cached_results:
        cached_results = get_candidates()

    for r in cached_results:
        summaries_dict = {s.skill: s for s in r.skillSummary}
        from backend.app.engine.scoring_engine import match_candidate_to_vacancy
        r.vacancyMatch = match_candidate_to_vacancy(
            summaries_dict, r.skillClaims, pipeline.vacancy_info, pipeline.kg_engine
        )
    if cached_results:
        pipeline.export_results(cached_results)

    return {
        "status": "success",
        "vacancy": pipeline.vacancy_info,
        "candidates": cached_results
    }

@app.post("/api/vacancy/upload")
async def upload_vacancy_file(file: UploadFile = File(...)):
    """Uploads a new vacancy file (txt), parses it, and re-scores candidates in the current workspace."""
    temp_path = os.path.join(pipeline.output_dir, f"temp_{file.filename}")
    with open(temp_path, "wb") as out:
        content = await file.read()
        out.write(content)
    
    parsed_vac = parse_vacancy_file(temp_path)
    pipeline.vacancy_info = parsed_vac
    vacancy_manager.save_vacancy_info(pipeline.vacancy_info)

    global cached_results
    if not cached_results:
        cached_results = get_candidates()

    for r in cached_results:
        summaries_dict = {s.skill: s for s in r.skillSummary}
        from backend.app.engine.scoring_engine import match_candidate_to_vacancy
        r.vacancyMatch = match_candidate_to_vacancy(
            summaries_dict, r.skillClaims, pipeline.vacancy_info, pipeline.kg_engine
        )
    if cached_results:
        pipeline.export_results(cached_results)

    return {
        "status": "success",
        "vacancy": pipeline.vacancy_info,
        "candidates": cached_results
    }

@app.post("/api/resumes/upload")
async def upload_resumes(files: List[UploadFile] = File(...)):
    """Uploads more resume files directly to the active vacancy folder."""
    target_dir = pipeline.resumes_dir
    os.makedirs(target_dir, exist_ok=True)
    saved_files = []
    for f in files:
        if f.filename:
            target_path = os.path.join(target_dir, f.filename)
            with open(target_path, "wb") as out:
                content = await f.read()
                out.write(content)
            saved_files.append(f.filename)

    return {
        "status": "success",
        "uploadedCount": len(saved_files),
        "totalFiles": len(pipeline.get_available_resume_files()),
        "savedFiles": saved_files
    }

@app.get("/api/knowledge-graph")
def get_knowledge_graph():
    return pipeline.kg_engine.proxies

@app.post("/api/knowledge-graph/toggle")
def toggle_knowledge_graph_proxy(req: ToggleProxyRequest):
    pipeline.kg_engine.update_proxy_state(req.targetSkill, req.proxySkill, req.isEnabled)
    global cached_results
    if not cached_results:
        cached_results = get_candidates()

    for r in cached_results:
        summaries_dict = {s.skill: s for s in r.skillSummary}
        from backend.app.engine.scoring_engine import match_candidate_to_vacancy
        r.vacancyMatch = match_candidate_to_vacancy(
            summaries_dict, r.skillClaims, pipeline.vacancy_info, pipeline.kg_engine
        )
    
    # Save back to results.jsonl and skills.csv so Refresh retains updated scores!
    if cached_results:
        pipeline.export_results(cached_results)

    return {
        "status": "success",
        "proxies": pipeline.kg_engine.proxies,
        "candidates": cached_results
    }

@app.get("/api/resumes/status")
def get_resumes_status():
    files = pipeline.get_available_resume_files()
    local_jsonl = os.path.join(pipeline.output_dir, "results.jsonl")
    parsed_count = len(cached_results)
    if parsed_count == 0 and os.path.exists(local_jsonl):
        try:
            with open(local_jsonl, "r", encoding="utf-8") as f:
                parsed_count = sum(1 for line in f if line.strip())
        except Exception:
            parsed_count = 0

    return {
        "totalFiles": len(files),
        "defaultLimit": 10,
        "currentProgress": pipeline.current_progress,
        "parsedCount": parsed_count,
        "isLlmOnline": pipeline.llm_client.is_available(),
        "llmModel": pipeline.llm_client.model,
        "activeVacancyId": vacancy_manager.active_vacancy_id
    }

@app.post("/api/resumes/process")
def process_resumes_batch(req: ProcessRequest = Body(...)):
    global cached_results
    cached_results = pipeline.process_resumes(
        limit=req.limit,
        batch_size=req.batchSize,
        as_of_date=req.asOfDate
    )
    return {
        "status": "completed",
        "processedCount": len(cached_results),
        "results": cached_results
    }

@app.get("/api/candidates")
def get_candidates():
    global cached_results
    if not cached_results:
        # Check active vacancy's isolated results.jsonl
        jsonl_path = os.path.join(pipeline.output_dir, "results.jsonl")
        if not os.path.exists(jsonl_path) and vacancy_manager.active_vacancy_id == DEFAULT_JAVA_VACANCY_ID:
            jsonl_path = os.path.join(OUTPUT_DIR, "results.jsonl")

        if os.path.exists(jsonl_path):
            cached_results = []
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        r = ResumeResult(**json.loads(line))
                        summaries_dict = {s.skill: s for s in r.skillSummary}
                        from backend.app.engine.scoring_engine import match_candidate_to_vacancy
                        r.vacancyMatch = match_candidate_to_vacancy(
                            summaries_dict, r.skillClaims, pipeline.vacancy_info, pipeline.kg_engine
                        )
                        cached_results.append(r)
    return cached_results

@app.get("/api/export/jsonl")
def export_jsonl():
    file_path = os.path.join(pipeline.output_dir, "results.jsonl")
    if not os.path.exists(file_path):
        file_path = os.path.join(OUTPUT_DIR, "results.jsonl")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="results.jsonl not generated yet. Run batch process first.")
    return FileResponse(file_path, filename="results.jsonl", media_type="application/x-jsonlines")

@app.get("/api/export/csv")
def export_csv():
    file_path = os.path.join(pipeline.output_dir, "skills.csv")
    if not os.path.exists(file_path):
        file_path = os.path.join(OUTPUT_DIR, "skills.csv")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="skills.csv not generated yet. Run batch process first.")
    return FileResponse(file_path, filename="skills.csv", media_type="text/csv")

@app.get("/api/report")
def get_validation_report():
    global cached_results
    if not cached_results:
        return {"error": "No candidates processed yet"}

    total = len(cached_results)
    success_count = sum(1 for r in cached_results if r.parseStatus == "success")
    partial_count = sum(1 for r in cached_results if r.parseStatus == "partial")
    failed_count = sum(1 for r in cached_results if r.parseStatus == "failed")

    has_projects_count = sum(1 for r in cached_results if len(r.projects) > 0)
    has_dated_skills_count = sum(
        1 for r in cached_results if any(s.durationStatus == "dated" for s in r.skillSummary)
    )
    meets_java_req_count = sum(
        1 for r in cached_results if r.vacancyMatch and r.vacancyMatch.meetsJavaExperience
    )

    return {
        "totalEvaluated": total,
        "parseStatusSummary": {
            "success": success_count,
            "partial": partial_count,
            "failed": failed_count,
            "successRatePercent": round((success_count / total) * 100, 1)
        },
        "metrics": {
            "percentWithProjects": round((has_projects_count / total) * 100, 1),
            "percentWithDatedSkillUse": round((has_dated_skills_count / total) * 100, 1),
            "percentMeetingJava5Years": round((meets_java_req_count / total) * 100, 1)
        },
        "asOfDate": "2026-10-21",
        "roleEvaluated": pipeline.vacancy_info.get("title")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
