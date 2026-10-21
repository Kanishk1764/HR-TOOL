export interface Role {
  id: string;
  company: string;
  title: string;
  start?: string | null;
  end?: string | null;
  isCurrent: boolean;
  responsibilities: string[];
}

export interface Project {
  id: string;
  roleId?: string | null;
  name: string;
  context: "employment" | "freelance" | "personal" | "academic" | "unknown";
  start?: string | null;
  end?: string | null;
  personalContribution?: string | null;
}

export interface SkillClaim {
  skill: string;
  rawSkill: string;
  evidenceType: "personal_use" | "listed_only" | "team_stack_only" | "company_or_product_only" | "explicit_non_use";
  roleId?: string | null;
  projectId?: string | null;
  personalTask?: string | null;
  start?: string | null;
  end?: string | null;
  isOngoing?: boolean | null;
  claimedDurationMonths?: number | null;
  durationQualifier?: string | null;
  statedLevel?: string | null;
  supportingText: string;
  isQuoteVerified: boolean;
}

export interface SkillSummary {
  skill: string;
  supportedMonths?: number | null;
  supportedYears?: number | null;
  lastUsed?: string | null;
  durationStatus: "dated" | "partial" | "claimed_only" | "unknown" | "conflicting" | "confirmed_zero";
  contexts: string[];
  statedLevels: string[];
  claimCount: number;
  intervals: string[];
}

export interface SelectionInsights {
  stabilityScore: number;
  averageTenureMonths: number;
  hasJobHoppingRisk: boolean;
  skillRecencyMonths: Record<string, number | null>;
  careerVelocity: string;
  leadershipSignals: string[];
  employmentGapsMonths: number[];
  redFlags: string[];
}

export interface ProxySkillMatch {
  targetSkill: string;
  candidateSkill: string;
  weight: number;
  sharedConcepts: string[];
  missingDelta: string[];
  rampUpEstimateWeeks: string;
}

export interface VacancyMatch {
  directMatchScore: number;
  transferableScore: number;
  supportedJavaYears: number;
  meetsJavaExperience: boolean;
  matchedDirectSkills: string[];
  matchedProxySkills: ProxySkillMatch[];
  missingCriticalSkills: string[];
  verdict: string;
  summaryNotes: string[];
}

export interface Candidate {
  documentId: string;
  candidateName?: string | null;
  parseStatus: "success" | "partial" | "failed";
  roles: Role[];
  projects: Project[];
  skillClaims: SkillClaim[];
  skillSummary: SkillSummary[];
  reviewFlags: string[];
  selectionInsights?: SelectionInsights | null;
  vacancyMatch?: VacancyMatch | null;
  rawTextLength: number;
}

export interface VacancyInfo {
  title: string;
  experienceMinYears: number;
  experienceMaxYears: number;
  location: string;
  requiredCoreSkills: string[];
  requiredDomainSkills: string[];
  requiredInfraSkills: string[];
  preferredSkills: string[];
}

export interface VacancySummary {
  id: string;
  title: string;
  experienceMinYears: number;
  experienceMaxYears: number;
  location: string;
  requiredCoreSkills: string[];
  requiredDomainSkills: string[];
  requiredInfraSkills: string[];
  preferredSkills: string[];
  resumeCount: number;
  parsedCount: number;
  isActive: boolean;
  createdAt?: string;
}

export interface SkillProxyRule {
  targetSkill: string;
  proxySkill: string;
  transferabilityWeight: number;
  sharedConcepts: string[];
  missingDelta: string[];
  rampUpEstimateWeeks: string;
  isEnabled: boolean;
}


