import os
import sys
import glob
import json

TRACES_DIR = r"c:\Users\Cog\Desktop\HR TASK\batch_outputs\stage_traces"

def inspect(query: str):
    if not os.path.exists(TRACES_DIR):
        print(f"Traces directory not found at {TRACES_DIR}")
        return
        
    query_lower = query.lower()
    all_files = glob.glob(os.path.join(TRACES_DIR, "*_trace.json"))
    matched = [f for f in all_files if query_lower in os.path.basename(f).lower()]
    
    if not matched:
        print(f"No traces found matching: '{query}'")
        print(f"Total traces available: {len(all_files)}")
        return
        
    for trace_file in matched[:3]:
        with open(trace_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        doc_id = data.get("documentId", os.path.basename(trace_file))
        stages = data.get("stages", {})
        cand = data.get("finalCandidate", {})
        
        print("=" * 75)
        print(f"DIAGNOSTIC TRACE FOR: {doc_id}")
        print("=" * 75)
        print("[STAGE 1: INGESTION]")
        s1 = stages.get("stage1_ingestion", {})
        print(f"  • Extractor Used     : {s1.get('extractor')}")
        print(f"  • Raw Character Count: {s1.get('rawCharCount')}")
        print(f"  • Read Time          : {s1.get('durationSeconds')}s")
        
        print("\n[STAGE 2: COARSE SLICING]")
        s2 = stages.get("stage2_slicing", {})
        print(f"  • Start Header Matched : '{s2.get('startHeader')}'")
        print(f"  • Terminator Matched   : '{s2.get('terminator')}'")
        print(f"  • Sliced WE Char Count : {s2.get('weCharCount')}")
        
        print("\n[STAGE 3: PROMPT FORMULATION]")
        s3 = stages.get("stage3_prompt", {})
        print(f"  • Email Hint Passed    : '{s3.get('emailHintPassed')}'")
        print(f"  • WE Chars Sent to LLM : {s3.get('weCharsPassed')}")
        
        print("\n[STAGE 4: LLM INFERENCE]")
        s4 = stages.get("stage4_llm_raw", {})
        print(f"  • Raw Companies Found  : {s4.get('rawCompanies')}")
        
        print("\n[STAGE 5: VERBATIM GROUNDING GUARD]")
        s5 = stages.get("stage5_guard_filter", {})
        print(f"  • Items Dropped Count  : {s5.get('droppedCount')}")
        print(f"  • Dropped Items Audit  : {s5.get('droppedAudit')}")
        print(f"  • Final Companies Count: {s5.get('finalCompaniesCount')}")
        
        print("\n[FINAL EXTRACTED CANDIDATE DATA]")
        print(f"  • Email            : {cand.get('email')}")
        print(f"  • Total Skills     : {len(cand.get('skillsMentioned', []))}")
        print(f"  • Work Experience  :")
        for exp in cand.get("workExperience", []):
            print(f"     - {exp.get('company')} ({exp.get('startDate')} - {exp.get('endDate')}): {len(exp.get('skills', []))} skills -> {exp.get('skills')[:8]}")
        print("=" * 75)

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else ""
    if not q:
        print("Usage: python inspect_candidate.py <candidate_name_or_document_id>")
    else:
        inspect(q)
