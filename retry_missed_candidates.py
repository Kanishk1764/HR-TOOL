import os
import json
import time
from main_processor import (
    call_luna_batch, apply_verbatim_grounding_guard, FINAL_JSON_FILE, CHECKPOINT_FILE,
    TRACES_DIR, SUMMARY_CSV_FILE
)

with open(FINAL_JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# Find candidates that were missed in batch responses
missed = [c for c in data["candidates"] if c.get("status") == "partial_batch_miss"]
print(f"Total partial batch miss candidates to recover: {len(missed)}")

if not missed:
    print("No missed candidates!")
    exit(0)

# Load their traces to get the exact pre-sliced text
batch_items = []
for m in missed:
    doc_id = m["documentId"]
    safe_name = [f for f in os.listdir(TRACES_DIR) if doc_id in f][0]
    with open(os.path.join(TRACES_DIR, safe_name), "r", encoding="utf-8") as f_tr:
        tr = json.load(f_tr)
    
    # We will recover their text from their original file
    batch_items.append({
        "documentId": doc_id,
        "emailHint": m.get("email", ""),
        "weText": tr["stages"]["stage2_slicing"]["weCharCount"], # we need text
        "tracePath": os.path.join(TRACES_DIR, safe_name)
    })

# Let's get the actual text from the file paths
from main_processor import discover_all_resumes, extract_pdf_with_smart_fallback, slice_work_experience_coarse
all_res = {r["documentId"]: r["path"] for r in discover_all_resumes()}

call_items = []
for m in missed:
    doc_id = m["documentId"]
    p = all_res[doc_id]
    txt, ext_used = extract_pdf_with_smart_fallback(p)
    we_txt, hdr, term, s, e = slice_work_experience_coarse(txt)
    call_items.append({
        "documentId": doc_id,
        "emailHint": m.get("email", ""),
        "weText": we_txt,
        "fullText": txt,
        "extUsed": ext_used,
        "hdr": hdr,
        "term": term,
        "s": s,
        "e": e
    })

print(f"Calling gpt-5.6-luna for {len(call_items)} candidates...")
results = call_luna_batch(call_items)
res_by_id = {c["documentId"]: c for c in results if c.get("documentId")}

recovered = []
for item in call_items:
    doc_id = item["documentId"]
    res = res_by_id.get(doc_id)
    if res:
        res, dropped = apply_verbatim_grounding_guard(res, item["fullText"], item["weText"])
        res.pop("status", None)
        recovered.append(res)
        
        # Update trace file
        safe_name = [f for f in os.listdir(TRACES_DIR) if doc_id in f][0]
        tr_path = os.path.join(TRACES_DIR, safe_name)
        with open(tr_path, "w", encoding="utf-8") as f_tr:
            json.dump({
                "documentId": doc_id,
                "stages": {
                    "stage1_ingestion": {"extractor": item["extUsed"], "rawCharCount": len(item["fullText"])},
                    "stage2_slicing": {"startHeader": item["hdr"], "terminator": item["term"], "weCharCount": len(item["weText"])},
                    "stage3_prompt": {"emailHintPassed": item["emailHint"]},
                    "stage4_llm_raw": {"rawCompanies": [e.get("company") for e in res.get("workExperience", [])]},
                    "stage5_guard_filter": {"droppedCount": len(dropped), "droppedAudit": dropped, "finalCompaniesCount": len(res.get("workExperience", []))}
                },
                "finalCandidate": res
            }, f_tr, indent=2, ensure_ascii=False)
        print(f"Successfully recovered: {doc_id} -> {len(res.get('workExperience', []))} companies, {len(res.get('skillsMentioned', []))} skills")

# Update checkpoint and final JSON
all_cands_map = {c["documentId"]: c for c in data["candidates"]}
for r in recovered:
    all_cands_map[r["documentId"]] = r

all_updated = list(all_cands_map.values())

# Recompute auditSummary
total = len(all_updated)
no_we = []
has_we = []
all_l = []
all_w = []
for c in all_updated:
    doc_id = c.get("documentId", "")
    email = c.get("email", "")
    exps = c.get("workExperience", [])
    l = len(c.get("skillsMentioned", []))
    w_set = set(s for e in exps for s in e.get("skills", []))
    all_l.append(l)
    all_w.append(len(w_set))
    if len(w_set) == 0:
        no_we.append({"documentId": doc_id, "email": email, "overallSkillsCount": l, "workExperienceEntriesCount": len(exps)})
    else:
        has_we.append({"documentId": doc_id, "email": email, "jobSkillsCount": len(w_set), "overallSkillsCount": l})

avg_l = round(sum(all_l)/max(1, total), 1)
avg_w = round(sum(all_w)/max(1, total), 1)
ratio = round(sum(all_w)/max(1, sum(all_l)) * 100, 1)

new_audit = {
    "totalUniqueCandidatesProcessed": total,
    "candidatesWithSkillsInWorkExperience": {
        "count": len(has_we),
        "percentage": round(len(has_we) / max(1, total) * 100, 1)
    },
    "candidatesWithZeroSkillsInWorkExperience": {
        "count": len(no_we),
        "percentage": round(len(no_we) / max(1, total) * 100, 1),
        "candidatesList": no_we
    },
    "skillMetrics": {
        "averageSkillsListedPerResume": avg_l,
        "averageSkillsVerifiedInWorkExperience": avg_w,
        "overallSkillGroundingRatioPercentage": ratio,
        "unsubstantiatedKeywordStuffingPercentage": round(100 - ratio, 1)
    }
}

with open(FINAL_JSON_FILE, "w", encoding="utf-8") as f:
    json.dump({"auditSummary": new_audit, "candidates": all_updated}, f, indent=2, ensure_ascii=False)

with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
    for c in all_updated:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")

print("\nAudit Summary Updated:")
print(json.dumps(new_audit, indent=2))
