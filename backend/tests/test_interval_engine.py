import pytest
from backend.app.models.schemas import SkillClaim
from backend.app.engine.interval_engine import calculate_skill_intervals

def test_five_year_job_with_18_months_skill():
    """
    Test Case 1: Five-year job; explicit React use for 18 months.
    Expected: 18 supported React months; no career-duration fallback.
    """
    claims = [
        SkillClaim(
            skill="React",
            rawSkill="React.js",
            evidenceType="personal_use",
            roleId="r1",
            start="2023-01",
            end="2024-06",
            supportingText="I built React screens from Jan 2023 to June 2024"
        )
    ]
    summaries = calculate_skill_intervals(claims)
    assert "React" in summaries
    react = summaries["React"]
    assert react.supportedMonths == 18
    assert react.supportedYears == 1.5
    assert react.durationStatus == "dated"
    assert react.lastUsed == "2024-06"

def test_overlapping_intervals_union():
    """
    Test Case 2: React Jan-Dec 2023 (12 mo) and Jul 2023-Jun 2024 (12 mo).
    Expected: 12 + 12 - 6 = 18 months. Repeating either claim changes nothing.
    """
    claims = [
        SkillClaim(
            skill="React",
            rawSkill="React",
            evidenceType="personal_use",
            start="2023-01",
            end="2023-12",
            supportingText="Built React app from Jan to Dec 2023"
        ),
        SkillClaim(
            skill="React",
            rawSkill="React",
            evidenceType="personal_use",
            start="2023-07",
            end="2024-06",
            supportingText="Maintained React frontend from Jul 2023 to Jun 2024"
        ),
        # Duplicate claim
        SkillClaim(
            skill="React",
            rawSkill="React",
            evidenceType="personal_use",
            start="2023-01",
            end="2023-12",
            supportingText="Duplicate statement"
        )
    ]
    summaries = calculate_skill_intervals(claims)
    react = summaries["React"]
    assert react.supportedMonths == 18
    assert react.supportedYears == 1.5
    assert react.durationStatus == "dated"

def test_listed_only_and_stated_level():
    """
    Test Case 3: 'Skills: React' or 'React: advanced'.
    Expected: Duration null. Level null in first; advanced in second.
    """
    claims = [
        SkillClaim(
            skill="React",
            rawSkill="React",
            evidenceType="listed_only",
            statedLevel="advanced",
            supportingText="React: advanced"
        )
    ]
    summaries = calculate_skill_intervals(claims)
    react = summaries["React"]
    assert react.supportedMonths is None
    assert react.supportedYears is None
    assert react.durationStatus == "unknown"
    assert "advanced" in react.statedLevels

def test_claimed_duration_without_dates():
    """
    Test Case 4: '3+ years Python', without dates.
    Expected: Claimed 36 months, qualifier 'at least'; supported months and last use unknown.
    """
    claims = [
        SkillClaim(
            skill="Python",
            rawSkill="Python",
            evidenceType="listed_only",
            claimedDurationMonths=36,
            durationQualifier="at least",
            supportingText="3+ years Python"
        )
    ]
    summaries = calculate_skill_intervals(claims)
    py = summaries["Python"]
    assert py.supportedMonths is None
    assert py.durationStatus == "claimed_only"
    assert py.lastUsed is None

def test_team_stack_separation():
    """
    Test Case 5: Team uses AWS; candidate lists Angular.
    Expected: AWS duration is unknown, evidenceType is team_stack_only, no personal experience manufactured.
    """
    claims = [
        SkillClaim(
            skill="AWS",
            rawSkill="AWS",
            evidenceType="team_stack_only",
            supportingText="The team used AWS Cloud infrastructure"
        )
    ]
    summaries = calculate_skill_intervals(claims)
    aws = summaries["AWS"]
    assert aws.supportedMonths is None
    assert aws.durationStatus == "unknown"

def test_conflicting_reversed_dates():
    """
    Test Case 6: Conflicting dates (start > end).
    Expected: Flagged as conflicting, no fake duration.
    """
    claims = [
        SkillClaim(
            skill="Java",
            rawSkill="Java",
            evidenceType="personal_use",
            start="2024-12",
            end="2022-01",
            supportingText="Invalid reversed timeline"
        )
    ]
    summaries = calculate_skill_intervals(claims)
    java = summaries["Java"]
    assert java.durationStatus == "conflicting"
    assert java.supportedMonths is None
