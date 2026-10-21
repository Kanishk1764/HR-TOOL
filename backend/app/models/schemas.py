from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

# Evidence types strictly matching resumeParsingTask specification
EvidenceType = Literal[
    "personal_use",
    "listed_only",
    "team_stack_only",
    "company_or_product_only",
    "explicit_non_use"
]

# Duration status strictly matching resumeParsingTask Section 3
DurationStatus = Literal[
    "dated",
    "partial",
    "claimed_only",
    "unknown",
    "conflicting",
    "confirmed_zero"
]

# Project context types
ProjectContext = Literal[
    "employment",
    "freelance",
    "personal",
    "academic",
    "unknown"
]

ParseStatus = Literal["success", "partial", "failed"]


class Role(BaseModel):
    id: str = Field(description="Unique role ID like r1, r2")
    company: Optional[str] = "Independent / Undisclosed"
    title: Optional[str] = "Software Engineer"
    start: Optional[str] = None  # YYYY-MM or YYYY
    end: Optional[str] = None    # YYYY-MM or YYYY or null
    isCurrent: bool = False
    responsibilities: List[str] = Field(default_factory=list)


class Project(BaseModel):
    id: str = Field(description="Unique project ID like p1, p2")
    roleId: Optional[str] = None
    name: Optional[str] = "Project"
    context: ProjectContext = "employment"
    start: Optional[str] = None
    end: Optional[str] = None
    personalContribution: Optional[str] = None


class SkillClaim(BaseModel):
    skill: str = Field(description="Normalized canonical skill name e.g. Java, React")
    rawSkill: Optional[str] = None
    evidenceType: EvidenceType = "listed_only"
    roleId: Optional[str] = None
    projectId: Optional[str] = None
    personalTask: Optional[str] = None
    start: Optional[str] = None  # YYYY-MM
    end: Optional[str] = None    # YYYY-MM
    isOngoing: Optional[bool] = None
    ongoingConfirmedAsOf: Optional[str] = None
    claimedDurationMonths: Optional[int] = None
    durationQualifier: Optional[str] = None  # e.g. "at least", "approximately"
    statedLevel: Optional[str] = None  # "beginner", "intermediate", "advanced" or null
    supportingText: Optional[str] = ""
    isQuoteVerified: bool = False


class SkillSummary(BaseModel):
    skill: str
    supportedMonths: Optional[int] = None
    supportedYears: Optional[float] = None
    lastUsed: Optional[str] = None
    durationStatus: DurationStatus
    contexts: List[str] = Field(default_factory=list)
    statedLevels: List[str] = Field(default_factory=list)
    claimCount: int = 0
    intervals: List[str] = Field(default_factory=list)  # Formatted as ["2022-01 to 2023-06", ...]


class SelectionInsights(BaseModel):
    stabilityScore: float = 0.0  # 0 to 10
    averageTenureMonths: float = 0.0
    hasJobHoppingRisk: bool = False
    skillRecencyMonths: Dict[str, Optional[int]] = Field(default_factory=dict)
    careerVelocity: str = "steady"  # fast, steady, flat
    leadershipSignals: List[str] = Field(default_factory=list)
    employmentGapsMonths: List[int] = Field(default_factory=list)
    redFlags: List[str] = Field(default_factory=list)


class VacancyMatch(BaseModel):
    directMatchScore: float = 0.0      # 0 to 100 based strictly on hard requirements
    transferableScore: float = 0.0     # 0 to 100 with knowledge graph equivalents
    supportedJavaYears: float = 0.0
    meetsJavaExperience: bool = False  # required 5+ years
    matchedDirectSkills: List[str] = Field(default_factory=list)
    matchedProxySkills: List[Dict[str, Any]] = Field(default_factory=list)
    missingCriticalSkills: List[str] = Field(default_factory=list)
    verdict: str = "Under Review"      # Strong Fit, Transferable Fit, Junior Fit, No Fit
    summaryNotes: List[str] = Field(default_factory=list)


class ResumeResult(BaseModel):
    documentId: str
    candidateName: Optional[str] = None
    parseStatus: ParseStatus = "success"
    roles: List[Role] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    skillClaims: List[SkillClaim] = Field(default_factory=list)
    skillSummary: List[SkillSummary] = Field(default_factory=list)
    reviewFlags: List[str] = Field(default_factory=list)
    selectionInsights: Optional[SelectionInsights] = None
    vacancyMatch: Optional[VacancyMatch] = None
    rawTextLength: int = 0
