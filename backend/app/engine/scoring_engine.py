from typing import Dict, List, Any, Optional
from ..models.schemas import (
    Role, Project, SkillClaim, SkillSummary,
    SelectionInsights, VacancyMatch
)
from .knowledge_graph import KnowledgeGraphEngine

def compute_selection_insights(
    roles: List[Role],
    claims: List[SkillClaim],
    summaries: Dict[str, SkillSummary],
    as_of_year: int = 2026
) -> SelectionInsights:
    """Computes tenure stability, skill recency, leadership signals, and flags."""
    # Compute average tenure
    tenures: List[int] = []
    red_flags: List[str] = []
    
    for r in roles:
        if r.start and r.end:
            try:
                sy, sm = int(r.start[:4]), int(r.start[5:7]) if len(r.start) >= 7 else 1
                ey, em = int(r.end[:4]), int(r.end[5:7]) if len(r.end) >= 7 else 12
                dur = (ey - sy) * 12 + (em - sm) + 1
                if dur > 0:
                    tenures.append(dur)
            except Exception:
                pass

    avg_tenure = round(sum(tenures) / len(tenures), 1) if tenures else 0.0
    has_job_hopping = bool(tenures and avg_tenure < 14 and len(tenures) >= 3)
    if has_job_hopping:
        red_flags.append(f"Frequent short stints: average company tenure is only {avg_tenure} months.")

    # Stability score out of 10
    if not tenures:
        stability = 5.0
    else:
        # 36+ months avg tenure gets 10, 12 months gets 4
        stability = min(10.0, max(1.0, round((avg_tenure / 36.0) * 10, 1)))

    # Skill recency in months from 2026-10
    recency: Dict[str, Optional[int]] = {}
    for skill_name, summary in summaries.items():
        if summary.lastUsed:
            try:
                ly = int(summary.lastUsed[:4])
                lm = int(summary.lastUsed[5:7]) if len(summary.lastUsed) >= 7 else 1
                months_ago = (2026 - ly) * 12 + (10 - lm)
                recency[skill_name] = max(0, months_ago)
            except Exception:
                recency[skill_name] = None
        else:
            recency[skill_name] = None

    # Leadership signals
    leadership_keywords = [
        "lead", "led", "architect", "mentor", "mentored", "designed",
        "spearheaded", "principal", "head of", "scaled system to"
    ]
    signals: List[str] = []
    for r in roles:
        for resp in r.responsibilities:
            for kw in leadership_keywords:
                if kw in resp.lower() and resp not in signals:
                    signals.append(resp[:120])
                    break
                    
    for c in claims:
        if c.personalTask:
            for kw in leadership_keywords:
                if kw in c.personalTask.lower() and c.personalTask not in signals:
                    signals.append(c.personalTask[:120])
                    break

    velocity = "steady"
    if len(signals) >= 3 or any("lead" in r.title.lower() for r in roles):
        velocity = "fast"

    return SelectionInsights(
        stabilityScore=stability,
        averageTenureMonths=avg_tenure,
        hasJobHoppingRisk=has_job_hopping,
        skillRecencyMonths=recency,
        careerVelocity=velocity,
        leadershipSignals=signals[:4],
        redFlags=red_flags
    )


def match_candidate_to_vacancy(
    summaries: Dict[str, SkillSummary],
    claims: List[SkillClaim],
    vacancy_info: Dict[str, Any],
    kg_engine: KnowledgeGraphEngine
) -> VacancyMatch:
    """
    Evaluates candidate strictly against Vacancy details.txt:
    1. Direct match: Exact skills and supported dated experience.
    2. Transferable match: Knowledge graph proxies (e.g. C -> C++, Stripe -> Razorpay).
    """
    candidate_skills = {k.lower(): s for k, s in summaries.items()}
    required_core = vacancy_info.get("requiredCoreSkills", ["Java", "Spring Boot", "Microservices", "REST API", "SQL"])
    required_domain = vacancy_info.get("requiredDomainSkills", ["Payment Gateway", "Razorpay", "Stripe", "Checkout"])
    required_infra = vacancy_info.get("requiredInfraSkills", ["Docker", "Kubernetes", "CI/CD"])

    # Dynamic primary core competency experience check (Universal for any vacancy: Java, IT Support, DevOps, etc.)
    primary_skill = vacancy_info.get("primaryCoreSkill") or (required_core[0] if required_core else "Core Skill")
    core_summary = candidate_skills.get(primary_skill.lower())
    core_years = core_summary.supportedYears if core_summary and core_summary.supportedYears else 0.0
    
    # If primary skill has only claimed months (claimed_only)
    if core_years == 0.0 and core_summary and core_summary.durationStatus == "claimed_only":
        for c in claims:
            if c.skill.lower() == primary_skill.lower() and c.claimedDurationMonths:
                core_years = round(c.claimedDurationMonths / 12.0, 1)
                break

    min_required_exp = vacancy_info.get("experienceMinYears", 5.0)
    # Allow standard 3-month (0.25-0.3 yr) ATS rounding tolerance for senior roles
    meets_core = (core_years >= min_required_exp or (min_required_exp - core_years) <= 0.3)

    matched_direct: List[str] = []
    missing_critical: List[str] = []
    matched_proxies: List[Dict[str, Any]] = []

    # Check Core Skills
    for skill in required_core:
        sk_lower = skill.lower()
        if sk_lower in candidate_skills and candidate_skills[sk_lower].durationStatus in ("dated", "partial", "claimed_only"):
            matched_direct.append(skill)
        elif sk_lower in candidate_skills:
            # Listed only
            matched_direct.append(f"{skill} (listed)")
        else:
            # Check Knowledge Graph
            proxy = kg_engine.find_proxy_match(skill, list(summaries.keys()))
            if proxy:
                matched_proxies.append(proxy)
            else:
                missing_critical.append(skill)

    # Check Domain Skills (Payments / Checkout)
    has_domain = False
    for skill in required_domain:
        if skill.lower() in candidate_skills:
            matched_direct.append(skill)
            has_domain = True
            break
        else:
            proxy = kg_engine.find_proxy_match(skill, list(summaries.keys()))
            if proxy:
                matched_proxies.append(proxy)
                has_domain = True
                break

    if not has_domain:
        missing_critical.append("Payment Gateway / Checkout Experience")

    # Check Infra
    for skill in required_infra:
        if skill.lower() in candidate_skills:
            matched_direct.append(skill)

    # Calculate Direct Match Score (0 - 100)
    # Weighting: 40% Core Experience, 30% Core stack, 20% Domain, 10% Infra
    exp_score = min(1.0, core_years / min_required_exp) * 40.0
    core_score = (len([s for s in matched_direct if not s.endswith("(listed)")]) / max(1, len(required_core))) * 30.0
    domain_score = 20.0 if has_domain else 0.0
    infra_score = 10.0 if any(s.lower() in candidate_skills for s in ["docker", "kubernetes", "ci/cd"]) else 0.0

    direct_score = round(exp_score + core_score + domain_score + infra_score, 1)

    # Calculate Transferable Match Score (adds value for acceptable proxies)
    proxy_bonus = 0.0
    for p in matched_proxies:
        proxy_bonus += (p["weight"] * 10.0)

    transferable_score = min(100.0, round(direct_score + proxy_bonus, 1))

    # Determine Verdict
    notes: List[str] = []
    if direct_score >= 75 and meets_core:
        verdict = "Strong Fit"
        notes.append(f"Candidate meets the {min_required_exp}+ years {primary_skill} requirement with strong stack coverage.")
    elif transferable_score >= 70:
        verdict = "Transferable Fit"
        notes.append("Candidate has strong adjacent skills that transfer well via the Knowledge Graph.")
    elif core_years > 0 and core_years < min_required_exp:
        verdict = "Junior/Mid Fit"
        notes.append(f"Candidate has {core_years} supported {primary_skill} years (role requires {min_required_exp}+ years).")
    else:
        verdict = "Low Fit"
        notes.append(f"Missing core {primary_skill} prerequisites.")

    return VacancyMatch(
        directMatchScore=direct_score,
        transferableScore=transferable_score,
        supportedJavaYears=core_years,
        meetsJavaExperience=meets_core,
        matchedDirectSkills=matched_direct,
        matchedProxySkills=matched_proxies,
        missingCriticalSkills=missing_critical,
        verdict=verdict,
        summaryNotes=notes
    )
