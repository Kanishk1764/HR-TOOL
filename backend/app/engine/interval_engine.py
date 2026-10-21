import re
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Set, Any
from ..models.schemas import SkillClaim, SkillSummary, DurationStatus

def parse_month_string(date_str: Optional[str]) -> Optional[Tuple[int, int]]:
    """
    Parses a string like '2023-01' or '2023-01-15' into (year, month).
    Returns None if date_str is null, invalid, or year-only.
    """
    if not date_str:
        return None
    date_str = date_str.strip()
    
    # Check YYYY-MM
    m = re.match(r'^(\d{4})-(\d{1,2})', date_str)
    if m:
        year = int(m.group(1))
        month = int(m.group(2))
        if 1 <= month <= 12:
            return (year, month)
            
    # Check MM/YYYY
    m2 = re.match(r'^(\d{1,2})/(\d{4})', date_str)
    if m2:
        month = int(m2.group(1))
        year = int(m2.group(2))
        if 1 <= month <= 12:
            return (year, month)
            
    return None

def month_to_int(year: int, month: int) -> int:
    """Converts (year, month) to absolute month index."""
    return year * 12 + (month - 1)

def int_to_month(m_int: int) -> str:
    """Converts absolute month index to 'YYYY-MM'."""
    year = m_int // 12
    month = (m_int % 12) + 1
    return f"{year:04d}-{month:02d}"

def calculate_skill_intervals(
    claims: List[SkillClaim],
    as_of_date: str = "2026-10-21",
    roles: Optional[List[Any]] = None
) -> Dict[str, SkillSummary]:
    """
    Implements Section 3 & Minimum Test Cases of resumeParsingTask.html:
    1. Only personal_use evidence qualifies for dated experience calculation.
    2. Unions overlapping or duplicate intervals to prevent double-counting.
    3. Handles ongoing use capped at as_of_date.
    4. Distinguishes duration states: dated, partial, claimed_only, unknown, conflicting, confirmed_zero.
    """
    as_of_ym = parse_month_string(as_of_date) or (2026, 10)
    as_of_idx = month_to_int(as_of_ym[0], as_of_ym[1])

    # Map roles by ID if supplied
    role_map = {}
    if roles:
        for r in roles:
            r_id = getattr(r, "id", None) or (r.get("id") if isinstance(r, dict) else None)
            if r_id:
                role_map[r_id] = r

    # Group claims by normalized skill name (case-insensitive key, retain proper casing)
    skill_groups: Dict[str, List[SkillClaim]] = {}
    display_names: Dict[str, str] = {}

    for claim in claims:
        key = claim.skill.strip().lower()
        if key not in skill_groups:
            skill_groups[key] = []
            display_names[key] = claim.skill.strip()
        skill_groups[key].append(claim)

    summaries: Dict[str, SkillSummary] = {}

    for key, group in skill_groups.items():
        canonical_name = display_names[key]
        
        # Check for confirmed zero / explicit non-use
        has_non_use = any(c.evidenceType == "explicit_non_use" for c in group)
        
        personal_claims = [c for c in group if c.evidenceType == "personal_use"]
        claimed_only_claims = [c for c in group if c.claimedDurationMonths is not None]
        listed_claims = [c for c in group if c.evidenceType in ("listed_only", "team_stack_only", "company_or_product_only")]

        contexts: Set[str] = set()
        stated_levels: Set[str] = set()
        for c in group:
            if c.statedLevel:
                stated_levels.add(c.statedLevel)
            if c.projectId:
                contexts.add("project")
            if c.roleId:
                contexts.add("employment")

        # Collect covered distinct month indices
        covered_months: Set[int] = set()
        formatted_intervals: List[str] = []
        has_conflicts = False
        has_unresolved_dates = False
        last_used_idx: Optional[int] = None

        for c in personal_claims:
            start_str = c.start
            end_str = c.end
            is_ongoing = bool(c.isOngoing)

            # Inherit dates from linked role if claim has incomplete dates
            if c.roleId and c.roleId in role_map:
                r_obj = role_map[c.roleId]
                r_start = getattr(r_obj, "start", None) or (r_obj.get("start") if isinstance(r_obj, dict) else None)
                r_end = getattr(r_obj, "end", None) or (r_obj.get("end") if isinstance(r_obj, dict) else None)
                r_curr = getattr(r_obj, "isCurrent", False) or (r_obj.get("isCurrent", False) if isinstance(r_obj, dict) else False)
                if not start_str and r_start:
                    start_str = r_start
                if not end_str and r_end:
                    end_str = r_end
                if not end_str and r_curr:
                    is_ongoing = True

            start_ym = parse_month_string(start_str)
            end_ym = parse_month_string(end_str)

            # Ongoing handling
            if is_ongoing:
                if start_ym:
                    end_ym = as_of_ym
                else:
                    has_unresolved_dates = True
                    continue

            # If both start and end exist
            if start_ym and end_ym:
                start_idx = month_to_int(start_ym[0], start_ym[1])
                end_idx = month_to_int(end_ym[0], end_ym[1])

                if start_idx > end_idx:
                    # Reversed dates - conflict!
                    has_conflicts = True
                    continue

                # Add all discrete months inclusive [start, end]
                for m in range(start_idx, end_idx + 1):
                    covered_months.add(m)

                if last_used_idx is None or end_idx > last_used_idx:
                    last_used_idx = end_idx

                formatted_intervals.append(f"{int_to_month(start_idx)} to {int_to_month(end_idx)}")
            elif start_ym or end_ym or c.start or c.end:
                # Ambiguous or year-only interval
                has_unresolved_dates = True
            else:
                # No dates on this personal use claim
                has_unresolved_dates = True

        total_months = len(covered_months) if covered_months else None
        total_years = round(total_months / 12.0, 2) if total_months is not None else None
        last_used = int_to_month(last_used_idx) if last_used_idx is not None else None

        # Determine durationStatus strictly per Section 3
        if has_non_use and not covered_months:
            duration_status: DurationStatus = "confirmed_zero"
            total_months = 0
            total_years = 0.0
        elif has_conflicts:
            duration_status = "conflicting"
        elif total_months is not None and total_months > 0:
            if has_unresolved_dates:
                duration_status = "partial"
            else:
                duration_status = "dated"
        elif claimed_only_claims:
            duration_status = "claimed_only"
        else:
            duration_status = "unknown"

        summaries[canonical_name] = SkillSummary(
            skill=canonical_name,
            supportedMonths=total_months,
            supportedYears=total_years,
            lastUsed=last_used,
            durationStatus=duration_status,
            contexts=list(contexts),
            statedLevels=list(stated_levels),
            claimCount=len(group),
            intervals=formatted_intervals
        )

    return summaries
