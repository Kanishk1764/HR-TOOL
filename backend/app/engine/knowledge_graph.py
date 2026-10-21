from typing import Dict, List, Optional, Any
from pydantic import BaseModel

class SkillProxy(BaseModel):
    targetSkill: str              # Skill required by JD (e.g. Spring MVC, Hibernate/JPA, C++, Razorpay)
    proxySkill: str               # Alternative candidate skill (e.g. Spring Boot, SQL, C, Stripe)
    transferabilityWeight: float  # 0.0 to 1.0 (e.g. 0.85)
    sharedConcepts: List[str]     # e.g. ["ORM mapping", "Query optimization"]
    missingDelta: List[str]       # e.g. ["JPA entity lifecycle"]
    rampUpEstimateWeeks: str      # e.g. "1-2 weeks"
    isEnabled: bool = True        # HR toggleable in UI


# Targeted Knowledge Graph Rules addressing exact skills required by the Senior Java Backend Vacancy
DEFAULT_TECH_GRAPH: List[SkillProxy] = [
    # 1. Spring MVC <-> Spring Boot (Very common: developers using Spring Boot have full Spring MVC controller expertise)
    SkillProxy(
        targetSkill="Spring MVC",
        proxySkill="Spring Boot",
        transferabilityWeight=0.95,
        sharedConcepts=["DispatcherServlet", "REST Controllers", "Request Mapping", "Dependency Injection"],
        missingDelta=["XML configuration conventions (rarely needed in modern stacks)"],
        rampUpEstimateWeeks="Immediate (0-1 week)"
    ),

    # 2. Hibernate/JPA <-> SQL / Databases (Candidates with strong SQL easily adopt Hibernate ORM entities)
    SkillProxy(
        targetSkill="Hibernate/JPA",
        proxySkill="SQL",
        transferabilityWeight=0.88,
        sharedConcepts=["Relational table mapping", "Foreign keys", "Indexing", "Query performance tuning"],
        missingDelta=["JPA annotations (@Entity, @ManyToOne)", "Cascade types", "N+1 query resolution"],
        rampUpEstimateWeeks="1-2 weeks"
    ),

    # 3. Systems Programming: C++ <-> C (Low-level performance)
    SkillProxy(
        targetSkill="C++",
        proxySkill="C",
        transferabilityWeight=0.85,
        sharedConcepts=["Pointers & Memory Allocation", "Low-level Systems Programming", "POSIX / Linux APIs", "Performance Tuning"],
        missingDelta=["Object-Oriented Design (Classes/Inheritance)", "Modern C++ (RAII, Smart Pointers)", "STL & Templates"],
        rampUpEstimateWeeks="2-4 weeks"
    ),

    # 4. Systems Programming: C++ <-> C# (Enterprise systems)
    SkillProxy(
        targetSkill="C++",
        proxySkill="C#",
        transferabilityWeight=0.80,
        sharedConcepts=["Object-oriented architecture", "Strong static typing", "Memory profiling"],
        missingDelta=["Manual pointer manipulation (malloc/free vs GC)", "Header compilation"],
        rampUpEstimateWeeks="3-4 weeks"
    ),

    # 5. Payment Gateways: Razorpay <-> Stripe / Generic Payment Gateway
    SkillProxy(
        targetSkill="Razorpay",
        proxySkill="Payment Gateway",
        transferabilityWeight=0.95,
        sharedConcepts=["Webhook verification & idempotency", "Payment intent lifecycles", "Refunds & Settlement APIs"],
        missingDelta=["Razorpay-specific SDK signatures"],
        rampUpEstimateWeeks="Immediate (1 week)"
    ),
    SkillProxy(
        targetSkill="Razorpay",
        proxySkill="Stripe",
        transferabilityWeight=0.95,
        sharedConcepts=["Webhook verification", "Tokenized card processing", "Refunds & Webhooks"],
        missingDelta=["Indian domestic payment rails (UPI, Netbanking)"],
        rampUpEstimateWeeks="1 week"
    ),

    # 6. Messaging: Kafka <-> RabbitMQ / REST Event Queues
    SkillProxy(
        targetSkill="Kafka",
        proxySkill="RabbitMQ",
        transferabilityWeight=0.82,
        sharedConcepts=["Asynchronous message queuing", "Publish/Subscribe paradigm", "Consumer groups"],
        missingDelta=["Distributed commit log architecture", "Partition rebalancing"],
        rampUpEstimateWeeks="2-3 weeks"
    ),

    # 7. Orchestration: Kubernetes <-> Docker
    SkillProxy(
        targetSkill="Kubernetes",
        proxySkill="Docker",
        transferabilityWeight=0.85,
        sharedConcepts=["Containerization", "Port mapping", "Environment configuration", "Microservice packaging"],
        missingDelta=["Pod specifications", "Ingress controllers", "Helm charts"],
        rampUpEstimateWeeks="2 weeks"
    )
]


class KnowledgeGraphEngine:
    def __init__(self, proxies: Optional[List[SkillProxy]] = None):
        self.proxies: List[SkillProxy] = proxies or DEFAULT_TECH_GRAPH

    def get_proxies_for_target(self, target_skill: str) -> List[SkillProxy]:
        target_lower = target_skill.strip().lower()
        return [
            p for p in self.proxies 
            if p.isEnabled and p.targetSkill.lower() == target_lower
        ]

    def find_proxy_match(self, required_skill: str, candidate_skills: List[str]) -> Optional[Dict[str, Any]]:
        candidate_skills_lower = [s.strip().lower() for s in candidate_skills]
        proxies = self.get_proxies_for_target(required_skill)
        
        best_match = None
        for p in proxies:
            if p.proxySkill.lower() in candidate_skills_lower:
                if best_match is None or p.transferabilityWeight > best_match["weight"]:
                    best_match = {
                        "targetSkill": p.targetSkill,
                        "candidateSkill": p.proxySkill,
                        "weight": p.transferabilityWeight,
                        "sharedConcepts": p.sharedConcepts,
                        "missingDelta": p.missingDelta,
                        "rampUpEstimateWeeks": p.rampUpEstimateWeeks
                    }
        return best_match

    def update_proxy_state(self, target_skill: str, proxy_skill: str, enabled: bool):
        for p in self.proxies:
            if p.targetSkill.lower() == target_skill.lower() and p.proxySkill.lower() == proxy_skill.lower():
                p.isEnabled = enabled
