#!/usr/bin/env python3
"""
CLI entrypoint for Resume Data Extraction & Skill Duration Pipeline.
Conforms strictly to Section 6 of the Technical Assessment specification.

Usage:
  python cli.py --input-dir "assests/vacancyId=..." --output-dir "outputs" --as-of-date 2026-10-21 --limit 10
"""

import os
import sys
import argparse
import json

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.llm.batch_worker import BatchProcessingPipeline
from backend.app.managers.vacancy_manager import VacancyManager, DEFAULT_JAVA_VACANCY_ID

def main():
    parser = argparse.ArgumentParser(
        description="Resume Data Extraction & Deterministic Skill Duration Pipeline (AI Assessment)"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=None,
        help="Path to folder containing PDF/DOCX resumes (defaults to active vacancy directory)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Path to output folder for results.jsonl and skills.csv"
    )
    parser.add_argument(
        "--as-of-date",
        type=str,
        default="2026-10-21",
        help="As-of date for capping ongoing/present intervals (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum resumes to process (default: 10 fixed resumes for cost/safety control, 0 for all)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Batch size for packed economic LLM calls (default: 5)"
    )

    args = parser.parse_args()

    vm = VacancyManager()
    input_dir = args.input_dir or vm.get_active_vacancy_dir()
    output_dir = args.output_dir or vm.get_active_output_dir()
    vacancy_info = vm.get_active_vacancy_info()

    print("=" * 70)
    print("RESUME DATA EXTRACTION & FACTUAL INTERVAL AUDITOR")
    print("=" * 70)
    print(f"Input Directory:  {input_dir}")
    print(f"Output Directory: {output_dir}")
    print(f"As-of Date:       {args.as_of_date}")
    print(f"Processing Limit: {args.limit if args.limit > 0 else 'All files'}")
    print(f"Active Vacancy:   {vacancy_info.get('title')}")
    print("-" * 70)

    pipeline = BatchProcessingPipeline(
        resumes_dir=input_dir,
        output_dir=output_dir,
        vacancy_info=vacancy_info
    )

    available_files = pipeline.get_available_resume_files()
    print(f"Discovered {len(available_files)} resume file(s) in input folder.")

    if not available_files:
        print("[!] No PDF or DOCX files found. Exiting.")
        sys.exit(0)

    print(f"Starting pipeline execution (Batch Size: {args.batch_size})...")
    results = pipeline.process_resumes(
        limit=args.limit,
        batch_size=args.batch_size,
        as_of_date=args.as_of_date
    )

    print(f"[✓] Successfully processed {len(results)} resume(s).")
    print(f"[✓] Exported: {os.path.join(output_dir, 'results.jsonl')}")
    print(f"[✓] Exported: {os.path.join(output_dir, 'skills.csv')}")

    # Generate validation report metrics per Section 6
    total = len(results)
    if total > 0:
        success_count = sum(1 for r in results if r.parseStatus == "success")
        partial_count = sum(1 for r in results if r.parseStatus == "partial")
        failed_count = sum(1 for r in results if r.parseStatus == "failed")
        with_projects = sum(1 for r in results if len(r.projects) > 0)
        with_dated = sum(1 for r in results if any(s.durationStatus == "dated" for s in r.skillSummary))
        meets_java = sum(1 for r in results if r.vacancyMatch and r.vacancyMatch.meetsJavaExperience)

        report = {
            "totalResumesEvaluated": total,
            "successCount": success_count,
            "partialCount": partial_count,
            "failedCount": failed_count,
            "successRatePercent": round((success_count / total) * 100, 1),
            "percentWithProjects": round((with_projects / total) * 100, 1),
            "percentWithDatedSkillUse": round((with_dated / total) * 100, 1),
            "percentMeetingJava5Years": round((meets_java / total) * 100, 1),
            "asOfDate": args.as_of_date,
            "vacancyTitle": vacancy_info.get("title")
        }

        report_path = os.path.join(output_dir, "validation_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print("\n" + "=" * 70)
        print("SHORT VALIDATION REPORT (Section 6 Deliverable)")
        print("=" * 70)
        print(f"Total Evaluated:              {total}")
        print(f"Parse Status:                 Success: {success_count} | Partial: {partial_count} | Failed: {failed_count}")
        print(f"Success Rate:                 {report['successRatePercent']}%")
        print(f"With Employer/Projects:       {report['percentWithProjects']}%")
        print(f"With Dated Skill Evidence:    {report['percentWithDatedSkillUse']}%")
        print(f"Meeting Java 5+ Year Target:  {report['percentMeetingJava5Years']}%")
        print(f"[✓] Report saved to: {report_path}")
        print("=" * 70)

if __name__ == "__main__":
    main()
