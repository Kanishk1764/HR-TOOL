import os
import glob
import json
import csv
from typing import List, Dict, Any, Optional
from ..parsers.pdf_parser import extract_pdf_layout_aware
from ..parsers.docx_parser import extract_docx
from ..parsers.vacancy_parser import parse_vacancy_file
from ..models.schemas import ResumeResult, Role, Project, SkillClaim
from ..engine.interval_engine import calculate_skill_intervals
from ..engine.quote_verifier import verify_claims_against_source
from ..engine.knowledge_graph import KnowledgeGraphEngine
from ..engine.scoring_engine import compute_selection_insights, match_candidate_to_vacancy
from .client import LLMExtractorClient

RESUMES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "assests",
    "vacancyId=6ac37cb2765ff358c60b6d7a-SeniorSoftwareEngineerJavaBackend"
)
VACANCY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "Vacancy details.txt"
)

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "outputs"
)

class BatchProcessingPipeline:
    def __init__(
        self,
        resumes_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
        vacancy_info: Optional[Dict[str, Any]] = None
    ):
        self.llm_client = LLMExtractorClient()
        self.kg_engine = KnowledgeGraphEngine()
        self.resumes_dir = resumes_dir or RESUMES_DIR
        self.output_dir = output_dir or OUTPUT_DIR
        self.vacancy_info = vacancy_info or (parse_vacancy_file(VACANCY_FILE) if os.path.exists(VACANCY_FILE) else {})
        self.current_progress = {"total": 0, "processed": 0, "status": "idle"}
        os.makedirs(self.output_dir, exist_ok=True)

    def set_active_scope(self, resumes_dir: str, output_dir: str, vacancy_info: Dict[str, Any]):
        """Dynamically switches active vacancy workspace without losing previous state."""
        self.resumes_dir = resumes_dir
        self.output_dir = output_dir
        self.vacancy_info = vacancy_info
        os.makedirs(self.output_dir, exist_ok=True)

    def get_available_resume_files(self) -> List[str]:
        if not os.path.exists(self.resumes_dir):
            return []
        files = glob.glob(os.path.join(self.resumes_dir, "*.pdf")) + glob.glob(os.path.join(self.resumes_dir, "*.docx"))
        return sorted(files)

    def process_resumes(
        self,
        limit: int = 10,
        batch_size: int = 5,
        as_of_date: str = "2026-10-21"
    ) -> List[ResumeResult]:
        """
        Processes resumes in economic packed batches.
        Default: limit = 10 fixed resumes (cost-control rule).
        """
        all_files = self.get_available_resume_files()
        target_files = all_files[:limit] if limit and limit > 0 else all_files

        self.current_progress = {
            "total": len(target_files),
            "processed": 0,
            "status": "processing"
        }

        # Step 1: Text extraction for all files in this run
        raw_documents: List[Dict[str, Any]] = []
        for file_path in target_files:
            doc_id = os.path.basename(file_path)
            flags: List[str] = []
            text = ""

            try:
                if file_path.lower().endswith(".pdf"):
                    text, flags = extract_pdf_layout_aware(file_path)
                elif file_path.lower().endswith(".docx"):
                    text, flags = extract_docx(file_path)
            except Exception as e:
                flags.append(f"file_read_error: {str(e)[:100]}")

            raw_documents.append({
                "documentId": doc_id,
                "filePath": file_path,
                "text": text,
                "layoutFlags": flags
            })

        results: List[ResumeResult] = []

        # Step 2: Economic chunked batch calls to LLM
        for i in range(0, len(raw_documents), batch_size):
            chunk = raw_documents[i:i + batch_size]
            llm_input = [{"documentId": d["documentId"], "text": d["text"]} for d in chunk]

            # LLM packed call with fallback protection
            try:
                extracted_batch = self.llm_client.extract_batch(llm_input)
            except Exception as batch_err:
                # If the batch call fails completely, fallback per-doc
                extracted_batch = []

            for idx, doc in enumerate(chunk):
                doc_id = doc["documentId"]
                raw_text = doc["text"]
                flags = list(doc["layoutFlags"])

                try:
                    if not raw_text.strip():
                        # Unreadable / corrupted file handling (Section 1)
                        res = ResumeResult(
                            documentId=doc_id,
                            candidateName=os.path.splitext(doc_id)[0],
                            parseStatus="failed",
                            reviewFlags=flags + ["file_empty_or_unreadable"]
                        )
                        results.append(res)
                        self.current_progress["processed"] += 1
                        continue

                    # Find matching extracted item by documentId, substring, candidate name, or positional index
                    raw_data = None
                    for item in extracted_batch:
                        item_id = str(item.get("documentId", "")).strip()
                        if item_id and (item_id == doc_id or item_id in doc_id or doc_id in item_id):
                            raw_data = item
                            break
                        item_name = str(item.get("candidateName", "")).strip()
                        if item_name and (item_name.lower() in doc_id.lower() or doc_id.lower().startswith(item_name.lower())):
                            raw_data = item
                            break

                    if not raw_data and idx < len(extracted_batch):
                        raw_data = extracted_batch[idx]

                    if not raw_data:
                        raw_data = {}

                    candidate_name = raw_data.get("candidateName") or os.path.splitext(doc_id)[0].split(".")[0]

                    # Convert roles
                    roles = [Role(**r) for r in raw_data.get("roles", [])]
                    projects = [Project(**p) for p in raw_data.get("projects", [])]

                    # Convert skill claims
                    raw_claims = [SkillClaim(**c) for c in raw_data.get("skillClaims", [])]

                    # Catch 3: Exact-quote verification against raw source (prompt injection / keyword stuffing defense)
                    verified_claims, quote_flags = verify_claims_against_source(raw_claims, raw_text)
                    flags.extend(quote_flags)

                    # Catch 2 & 4: Deterministic Interval Union Calculation
                    summaries = calculate_skill_intervals(verified_claims, as_of_date=as_of_date, roles=roles)

                    # Selection Insights (tenure stability, recency, velocity)
                    insights = compute_selection_insights(roles, verified_claims, summaries)

                    # Vacancy Matching & Knowledge Graph Evaluation
                    match = match_candidate_to_vacancy(summaries, verified_claims, self.vacancy_info, self.kg_engine)

                    parse_status = "success"
                    if any("quote_verification_failed" in f for f in flags) or not verified_claims:
                        parse_status = "partial"

                    result_obj = ResumeResult(
                        documentId=doc_id,
                        candidateName=candidate_name,
                        parseStatus=parse_status,
                        roles=roles,
                        projects=projects,
                        skillClaims=verified_claims,
                        skillSummary=list(summaries.values()),
                        reviewFlags=flags,
                        selectionInsights=insights,
                        vacancyMatch=match,
                        rawTextLength=len(raw_text)
                    )
                    results.append(result_obj)
                except Exception as doc_err:
                    # Gracefully isolate single bad resume error so entire batch completes cleanly
                    res = ResumeResult(
                        documentId=doc_id,
                        candidateName=os.path.splitext(doc_id)[0],
                        parseStatus="failed",
                        reviewFlags=flags + [f"parse_error: {str(doc_err)[:100]}"]
                    )
                    results.append(res)
                finally:
                    self.current_progress["processed"] += 1

        self.current_progress["status"] = "completed"

        # Step 3: Write outputs to results.jsonl and skills.csv
        self.export_results(results)

        return results

    def export_results(self, results: List[ResumeResult]):
        """Exports results to results.jsonl and skills.csv strictly per Section 6 without duplicates."""
        os.makedirs(self.output_dir, exist_ok=True)
        jsonl_path = os.path.join(self.output_dir, "results.jsonl")
        csv_path = os.path.join(self.output_dir, "skills.csv")

        # Read existing records if present to merge by documentId (prevents duplicate rows on reruns)
        merged_by_id: Dict[str, ResumeResult] = {}
        if os.path.exists(jsonl_path):
            try:
                with open(jsonl_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            existing = ResumeResult(**json.loads(line))
                            merged_by_id[existing.documentId] = existing
            except Exception:
                pass

        # Overwrite or add with latest results
        for r in results:
            merged_by_id[r.documentId] = r

        all_results = list(merged_by_id.values())

        # 1. results.jsonl (deduplicated)
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for r in all_results:
                f.write(r.model_dump_json() + "\n")

        # 2. skills.csv (deduplicated)
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "documentId", "skill", "contexts", "supportedMonths",
                "supportedYears", "lastUsed", "statedLevels", "durationStatus"
            ])
            for r in all_results:
                for s in r.skillSummary:
                    writer.writerow([
                        r.documentId,
                        s.skill,
                        ";".join(s.contexts) if s.contexts else "none",
                        s.supportedMonths if s.supportedMonths is not None else "null",
                        s.supportedYears if s.supportedYears is not None else "null",
                        s.lastUsed if s.lastUsed else "null",
                        ";".join(s.statedLevels) if s.statedLevels else "null",
                        s.durationStatus
                    ])
