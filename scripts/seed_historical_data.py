#!/usr/bin/env python
"""
SkillSight Historical Data Generator & Seeder.
Generates realistic 30-90 day historical time series for SkillSight skills
to immediately power User Story 1 (Weekly Top 10) & User Story 2 (30-day Trends: Django vs Flask).
"""
import os
import sys
import random
from datetime import datetime, timedelta, timezone

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillsight.settings')
import django
django.setup()

from django.db import transaction
from dashboard.models import Skill, JobPosting, DailySkillAggregate, PipelineRunLog
from etl.config import TECH_SKILLS
from etl.load import ensure_skills_seeded
from etl.extract import SAMPLE_FALLBACK_JOBS


# Baseline market demand percentages and weights for realistic trends
BASE_WEIGHTS = {
    # Languages
    "python": 0.28,
    "javascript": 0.26,
    "typescript": 0.21,
    "java": 0.19,
    "cpp": 0.12,
    "csharp": 0.15,
    "go": 0.14,
    "rust": 0.08,
    "ruby": 0.07,
    "php": 0.09,
    "swift": 0.06,
    "kotlin": 0.07,
    "sql": 0.25,

    # Frameworks
    "react": 0.24,
    "nextjs": 0.14,
    "nodejs": 0.22,
    "vue": 0.11,
    "angular": 0.09,
    "django": 0.13,
    "flask": 0.08,
    "fastapi": 0.10,
    "spring-boot": 0.16,
    "rails": 0.06,
    "dotnet": 0.13,
    "express": 0.12,

    # Databases
    "postgresql": 0.22,
    "mysql": 0.18,
    "mongodb": 0.14,
    "redis": 0.15,
    "elasticsearch": 0.08,

    # Cloud & DevOps
    "aws": 0.31,
    "azure": 0.18,
    "gcp": 0.13,
    "docker": 0.27,
    "kubernetes": 0.21,
    "terraform": 0.14,
    "cicd": 0.20,
    "linux": 0.26,
    "git": 0.32,
}


def seed_data(days: int = 45):
    print(f"Seeding {days} days of historical data for SkillSight...")
    skill_map = ensure_skills_seeded()

    today = datetime.now(timezone.utc).date()
    total_aggregates = 0

    with transaction.atomic():
        # 1. Create sample jobs
        for job_data in SAMPLE_FALLBACK_JOBS:
            job, _ = JobPosting.objects.update_or_create(
                job_id=job_data["slug"],
                defaults={
                    "title": job_data["title"],
                    "company_name": job_data["company_name"],
                    "location": job_data["location"],
                    "is_remote": job_data["remote"],
                    "job_type": job_data["job_types"][0] if job_data.get("job_types") else "Full-time",
                    "url": job_data["url"],
                    "description_snippet": job_data["description"][:300],
                    "posted_date": today,
                }
            )
            # Link matched skills
            job_skills = []
            for tag in job_data.get("tags", []):
                for s in skill_map.values():
                    if s.name.lower() == tag.lower() or s.slug == tag.lower():
                        job_skills.append(s)
            job.skills.set(job_skills)

        # 2. Generate daily aggregates for each date in the window
        for day_offset in reversed(range(days)):
            current_date = today - timedelta(days=day_offset)
            
            # Base jobs on that day (e.g. between 180 and 260 jobs analyzed)
            daily_jobs_analyzed = random.randint(180, 260)

            for slug, skill_obj in skill_map.items():
                base_pct = BASE_WEIGHTS.get(slug, 0.05)
                # Introduce slight time drift / seasonal noise (+/- 2.5%)
                drift = (random.random() - 0.5) * 0.05
                # For Django vs Flask, give Django a slight upward trajectory
                if slug == "django":
                    drift += (days - day_offset) * 0.0005
                elif slug == "flask":
                    drift -= (days - day_offset) * 0.0002

                pct = max(0.01, min(0.95, base_pct + drift))
                job_count = int(round(daily_jobs_analyzed * pct))
                demand_pct = round(pct * 100, 2)

                DailySkillAggregate.objects.update_or_create(
                    date=current_date,
                    skill=skill_obj,
                    defaults={
                        "job_count": job_count,
                        "total_jobs_analyzed": daily_jobs_analyzed,
                        "demand_percentage": demand_pct,
                    }
                )
                total_aggregates += 1

        # 3. Create initial PipelineRunLog
        PipelineRunLog.objects.get_or_create(
            run_id="seed_initial_history",
            defaults={
                "status": "SUCCESS",
                "duration_seconds": 1.42,
                "jobs_fetched": 240,
                "jobs_processed": 240,
                "skills_identified": total_aggregates,
                "source": "Arbeitnow API (Historical Baseline)",
                "error_message": None,
                "details": {"days_seeded": days, "records": total_aggregates}
            }
        )

    print(f"Successfully seeded {total_aggregates} historical records across {len(skill_map)} skills for {days} days.")


if __name__ == "__main__":
    days_to_seed = int(sys.argv[1]) if len(sys.argv) > 1 else 45
    seed_data(days_to_seed)
