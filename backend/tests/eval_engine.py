import json
from typing import Dict, List, Any, Tuple

TECH_PARENT_MAP = {
    "spring boot": "java",
    "spring cloud": "java",
    "spring mvc": "java",
    "spring security": "java",
    "hibernate": "java",
    "jpa": "java",
    "react": "javascript",
    "fastapi": "python",
    "django": "python",
    "pandas": "python",
}

SYNONYMS = {
    "rest": "rest api",
    "restful apis": "rest api",
    "rest api": "rest api",
    "apache kafka": "kafka",
    "kafka": "kafka",
    "aws s3": "aws",
    "aws api gateway": "aws",
    "amazon web services": "aws",
    "postgres": "postgresql",
    "sql server": "sql",
    "mysql": "sql",
    "oracle": "sql",
}

def normalize_skill(s: str) -> str:
    s_clean = s.strip().lower()
    return SYNONYMS.get(s_clean, s_clean)

class EvaluationEngine:
    """
    Evaluates Candidate Extractions across the 4 Production AI Layers:
    - Layer 1: Temporal & Schema Invariants
    - Layer 2: Verbatim Grounding & Faithfulness
    - Layer 3: Factual Recall & Precision (vs Golden Dataset)
    - Layer 4: Domain & Hierarchy Consistency
    """

    @staticmethod
    def evaluate_layer1_temporal(candidate_json: Dict[str, Any]) -> Dict[str, Any]:
        """Layer 1: Checks chronological logic and project-to-role date bounding."""
        roles = candidate_json.get("roles", [])
        projects = candidate_json.get("projects", [])
        role_map = {r["id"]: r for r in roles}
        
        checks_passed = 0
        total_checks = 0
        violations = []

        # Role start <= end check
        for r in roles:
            total_checks += 1
            if r.get("start") and r.get("end") and r["start"] > r["end"]:
                violations.append(f"Role {r['id']} has start ({r['start']}) > end ({r['end']})")
            else:
                checks_passed += 1

        # Project date checks
        for p in projects:
            total_checks += 1
            parent = role_map.get(p.get("roleId"))
            if parent and not p.get("start") and not p.get("end"):
                violations.append(f"Project {p.get('id')} has null start/end despite parent role {parent['id']}")
            else:
                checks_passed += 1

        score = round((checks_passed / total_checks * 100), 1) if total_checks else 100.0
        return {"layer1_score": score, "violations": violations}

    @staticmethod
    def evaluate_layer2_grounding(candidate_json: Dict[str, Any]) -> Dict[str, Any]:
        """Layer 2: Checks verbatim quote verification for all extracted claims."""
        claims = candidate_json.get("skillClaims", [])
        if not claims:
            return {"layer2_score": 0.0, "verified_count": 0, "total_claims": 0}

        verified = sum(1 for c in claims if c.get("isQuoteVerified", False))
        score = round((verified / len(claims)) * 100, 1)
        return {"layer2_score": score, "verified_count": verified, "total_claims": len(claims)}

    @staticmethod
    def evaluate_layer3_recall_precision(candidate_json: Dict[str, Any], golden_record: Dict[str, Any]) -> Dict[str, Any]:
        """Layer 3: Measures Recall, Precision, and F1 against Golden Truth."""
        extracted_skills = {normalize_skill(c.get("skill", "")) for c in candidate_json.get("skillClaims", [])}
        golden_skills = {normalize_skill(s) for s in golden_record.get("groundTruthSkills", [])}

        true_positives = len(extracted_skills & golden_skills)
        recall = round((true_positives / len(golden_skills)) * 100, 1) if golden_skills else 100.0
        precision = round((true_positives / len(extracted_skills)) * 100, 1) if extracted_skills else 100.0
        f1 = round(2 * (precision * recall) / (precision + recall), 1) if (precision + recall) > 0 else 0.0

        missed_skills = list(golden_skills - extracted_skills)
        return {
            "layer3_recall": recall,
            "layer3_precision": precision,
            "layer3_f1": f1,
            "true_positives": true_positives,
            "missed_skills": missed_skills
        }

    @staticmethod
    def evaluate_layer4_domain_consistency(candidate_json: Dict[str, Any], skill_hierarchy: Dict[str, str] = None) -> Dict[str, Any]:
        """Layer 4: Checks if implied competencies (from vacancy skillHierarchy) are attributed to each active role interval."""
        hierarchy = {k.lower(): v.lower() for k, v in (skill_hierarchy or TECH_PARENT_MAP).items()}
        claims = candidate_json.get("skillClaims", [])
        claims_by_role: Dict[str, set] = {}
        for c in claims:
            rid = c.get("roleId")
            if rid:
                claims_by_role.setdefault(rid, set()).add(c.get("skill", "").lower())

        violations = []
        checks_passed = 0
        total_checks = 0

        for rid, role_skills in claims_by_role.items():
            for sk in role_skills:
                parent = hierarchy.get(sk)
                if parent:
                    total_checks += 1
                    if parent in role_skills or any(parent in s for s in role_skills):
                        checks_passed += 1
                    else:
                        violations.append(f"Role {rid} used '{sk}' but parent competency '{parent}' was missing")

        score = round((checks_passed / total_checks * 100), 1) if total_checks else 100.0
        return {"layer4_score": score, "violations": violations}

    @classmethod
    def evaluate_candidate(cls, candidate_json: Dict[str, Any], golden_record: Dict[str, Any], vacancy_info: Dict[str, Any] = None) -> Dict[str, Any]:
        hierarchy = vacancy_info.get("skillHierarchy") if vacancy_info else None
        l1 = cls.evaluate_layer1_temporal(candidate_json)
        l2 = cls.evaluate_layer2_grounding(candidate_json)
        l3 = cls.evaluate_layer3_recall_precision(candidate_json, golden_record)
        l4 = cls.evaluate_layer4_domain_consistency(candidate_json, skill_hierarchy=hierarchy)

        # Qualification Accuracy: Did candidate meet 5+ years?
        java_summary = next((s for s in candidate_json.get("skillSummary", []) if s.get("skill") == "Java"), None)
        computed_java_years = java_summary.get("supportedYears", 0.0) if java_summary else 0.0
        meets_exp = candidate_json.get("vacancyMatch", {}).get("meetsJavaExperience", False)
        expected_meets = golden_record.get("expectedMeetsVacancy", True)
        
        decision_correct = (meets_exp == expected_meets)

        overall_eval_score = round((l1["layer1_score"] + l2["layer2_score"] + l3["layer3_f1"] + l4["layer4_score"]) / 4.0, 1)

        return {
            "candidateName": golden_record["candidateName"],
            "overall_eval_score": overall_eval_score,
            "layer1_score": l1["layer1_score"],
            "layer2_score": l2["layer2_score"],
            "layer3_recall": l3["layer3_recall"],
            "layer3_precision": l3["layer3_precision"],
            "layer3_f1": l3["layer3_f1"],
            "layer4_score": l4["layer4_score"],
            "computed_java_years": computed_java_years,
            "decision_correct": decision_correct,
            "l1_violations": l1["violations"],
            "l4_violations": l4["violations"],
            "missed_skills": l3["missed_skills"]
        }
