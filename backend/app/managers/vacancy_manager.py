import os
import glob
import json
import shutil
import uuid
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ASSESTS_DIR = os.path.join(PROJECT_ROOT, "assests")
DEFAULT_VACANCY_FILE = os.path.join(PROJECT_ROOT, "Vacancy details.txt")
GLOBAL_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "outputs")

DEFAULT_JAVA_VACANCY_ID = "vacancyId=6ac37cb2765ff358c60b6d7a-SeniorSoftwareEngineerJavaBackend"

class VacancyManager:
    def __init__(self):
        os.makedirs(ASSESTS_DIR, exist_ok=True)
        self.active_vacancy_id = DEFAULT_JAVA_VACANCY_ID
        self._ensure_default_vacancy()

    def _ensure_default_vacancy(self):
        """Ensures the original Java Backend vacancy has its isolated files and outputs intact."""
        default_dir = os.path.join(ASSESTS_DIR, DEFAULT_JAVA_VACANCY_ID)
        os.makedirs(default_dir, exist_ok=True)
        
        # Ensure outputs folder exists
        out_dir = os.path.join(default_dir, "outputs")
        os.makedirs(out_dir, exist_ok=True)

        # Copy existing results.jsonl and skills.csv if in global outputs
        global_jsonl = os.path.join(GLOBAL_OUTPUT_DIR, "results.jsonl")
        global_csv = os.path.join(GLOBAL_OUTPUT_DIR, "skills.csv")
        local_jsonl = os.path.join(out_dir, "results.jsonl")
        local_csv = os.path.join(out_dir, "skills.csv")

        if os.path.exists(global_jsonl) and not os.path.exists(local_jsonl):
            shutil.copy2(global_jsonl, local_jsonl)
        if os.path.exists(global_csv) and not os.path.exists(local_csv):
            shutil.copy2(global_csv, local_csv)

        # Ensure vacancy.json exists
        vac_json_path = os.path.join(default_dir, "vacancy.json")
        if not os.path.exists(vac_json_path):
            from ..parsers.vacancy_parser import parse_vacancy_file
            if os.path.exists(DEFAULT_VACANCY_FILE):
                vac_info = parse_vacancy_file(DEFAULT_VACANCY_FILE)
            else:
                vac_info = {
                    "id": DEFAULT_JAVA_VACANCY_ID,
                    "title": "Senior Software Engineer - Java Backend",
                    "experienceMinYears": 5,
                    "experienceMaxYears": 10,
                    "location": "Hybrid / Remote",
                    "requiredCoreSkills": ["Java", "Spring Boot", "Microservices", "REST API", "SQL"],
                    "requiredDomainSkills": ["Payment Gateway", "Stripe", "Razorpay"],
                    "requiredInfraSkills": ["Docker", "Kubernetes", "Kafka", "AWS"],
                    "preferredSkills": ["CI/CD", "Redis", "Elasticsearch"]
                }
            with open(vac_json_path, "w", encoding="utf-8") as f:
                json.dump(vac_info, f, indent=2)

    def list_vacancies(self) -> List[Dict[str, Any]]:
        """Scans assests directory and lists all isolated vacancy workspaces with resume & parsed counts."""
        vacancies = []
        if not os.path.exists(ASSESTS_DIR):
            return vacancies

        for item in sorted(os.listdir(ASSESTS_DIR)):
            item_path = os.path.join(ASSESTS_DIR, item)
            if os.path.isdir(item_path) and item.startswith("vacancyId="):
                vac_json_path = os.path.join(item_path, "vacancy.json")
                out_dir = os.path.join(item_path, "outputs")
                results_jsonl = os.path.join(out_dir, "results.jsonl")

                # Count resumes (.pdf and .docx)
                resume_files = glob.glob(os.path.join(item_path, "*.pdf")) + glob.glob(os.path.join(item_path, "*.docx"))
                resume_count = len(resume_files)

                # Count parsed records
                parsed_count = 0
                if os.path.exists(results_jsonl):
                    try:
                        with open(results_jsonl, "r", encoding="utf-8") as f:
                            parsed_count = sum(1 for line in f if line.strip())
                    except Exception:
                        parsed_count = 0

                # Load metadata
                vac_info = {}
                if os.path.exists(vac_json_path):
                    try:
                        with open(vac_json_path, "r", encoding="utf-8") as f:
                            vac_info = json.load(f)
                    except Exception:
                        pass

                title = vac_info.get("title") or item.split("-", 1)[-1] if "-" in item else item
                vacancies.append({
                    "id": item,
                    "title": title,
                    "experienceMinYears": vac_info.get("experienceMinYears", 3),
                    "experienceMaxYears": vac_info.get("experienceMaxYears", 8),
                    "location": vac_info.get("location", "Hybrid / Remote"),
                    "requiredCoreSkills": vac_info.get("requiredCoreSkills", []),
                    "requiredDomainSkills": vac_info.get("requiredDomainSkills", []),
                    "requiredInfraSkills": vac_info.get("requiredInfraSkills", []),
                    "preferredSkills": vac_info.get("preferredSkills", []),
                    "resumeCount": resume_count,
                    "parsedCount": parsed_count,
                    "isActive": (item == self.active_vacancy_id),
                    "createdAt": vac_info.get("createdAt", "2026-10-21")
                })

        return vacancies

    def get_active_vacancy_dir(self) -> str:
        d = os.path.join(ASSESTS_DIR, self.active_vacancy_id)
        os.makedirs(d, exist_ok=True)
        return d

    def get_active_output_dir(self) -> str:
        d = os.path.join(self.get_active_vacancy_dir(), "outputs")
        os.makedirs(d, exist_ok=True)
        return d

    def get_active_vacancy_info(self) -> Dict[str, Any]:
        vac_json_path = os.path.join(self.get_active_vacancy_dir(), "vacancy.json")
        if os.path.exists(vac_json_path):
            try:
                with open(vac_json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "id": self.active_vacancy_id,
            "title": "Senior Software Engineer - Java Backend",
            "experienceMinYears": 5,
            "experienceMaxYears": 10,
            "location": "Hybrid / Remote",
            "requiredCoreSkills": ["Java", "Spring Boot", "Microservices", "REST API", "SQL"],
            "requiredDomainSkills": ["Payment Gateway", "Stripe", "Razorpay"],
            "requiredInfraSkills": ["Docker", "Kubernetes", "Kafka", "AWS"],
            "preferredSkills": ["CI/CD", "Redis", "Elasticsearch"]
        }

    def switch_active_vacancy(self, vacancy_id: str) -> Dict[str, Any]:
        """Switches active vacancy without altering any existing file."""
        target_dir = os.path.join(ASSESTS_DIR, vacancy_id)
        if not os.path.exists(target_dir):
            raise FileNotFoundError(f"Vacancy workspace '{vacancy_id}' does not exist.")
        self.active_vacancy_id = vacancy_id
        return self.get_active_vacancy_info()

    def create_vacancy(
        self,
        title: str,
        min_exp: int = 3,
        max_exp: int = 8,
        location: str = "Hybrid / Remote",
        core_skills: List[str] = None,
        domain_skills: List[str] = None,
        infra_skills: List[str] = None,
        preferred_skills: List[str] = None,
        jd_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a brand new isolated vacancy workspace with its own dedicated folder.
        The previous vacancy remains 100% untouched and preserved.
        """
        # Generate safe slug
        clean_slug = re.sub(r'[^a-zA-Z0-9]', '', title) or "CustomVacancy"
        short_id = uuid.uuid4().hex[:12]
        new_vacancy_id = f"vacancyId={short_id}-{clean_slug}"

        new_dir = os.path.join(ASSESTS_DIR, new_vacancy_id)
        os.makedirs(new_dir, exist_ok=True)
        os.makedirs(os.path.join(new_dir, "outputs"), exist_ok=True)

        vac_data = {
            "id": new_vacancy_id,
            "title": title,
            "experienceMinYears": min_exp,
            "experienceMaxYears": max_exp,
            "location": location,
            "requiredCoreSkills": core_skills or [],
            "requiredDomainSkills": domain_skills or [],
            "requiredInfraSkills": infra_skills or [],
            "preferredSkills": preferred_skills or [],
            "createdAt": datetime.now().isoformat()
        }

        # Save vacancy.json
        vac_json_path = os.path.join(new_dir, "vacancy.json")
        with open(vac_json_path, "w", encoding="utf-8") as f:
            json.dump(vac_data, f, indent=2)

        # Save raw JD text if provided
        if jd_text:
            with open(os.path.join(new_dir, "job_description.txt"), "w", encoding="utf-8") as f:
                f.write(jd_text)

        # Make the newly created vacancy the active one
        self.active_vacancy_id = new_vacancy_id
        return vac_data

    def save_vacancy_info(self, vac_info: Dict[str, Any]):
        """Updates the active vacancy's specification file."""
        vac_json_path = os.path.join(self.get_active_vacancy_dir(), "vacancy.json")
        with open(vac_json_path, "w", encoding="utf-8") as f:
            json.dump(vac_info, f, indent=2)

    def delete_vacancy(self, vacancy_id: str) -> Dict[str, Any]:
        """
        Safely deletes a vacancy workspace folder and all its resumes/outputs.
        The default baseline vacancy is protected from accidental deletion.
        If the active vacancy is deleted, automatically switches back to the default vacancy.
        """
        if vacancy_id == DEFAULT_JAVA_VACANCY_ID:
            raise ValueError("The baseline 'Senior Software Engineer - Java Backend' vacancy cannot be deleted as it contains the benchmark dataset.")

        target_dir = os.path.join(ASSESTS_DIR, vacancy_id)
        if not os.path.exists(target_dir):
            raise FileNotFoundError(f"Vacancy workspace '{vacancy_id}' does not exist.")

        shutil.rmtree(target_dir)

        # If the deleted vacancy was the currently active one, fall back to default
        if self.active_vacancy_id == vacancy_id:
            self.active_vacancy_id = DEFAULT_JAVA_VACANCY_ID

        return {
            "deletedId": vacancy_id,
            "activeVacancy": self.get_active_vacancy_info(),
            "vacancies": self.list_vacancies()
        }
