"""
SkillSight ETL - Load Module.
Loads cleaned job postings and daily aggregate metrics into the MySQL/Django database
using atomic transactions and upserts for reliable, fault-tolerant persistence.
"""
import os
import sys
import logging
import uuid
from datetime import datetime, timezone, date
from typing import Dict, Any, Tuple
import pandas as pd
from django.db import transaction

# Setup Django environment if not already loaded
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillsight.settings')
    import django
    django.setup()

from dashboard.models import Skill, JobPosting, DailySkillAggregate, PipelineRunLog
from .config import TECH_SKILLS

logger = logging.getLogger(__name__)


def ensure_skills_seeded() -> Dict[str, Skill]:
    """Ensures all configured technical skills exist in the database."""
    skill_map = {}
    for meta in TECH_SKILLS:
        skill, _ = Skill.objects.update_or_create(
            slug=meta["slug"],
            defaults={
                "name": meta["name"],
                "category": meta["category"],
                "color": meta["color"],
            }
        )
        skill_map[meta["slug"]] = skill
    return skill_map


def load_data_to_database(
    jobs_df: pd.DataFrame,
    aggregates_df: pd.DataFrame,
    target_date: date,
    source_name: str = "Arbeitnow API",
    duration_seconds: float = 0.0,
    error_message: str = None
) -> Dict[str, Any]:
    """
    Inserts or updates cleaned job postings and daily aggregates into the database.
    
    Args:
        jobs_df: DataFrame of processed job postings.
        aggregates_df: DataFrame of daily skill aggregates.
        target_date: Date of the pipeline run.
        source_name: Data source description.
        duration_seconds: Run duration in seconds.
        error_message: Optional error message if any step encountered issues.
        
    Returns:
        Dictionary summarizing load results.
    """
    if target_date is not None:
        target_date = pd.to_datetime(target_date).date()
    else:
        target_date = datetime.now(timezone.utc).date()

    logger.info(f"Loading data into database for date {target_date}...")

    # Ensure all skills are present
    skill_map = ensure_skills_seeded()

    jobs_saved = 0
    aggregates_saved = 0
    total_skills_identified = 0

    try:
        with transaction.atomic():
            # 1. Save JobPostings
            for _, row in jobs_df.iterrows():
                raw_posted_date = row.get("posted_date")
                if raw_posted_date is not None and not pd.isna(raw_posted_date):
                    posted_date = pd.to_datetime(raw_posted_date).date()
                else:
                    posted_date = target_date

                job_posting, _ = JobPosting.objects.update_or_create(
                    job_id=row["job_id"],
                    defaults={
                        "title": row["title"],
                        "company_name": row["company_name"],
                        "location": row["location"],
                        "is_remote": row["is_remote"],
                        "job_type": row["job_type"],
                        "url": row["url"],
                        "description_snippet": row["description_snippet"],
                        "posted_date": posted_date,
                    }
                )
                
                # Assign many-to-many skills
                matched_skill_objects = [
                    skill_map[slug] for slug in row["skill_slugs"] if slug in skill_map
                ]
                job_posting.skills.set(matched_skill_objects)
                jobs_saved += 1
                total_skills_identified += len(matched_skill_objects)

            # 2. Save DailySkillAggregates
            for _, row in aggregates_df.iterrows():
                slug = row["skill_slug"]
                if slug in skill_map:
                    skill_obj = skill_map[slug]
                    DailySkillAggregate.objects.update_or_create(
                        date=target_date,
                        skill=skill_obj,
                        defaults={
                            "job_count": int(row["job_count"]),
                            "total_jobs_analyzed": int(row["total_jobs_analyzed"]),
                            "demand_percentage": float(row["demand_percentage"]),
                        }
                    )
                    aggregates_saved += 1

            # 3. Create PipelineRunLog
            status = "WARNING" if error_message else "SUCCESS"
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
            run_id = f"run_{target_date.strftime('%Y%m%d')}_{now_ms}_{uuid.uuid4().hex[:6]}"
            PipelineRunLog.objects.update_or_create(
                run_id=run_id,
                defaults={
                    "status": status,
                    "duration_seconds": round(duration_seconds, 2),
                    "jobs_fetched": len(jobs_df),
                    "jobs_processed": jobs_saved,
                    "skills_identified": total_skills_identified,
                    "source": source_name,
                    "error_message": error_message,
                    "details": {
                        "aggregates_recorded": aggregates_saved,
                        "target_date": str(target_date),
                    },
                }
            )

        logger.info(
            f"Load successful: {jobs_saved} jobs saved, {aggregates_saved} daily aggregates saved."
        )

        return {
            "status": "SUCCESS",
            "jobs_saved": jobs_saved,
            "aggregates_saved": aggregates_saved,
            "total_skills_identified": total_skills_identified,
            "target_date": str(target_date),
        }

    except Exception as e:
        logger.error(f"Failed to load data into database: {e}", exc_info=True)
        # Log failure in PipelineRunLog
        try:
            fail_id = f"fail_{target_date.strftime('%Y%m%d')}_{target_date}"
            PipelineRunLog.objects.create(
                run_id=fail_id,
                status="FAILED",
                duration_seconds=round(duration_seconds, 2),
                jobs_fetched=len(jobs_df),
                jobs_processed=jobs_saved,
                skills_identified=0,
                source=source_name,
                error_message=str(e),
                details={"error": str(e)}
            )
        except Exception:
            pass
        raise e
