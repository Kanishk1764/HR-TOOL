import os
import sys
import re
import glob
import json
import time
import hashlib
import logging
import contextlib
import csv
import platform
from typing import List, Dict, Any, Tuple
from openai import OpenAI
import pdfplumber
import pymupdf
import docx

logging.getLogger("pdfminer").setLevel(logging.ERROR)

BASE_DIR = r"c:\Users\Cog\Desktop\HR TASK"
RESUMES1_DIR = os.path.join(BASE_DIR, "assests", "resumes1")
RESUMES2_DIR = os.path.join(BASE_DIR, "assests", "resumes2")
OUTPUT_DIR = os.path.join(BASE_DIR, "batch_outputs")
TRACES_DIR = os.path.join(OUTPUT_DIR, "stage_traces")

CHECKPOINT_FILE = os.path.join(OUTPUT_DIR, "checkpoint_results.jsonl")
FINAL_JSON_FILE = os.path.join(OUTPUT_DIR, "final_all_candidates.json")
SUMMARY_CSV_FILE = os.path.join(OUTPUT_DIR, "skills_overview.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TRACES_DIR, exist_ok=True)

# 1. Environment & OpenAI Client Setup
for env_path in [os.path.join(BASE_DIR, ".env"), os.path.join(BASE_DIR, "backend", ".env")]:
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("'\"")

api_key = os.getenv("OPENAI_API_KEY", "")
base_url = os.getenv("OPENAI_BASE_URL", None)
model_name = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

client = OpenAI(api_key=api_key, base_url=base_url)

# 2. Regular Expressions & Section Boundaries
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

WORK_EXP_HEADERS = re.compile(
    r'(?:^|\n)[^\S\r\n]*(?:[0-9IVX]+\.\s*)?(?:[A-Za-z/&\s]+\s+)?(?:WORK\s+EXPERIENCE|PROFESSIONAL\s+EXPERIENCE|EMPLOYMENT\s+HISTORY|EXPERIENCE|EXPERINCE|HISTORY)\s*[:\-\|]?[^\S\r\n]*(?:\s*\n|\s*$)',
    re.IGNORECASE
)
INLINE_WORK_EXP_HEADERS = re.compile(
    r'\b(?:WORK\s+EXPERIENCE|PROFESSIONAL\s+EXPERIENCE|EMPLOYMENT\s+HISTORY)\b',
    re.IGNORECASE
)

# Crucial Architectural Rule:
# Generic 'PROJECTS' is REMOVED from terminators to prevent cutting off nested client projects.
# Only unambiguous non-work boundaries terminate the work experience section.
COARSE_WORK_EXP_TERMINATORS = re.compile(
    r'(?:^|\n)[^\S\r\n]*(?:[0-9IVX]+\.\s*)?'
    r'(?:EDUCATION|ACADEMIC\s+BACKGROUND|ACADEMICS?'
    r'|CERTIFICATIONS?|PUBLICATIONS?|DECLARATION|LANGUAGES?'
    r'|KEY\s+STRENGTHS|AREAS\s+OF\s+EXPERTISE|PERSONAL\s+DOSSIER)'
    r'[^\S\r\n]*[:\-\|]?[^\S\r\n]*(?:\n|$)',
    re.IGNORECASE
)

@contextlib.contextmanager
def suppress_stderr():
    with open(os.devnull, "w") as devnull:
        old_stderr = sys.stderr
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stderr = old_stderr

def clean_extracted_text(text: str) -> str:
    text = re.sub(r'\(cid:\d+\)', '•', text)
    text = re.sub(r'[\uE000-\uF8FF]', '•', text)
    text = re.sub(r'[\u2022\u2023\u25E6\u2043\u2219]', '•', text)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'(?<=[a-zA-Z])\^(?=[a-zA-Z])', 'f', text)
    text = re.sub(r'(?:^|\b)\^(?=[a-zA-Z])', 'f', text)
    text = re.sub(r'(?<=[a-z])-\n[^\S\r\n]*(=[a-z])', '', text)
    text = re.sub(r'(?m)^\s*\d{1,3}\s*$', '', text)
    text = re.sub(r'(?m)^\s*[\.\,\;\:\-\_\|\/\\\*\^]+\s*$', '', text)
    
    cleaned_lines = []
    for line in text.split('\n'):
        if re.search(r'\b[A-Za-z]\s+[A-Za-z]\s+[A-Za-z]\s+[A-Za-z]\b', line):
            line = re.sub(r'(?<=[A-Za-z]) (?=[A-Za-z](?: |\b))', '', line)
            line = re.sub(r'\s+', ' ', line)
        cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)

def extract_scanned_pdf_ocr(pdf_path: str) -> Tuple[str, str]:
    """Smart OCR fallback for pure image/scanned PDFs."""
    # 1. Try Windows Native OCR if on Windows
    if platform.system() == "Windows":
        try:
            import asyncio
            import winsdk.windows.storage.streams as streams
            import winsdk.windows.graphics.imaging as imaging
            import winsdk.windows.media.ocr as ocr
            import winsdk.windows.globalization as glob

            lang = glob.Language("en-US")
            engine = ocr.OcrEngine.try_create_from_language(lang) or ocr.OcrEngine.try_create_from_user_profile_languages()
            doc = pymupdf.open(pdf_path)
            pages = []
            async def _run_win_ocr():
                for page in doc:
                    pix = page.get_pixmap(dpi=150)
                    writer = streams.DataWriter()
                    writer.write_bytes(pix.tobytes("png"))
                    buf = writer.detach_buffer()
                    mem = streams.InMemoryRandomAccessStream()
                    await mem.write_async(buf)
                    mem.seek(0)
                    dec = await imaging.BitmapDecoder.create_async(mem)
                    sb = await dec.get_software_bitmap_async()
                    res = await engine.recognize_async(sb)
                    pages.append(res.text)
            asyncio.run(_run_win_ocr())
            text = clean_extracted_text("\n\n".join(pages))
            if len(text.strip()) > 50:
                return text, "WINDOWS_NATIVE_OCR"
        except Exception:
            pass

    # 2. Try Tesseract OCR (cross-platform)
    try:
        import pytesseract
        from PIL import Image
        import io
        tess_exe = r"C:\Users\Cog\Desktop\tesseract-bin\tesseract.exe"
        if os.path.exists(tess_exe):
            pytesseract.pytesseract.tesseract_cmd = tess_exe
            os.environ["TESSDATA_PREFIX"] = r"C:\Users\Cog\Desktop\tesseract-bin\tessdata"
        doc = pymupdf.open(pdf_path)
        pages = []
        for page in doc:
            pix = page.get_pixmap(dpi=250)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            txt = pytesseract.image_to_string(img, lang="eng")
            pages.append(txt)
        text = clean_extracted_text("\n\n".join(pages))
        if len(text.strip()) > 50:
            return text, "TESSERACT_OCR"
    except Exception:
        pass

    return "", "NONE"

def extract_pdf_with_smart_fallback(pdf_path: str) -> Tuple[str, str]:
    extractor_used = "pdfplumber"
    with suppress_stderr():
        try:
            with pdfplumber.open(pdf_path) as pdf:
                plumber_text = "\n".join([page.extract_text() or "" for page in pdf.pages])
        except Exception:
            plumber_text = ""
            
    total_len = len(plumber_text)
    space_count = plumber_text.count(' ')
    space_ratio = space_count / max(1, total_len)
    
    final_text = plumber_text
    if space_ratio < 0.08 or total_len < 100:
        try:
            doc = pymupdf.open(pdf_path)
            mupdf_text = "\n".join([page.get_text() for page in doc])
            m_space_ratio = mupdf_text.count(' ') / max(1, len(mupdf_text))
            if m_space_ratio > space_ratio and len(mupdf_text) >= 100:
                final_text = mupdf_text
                extractor_used = "pymupdf"
        except Exception:
            pass
            
    # If still empty or less than 100 characters, trigger OCR Fallback!
    if len(final_text.strip()) < 100:
        ocr_text, ocr_engine = extract_scanned_pdf_ocr(pdf_path)
        if ocr_text:
            final_text = ocr_text
            extractor_used = f"OCR_FALLBACK_{ocr_engine}"
        else:
            extractor_used = "UNREADABLE_SCANNED_PDF"
            
    return clean_extracted_text(final_text), extractor_used

def extract_docx_file(docx_path: str) -> Tuple[str, str]:
    try:
        doc = docx.Document(docx_path)
        chunks = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    chunks.append(" | ".join(cells))
        return clean_extracted_text("\n\n".join(chunks)), "python-docx"
    except Exception as e:
        return f"[DOCX_READ_ERROR: {str(e)}]", "python-docx-error"

def slice_work_experience_coarse(cleaned_text: str) -> Tuple[str, str, str, int, int]:
    start_match = WORK_EXP_HEADERS.search(cleaned_text)
    header_used = ""
    if start_match:
        header_used = start_match.group().strip()
    else:
        start_match = INLINE_WORK_EXP_HEADERS.search(cleaned_text)
        if start_match:
            header_used = start_match.group().strip()
            
    if not start_match:
        return cleaned_text, "FALLBACK_FULL_TEXT", "NONE", 0, len(cleaned_text)
        
    start_pos = start_match.end()
    end_match = COARSE_WORK_EXP_TERMINATORS.search(cleaned_text, pos=start_pos)
    terminator_used = end_match.group().strip() if end_match else "EOF"
    end_pos = end_match.start() if end_match else len(cleaned_text)
    
    sliced_text = cleaned_text[start_pos:end_pos].strip()
    return sliced_text, header_used, terminator_used, start_pos, end_pos

# 3. Enhanced Packed Batch Prompt for gpt-5.6-luna
SYSTEM_PROMPT = """You are an expert AI resume parsing engine.
You are given a batch of resumes with their pre-sliced Work Experience sections and full text.
Extract structured JSON for ALL candidates in the batch.

RULES FOR EACH CANDIDATE:
1. 'email': Candidate's email address (trimmed, no trailing spaces).
2. 'skillsMentioned': Comprehensive array of all programming languages, databases, frameworks, developer tools, and cloud services found across the ENTIRE resume.
   - ZERO-INFERENCE RULE: You must ONLY extract technologies that appear EXPLICITLY and LITERALLY in the source text. NEVER infer related tools. For example, if the resume says 'CI/CD', do NOT add 'Jenkins' unless the word 'Jenkins' is literally written in the document. If the resume says 'C++', do NOT add 'CMake' unless 'CMake' is written. If the resume says 'Web Services', do NOT add 'SOAP' unless 'SOAP' is written.
   - Do NOT include vague English buzzwords (e.g. avoid 'Deployment Processes', 'Security', 'Scalability', 'Full Stack Developer', 'Team Management', 'Application Architecture').
   - 'skillsMentioned' MUST be a superset containing every technical skill found anywhere in the resume.
3. 'workExperience': Array of company entries.
   - 'company': Company name.
   - 'startDate': Start date (e.g. 'Apr 2022' or '2021').
   - 'endDate': End date. Standardize any variants like 'till date', 'till now', 'to date', 'current' to 'Present'.
   - 'skills': Array of raw technical skills EXPLICITLY mentioned in the bullets or responsibilities of THAT job (including languages, frameworks, databases, tools, APIs, and technical platforms/protocols like MDM, MAM, Kafka, REST).
   - CLIENT & NESTED PROJECTS RULE: If client/internal projects are listed under an employer/company (e.g. 'Projects: • MapHook (Java, JSP)...' under 'Quganitia Systems'), map those skills directly to that employer!
   - PERSONAL PROJECTS RULE: If a project is explicitly personal or self-built without an employer/company, do NOT create a company entry for it in workExperience.
   - MERGE RULE: If multiple roles/promotions are at the SAME company, combine them into ONE entry for that company with the earliest start and latest end date.
   - FILTER RULE: If a job mentions NO technical skills at all in its bullets, OMIT that company entry completely.

OUTPUT JSON FORMAT:
{
  "candidates": [
    {
      "documentId": "exact_document_id_provided",
      "email": "candidate@example.com",
      "skillsMentioned": ["...", "..."],
      "workExperience": [
        {
          "company": "...",
          "startDate": "...",
          "endDate": "...",
          "skills": ["...", "..."]
        }
      ]
    }
  ]
}"""

def apply_verbatim_grounding_guard(candidate: Dict[str, Any], full_text: str, we_text: str) -> Tuple[Dict[str, Any], List[str]]:
    candidate["email"] = candidate.get("email", "").strip()
    full_lower = full_text.lower()
    we_lower = we_text.lower() if we_text else full_lower
    dropped_audit = []

    def is_grounded(skill_name: str, target_text_lower: str) -> bool:
        s_clean = skill_name.strip()
        if not s_clean:
            return False
        s_lower = s_clean.lower()
        if s_lower in target_text_lower:
            return True
        esc = re.escape(s_clean)
        pattern = rf"(?<![A-Za-z0-9]){esc}(?![A-Za-z0-9])"
        return bool(re.search(pattern, target_text_lower, re.IGNORECASE))

    # Guard overall skills
    verified_overall = []
    for s in candidate.get("skillsMentioned", []):
        if is_grounded(s, full_lower):
            verified_overall.append(s.strip())
        else:
            dropped_audit.append(f"skillsMentioned dropped: '{s}' (Not found in full text)")
    candidate["skillsMentioned"] = verified_overall

    # Guard workExperience
    valid_exps = []
    for exp in candidate.get("workExperience", []):
        company = exp.get("company", "").strip()
        comp_skills = []
        for s in exp.get("skills", []):
            if is_grounded(s, we_lower):
                comp_skills.append(s.strip())
            else:
                dropped_audit.append(f"{company} skill dropped: '{s}' (Not found in WE text)")
        exp["skills"] = comp_skills
        if comp_skills:
            valid_exps.append(exp)
        else:
            dropped_audit.append(f"Company omitted: '{company}' (0 verified skills)")

    candidate["workExperience"] = valid_exps
    return candidate, dropped_audit

def call_luna_batch(batch_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    prompt_sections = []
    for idx, item in enumerate(batch_items, 1):
        prompt_sections.append(
            f"=== CANDIDATE #{idx} | documentId: {item['documentId']} ===\n"
            f"[EMAIL HINT]: {item['emailHint']}\n\n"
            f"[WORK EXPERIENCE SECTION (Source for workExperience)]:\n\"\"\"\n{item['weText']}\n\"\"\"\n\n"
            f"[FULL RESUME TEXT (Source for skillsMentioned superset)]:\n\"\"\"\n{item['fullText'][:3500]}\n\"\"\"\n"
        )
        
    user_prompt = "\n----------------------------------------\n".join(prompt_sections)
    user_prompt += "\n\nReturn strict JSON with the top-level 'candidates' array matching all candidates."

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        raw_out = response.choices[0].message.content or "{}"
        parsed = json.loads(raw_out)
        return parsed.get("candidates", [])
    except Exception as e:
        print(f"    [Batch LLM Error]: {e}")
        return []

def get_file_hash(path: str) -> str:
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        hasher.update(f.read(8192))
    return hasher.hexdigest()

def discover_all_resumes() -> List[Dict[str, str]]:
    discovered = []
    seen_hashes = set()
    seen_names = set()

    for folder in [RESUMES1_DIR, RESUMES2_DIR]:
        if not os.path.exists(folder):
            continue
        for root_dir, _, files in os.walk(folder):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in [".pdf", ".docx"]:
                    full_path = os.path.join(root_dir, file)
                    f_hash = get_file_hash(full_path)
                    if f_hash in seen_hashes or file in seen_names:
                        continue
                    seen_hashes.add(f_hash)
                    seen_names.add(file)
                    discovered.append({
                        "documentId": file,
                        "path": full_path,
                        "ext": ext
                    })
    return sorted(discovered, key=lambda x: x["documentId"])

def run_large_scale_batch(batch_size: int = 10):
    print("=" * 80)
    print("RESUME PROCESSOR (Coarse Slicing + OCR Fallback + Stage Trace Logging)")
    print(f"Model: {model_name} | Batch Size: {batch_size} resumes/call")
    print(f"Target Output Folder: {OUTPUT_DIR}")
    print(f"Stage Traces Folder : {TRACES_DIR}")
    print("=" * 80)

    overall_start_time = time.time()
    all_resumes = discover_all_resumes()
    total_unique = len(all_resumes)
    print(f"Discovered {total_unique} unique resumes across resumes1 and resumes2.")

    # Check for existing checkpoint
    processed_ids = set()
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        processed_ids.add(record.get("documentId"))
                    except Exception:
                        pass
                        
    pending_resumes = [r for r in all_resumes if r["documentId"] not in processed_ids]
    print(f"Already processed: {len(processed_ids)} | Pending resumes: {len(pending_resumes)}")

    # Process in batches
    num_batches = (len(pending_resumes) + batch_size - 1) // batch_size
    for b_idx in range(num_batches):
        batch_slice = pending_resumes[b_idx * batch_size : (b_idx + 1) * batch_size]
        print(f"\n--- [Batch {b_idx + 1:02d}/{num_batches:02d}] Pre-processing {len(batch_slice)} files ---")

        batch_items = []
        stage_metadata = {}

        for item in batch_slice:
            doc_id = item["documentId"]
            f_path = item["path"]
            ext = item["ext"]
            
            # STAGE 1: INGESTION (with Smart OCR Fallback)
            t_s1 = time.time()
            if ext == ".pdf":
                raw_text, extractor = extract_pdf_with_smart_fallback(f_path)
            elif ext == ".docx":
                raw_text, extractor = extract_docx_file(f_path)
            else:
                raw_text, extractor = "", "unsupported"
            dt_s1 = round(time.time() - t_s1, 2)
            
            # STAGE 2: SLICING (Coarse Boundary)
            we_text, hdr_used, term_used, s_pos, e_pos = slice_work_experience_coarse(raw_text)
            
            email_match = EMAIL_REGEX.search(raw_text)
            email_hint = email_match.group(0) if email_match else ""
            
            batch_items.append({
                "documentId": doc_id,
                "emailHint": email_hint,
                "weText": we_text,
                "fullText": raw_text
            })
            
            stage_metadata[doc_id] = {
                "stage1_ingestion": {
                    "extractor": extractor,
                    "rawCharCount": len(raw_text),
                    "durationSeconds": dt_s1
                },
                "stage2_slicing": {
                    "startHeader": hdr_used,
                    "terminator": term_used,
                    "sliceRange": [s_pos, e_pos],
                    "weCharCount": len(we_text)
                },
                "stage3_prompt": {
                    "emailHintPassed": email_hint,
                    "weCharsPassed": len(we_text)
                }
            }

        # STAGE 4: LLM BATCH CALL
        b_start = time.time()
        print(f"    Calling {model_name} with {len(batch_items)} packed candidates...")
        results = call_luna_batch(batch_items)
        elapsed = time.time() - b_start
        print(f"    Received {len(results)} parsed candidates in {elapsed:.1f}s")

        results_by_id = {c.get("documentId"): c for c in results if c.get("documentId")}

        # STAGE 5: VERBATIM GUARD & TRACE PERSISTENCE
        with open(CHECKPOINT_FILE, "a", encoding="utf-8") as f_chk:
            for item in batch_items:
                doc_id = item["documentId"]
                res = results_by_id.get(doc_id)
                meta = stage_metadata.get(doc_id, {})
                
                if not res:
                    res = {
                        "documentId": doc_id,
                        "email": item["emailHint"],
                        "skillsMentioned": [],
                        "workExperience": [],
                        "status": "partial_batch_miss"
                    }
                    dropped = ["Batch response omitted this candidate"]
                else:
                    res, dropped = apply_verbatim_grounding_guard(res, item["fullText"], item["weText"])
                    
                meta["stage4_llm_raw"] = {
                    "rawCompanies": [e.get("company") for e in res.get("workExperience", [])]
                }
                meta["stage5_guard_filter"] = {
                    "droppedCount": len(dropped),
                    "droppedAudit": dropped,
                    "finalCompaniesCount": len(res.get("workExperience", []))
                }
                
                # Write individual trace file for complete transparency
                safe_trace_name = re.sub(r'[^\w\-\.]', '_', doc_id) + "_trace.json"
                trace_file_path = os.path.join(TRACES_DIR, safe_trace_name)
                with open(trace_file_path, "w", encoding="utf-8") as f_tr:
                    json.dump({
                        "documentId": doc_id,
                        "stages": meta,
                        "finalCandidate": res
                    }, f_tr, indent=2, ensure_ascii=False)

                f_chk.write(json.dumps(res, ensure_ascii=False) + "\n")
                
        time.sleep(0.5)

    # 4. Final Aggregation & Compilation
    print("\n" + "=" * 80)
    print("All batches completed! Compiling final exports...")
    all_final_records = []
    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                all_final_records.append(json.loads(line))

    total = len(all_final_records)
    no_we_skills = []
    has_we_skills = []
    all_listed_counts = []
    all_we_counts = []

    for c in all_final_records:
        doc_id = c.get("documentId", "")
        email = c.get("email", "")
        exps = c.get("workExperience", [])
        listed = len(c.get("skillsMentioned", []))
        
        we_skills = set()
        for e in exps:
            for s in e.get("skills", []):
                we_skills.add(s)
                
        all_listed_counts.append(listed)
        all_we_counts.append(len(we_skills))
        
        if len(we_skills) == 0:
            no_we_skills.append({
                "documentId": doc_id,
                "email": email,
                "overallSkillsCount": listed,
                "workExperienceEntriesCount": len(exps)
            })
        else:
            has_we_skills.append({
                "documentId": doc_id,
                "email": email,
                "jobSkillsCount": len(we_skills),
                "overallSkillsCount": listed
            })

    avg_listed = round(sum(all_listed_counts) / max(1, total), 1)
    avg_we = round(sum(all_we_counts) / max(1, total), 1)
    grounding_pct = round((sum(all_we_counts) / max(1, sum(all_listed_counts))) * 100, 1)

    audit_summary = {
        "totalUniqueCandidatesProcessed": total,
        "candidatesWithSkillsInWorkExperience": {
            "count": len(has_we_skills),
            "percentage": round(len(has_we_skills) / max(1, total) * 100, 1)
        },
        "candidatesWithZeroSkillsInWorkExperience": {
            "count": len(no_we_skills),
            "percentage": round(len(no_we_skills) / max(1, total) * 100, 1),
            "candidatesList": no_we_skills
        },
        "skillMetrics": {
            "averageSkillsListedPerResume": avg_listed,
            "averageSkillsVerifiedInWorkExperience": avg_we,
            "overallSkillGroundingRatioPercentage": grounding_pct,
            "unsubstantiatedKeywordStuffingPercentage": round(100 - grounding_pct, 1)
        }
    }

    structured_json = {
        "auditSummary": audit_summary,
        "candidates": all_final_records
    }
    with open(FINAL_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(structured_json, f, indent=2, ensure_ascii=False)

    with open(SUMMARY_CSV_FILE, "w", newline="", encoding="utf-8") as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(["documentId", "email", "totalOverallSkills", "companiesCount", "workCompanies", "workSkillsSummary"])
        for r in all_final_records:
            comps = [e.get("company", "") for e in r.get("workExperience", [])]
            we_skills = set()
            for e in r.get("workExperience", []):
                for s in e.get("skills", []):
                    we_skills.add(s)
            writer.writerow([
                r.get("documentId", ""),
                r.get("email", ""),
                len(r.get("skillsMentioned", [])),
                len(comps),
                " | ".join(comps),
                "; ".join(sorted(list(we_skills))[:15])
            ])

    total_time = time.time() - overall_start_time
    print(f"Done! {len(all_final_records)} candidates processed in {total_time:.1f}s.")
    print(f" -> Master JSON: {FINAL_JSON_FILE}")
    print(f" -> Summary CSV: {SUMMARY_CSV_FILE}")
    print(f" -> Traces Dir : {TRACES_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    run_large_scale_batch(batch_size=10)
