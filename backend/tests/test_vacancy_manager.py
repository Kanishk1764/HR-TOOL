import os
import shutil
import pytest
from backend.app.managers.vacancy_manager import VacancyManager, DEFAULT_JAVA_VACANCY_ID, ASSESTS_DIR

def test_vacancy_manager_lifecycle():
    vm = VacancyManager()
    
    # 1. Verify default vacancy exists and is discovered
    vacancies = vm.list_vacancies()
    assert len(vacancies) >= 1
    java_vac = next((v for v in vacancies if v["id"] == DEFAULT_JAVA_VACANCY_ID), None)
    assert java_vac is not None
    assert java_vac["resumeCount"] == 50
    assert java_vac["isActive"] is True

    # 2. Create a new isolated vacancy
    new_vac = vm.create_vacancy(
        title="Test DevOps Cloud Engineer",
        min_exp=4,
        max_exp=9,
        location="Remote",
        core_skills=["AWS", "Terraform", "Kubernetes"],
        domain_skills=["FinTech"],
        infra_skills=["Docker", "CI/CD"],
        preferred_skills=["Python", "Prometheus"]
    )

    new_id = new_vac["id"]
    try:
        assert new_id.startswith("vacancyId=")
        assert "TestDevOps" in new_id
        
        # Verify active switched to new vacancy
        assert vm.active_vacancy_id == new_id
        active_info = vm.get_active_vacancy_info()
        assert active_info["title"] == "Test DevOps Cloud Engineer"

        # Verify new isolated directories exist
        new_dir = vm.get_active_vacancy_dir()
        assert os.path.exists(new_dir)
        assert os.path.exists(os.path.join(new_dir, "vacancy.json"))
        assert os.path.exists(os.path.join(new_dir, "outputs"))

        # Verify original vacancy directory and resumes remain 100% intact
        orig_dir = os.path.join(ASSESTS_DIR, DEFAULT_JAVA_VACANCY_ID)
        assert os.path.exists(orig_dir)
        orig_resumes = [f for f in os.listdir(orig_dir) if f.endswith(".pdf") or f.endswith(".docx")]
        assert len(orig_resumes) == 50

        # 3. Switch back to original Java vacancy
        vm.switch_active_vacancy(DEFAULT_JAVA_VACANCY_ID)
        assert vm.active_vacancy_id == DEFAULT_JAVA_VACANCY_ID
        java_info = vm.get_active_vacancy_info()
        assert "Java" in java_info["title"]

    finally:
        # Cleanup temporary test vacancy folder if still present
        test_path = os.path.join(ASSESTS_DIR, new_id)
        if os.path.exists(test_path):
            shutil.rmtree(test_path)

def test_delete_vacancy():
    vm = VacancyManager()

    # Default benchmark vacancy must be protected
    with pytest.raises(ValueError, match="benchmark dataset"):
        vm.delete_vacancy(DEFAULT_JAVA_VACANCY_ID)

    # Create temporary vacancy and delete it
    temp_vac = vm.create_vacancy(title="Temporary Role To Delete")
    temp_id = temp_vac["id"]
    temp_dir = os.path.join(ASSESTS_DIR, temp_id)
    assert os.path.exists(temp_dir)
    assert vm.active_vacancy_id == temp_id

    # Delete it
    del_res = vm.delete_vacancy(temp_id)
    assert del_res["deletedId"] == temp_id
    assert not os.path.exists(temp_dir)
    # Active automatically reverts to default Java vacancy
    assert vm.active_vacancy_id == DEFAULT_JAVA_VACANCY_ID

