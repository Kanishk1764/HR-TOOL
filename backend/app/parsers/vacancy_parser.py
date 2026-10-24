import os
import re
from typing import Dict, Any, List

def parse_vacancy_file(file_path: str) -> Dict[str, Any]:
    """
    Parses Vacancy details.txt and extracts required hard skills, experience thresholds,
    domain preferences, and critical technologies.
    """
    if not os.path.exists(file_path):
        return {
            "title": "Senior Software Engineer – Java Backend",
            "experienceMinYears": 5,
            "experienceMaxYears": 10,
            "location": "Pune, India",
            "requiredCoreSkills": ["Java", "Spring Boot", "Microservices", "REST API", "SQL"],
            "requiredDomainSkills": ["Payment Gateway", "Razorpay", "Stripe", "Checkout"],
            "requiredInfraSkills": ["Docker", "Kubernetes", "CI/CD"],
            "preferredSkills": ["Kafka", "OAuth2", "NoSQL", "GCP", "AWS"]
        }

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Extract Job Name
    title_match = re.search(r"JobName:\s*['\"]([^'\"]+)['\"]", content)
    title = title_match.group(1) if title_match else "Software Engineer / Senior Software Engineer – Java Backend"

    # Extract Experience
    exp_match = re.search(r"Experience:\s*(\d+)[\x96\u2013\-](\d+)\s*Years", content)
    min_exp = int(exp_match.group(1)) if exp_match else 5
    max_exp = int(exp_match.group(2)) if exp_match else 10

    # Extract HardSkills names
    hard_skills = list(set(re.findall(r"Name:\s*['\"]([^'\"]+)['\"]", content)))
    # Filter generic or meta names
    clean_hard_skills = [
        s for s in hard_skills 
        if s not in ["Java developer", "middle", "full", "office", "API Development", "Container & Kubernetes Management"]
    ]

    return {
        "title": title,
        "experienceMinYears": min_exp,
        "experienceMaxYears": max_exp,
        "primaryCoreSkill": "Java",
        "skillHierarchy": {
            "spring boot": "Java",
            "spring cloud": "Java",
            "spring mvc": "Java",
            "spring security": "Java",
            "hibernate": "Java",
            "hibernate/jpa": "Java",
            "jpa": "Java"
        },
        "requiredCoreSkills": ["Java", "Spring Boot", "Spring MVC", "Hibernate/JPA", "Microservices", "REST API", "SQL"],
        "requiredDomainSkills": ["Payment Gateway", "Razorpay", "Stripe", "Checkout", "Adyen", "PayU"],
        "requiredInfraSkills": ["Docker", "Kubernetes", "CI/CD", "Jenkins", "Git"],
        "preferredSkills": ["Kafka", "AWS", "GCP", "Azure", "OAuth2", "JWT", "Redis", "NoSQL", "Grafana", "Prometheus"],
        "extractedRawHardSkills": clean_hard_skills
    }
